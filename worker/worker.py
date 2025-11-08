from __future__ import annotations
import os
import time
import json
import orjson
from typing import Any, Iterable
import redis
import logging

from shared.config import (
    REDIS_URL,
    META_PAGE_ACCESS_TOKEN,
    META_APP_SECRET,
    BRAND_PERSONA,
    POSTGRES_URL,
    LOG_LEVEL,
)
from shared.logging_config import setup_logging, get_logger, log_message_processed, log_error
from shared.monitoring import track_duration, get_metrics

# Setup logging
setup_logging(service="worker", level=LOG_LEVEL or "INFO", json_format=os.getenv("JSON_LOGS", "false").lower() == "true")
logger = get_logger(__name__)
metrics = get_metrics()
from .meta_client import send_instagram_text, send_mark_seen, send_typing_on
from shared.db import (
    get_conn,
    ensure_user,
    ensure_thread,
    insert_message,
    insert_memory_embedding,
    search_memory,
    insert_analytics,
    update_thread_intent,
    delete_user_data,
)
from shared.rag import embed
from .llm import generate as llm_generate, default_system_prompt

QUEUE_KEY = "insta_jobs"
DEDUP_PROCESSED = "insta_worker_msg_dedup"


def connect_redis(url: str) -> redis.Redis:
    return redis.from_url(url, decode_responses=False)


def extract_messages(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    # Support both FB-style messaging array and IG changes
    entries = payload.get("entry", [])
    for entry in entries:
        # messaging variant (commonly used with IG too)
        for msg in entry.get("messaging", []) or []:
            sender = msg.get("sender", {}).get("id")
            if not sender:
                continue
            text = None
            if msg.get("message"):
                text = msg["message"].get("text")
                mid = msg["message"].get("mid") or msg.get("mid")
                attachments = msg["message"].get("attachments")
            if text:
                yield {
                    "sender_id": sender,
                    "text": text,
                    "mid": mid,
                    "attachments": attachments,
                    "timestamp": msg.get("timestamp"),
                }

        # changes variant
        for change in entry.get("changes", []) or []:
            value = change.get("value", {})
            if value.get("messaging_product") == "instagram":
                messages = value.get("messages", []) or []
                for m in messages:
                    sender = m.get("from") or m.get("from_")
                    sender_id = sender.get("id") if isinstance(sender, dict) else sender
                    username = sender.get("username") if isinstance(sender, dict) else None
                    text = (m.get("text") or {}).get("body") or m.get("message") or m.get("text")
                    mid = m.get("id") or m.get("mid")
                    attachments = m.get("attachments")
                    if sender_id and text:
                        yield {
                            "sender_id": sender_id,
                            "text": text,
                            "mid": mid,
                            "username": username,
                            "attachments": attachments,
                            "timestamp": m.get("timestamp"),
                        }


def generate_reply_basic(text: str) -> str:
    # Simple placeholder logic; replace with LLM+RAG later
    text = (text or "").strip()
    if not text:
        return "Hi! 👋 How can I help you today?"
    lower = text.lower()
    if any(k in lower for k in ["hello", "hi", "hey", "namaste", "नमस्ते"]):
        return "Hey there! 😊 How can I help today?"
    if any(k in lower for k in ["help", "support", "issue", "problem"]):
        return "I’m here to help! Could you share a few details about the issue?"
    # Default echo-ish with persona
    return f"Thanks for reaching out! {BRAND_PERSONA}. You said: ‘{text}’"


def generate_reply_smart(user_id: int, text: str) -> str:
    # Try DB-backed RAG + LLM; fallback to basic
    context_parts = []
    emb = None
    if text:
        try:
            emb = embed(text)
        except Exception as e:
            emb = None
    conn = get_conn() if POSTGRES_URL else None
    if conn and emb is not None:
        try:
            results = search_memory(conn, user_id, emb, limit=5)
            if results:
                context_parts.append("Relevant memory:\n" + "\n".join(f"- {r['content']}" for r in results))
        except Exception as e:
            pass
    context = "\n\n".join(context_parts).strip()
    system_prompt = default_system_prompt()
    out = llm_generate(system_prompt, text or "", context)
    if out and out.strip():
        return out.strip()
    return generate_reply_basic(text)


def classify_intent(text: str) -> tuple[str, float]:
    # Try LLM-based intent detection first
    try:
        sys = (
            "You classify Instagram DM intents. Return ONLY compact JSON with keys 'intent' and 'confidence' (0-1). "
            "Intents: greeting, support, sales, complaint, gratitude, other."
        )
        user = f"Text: {text}\nRespond as JSON."
        out = llm_generate(sys, user, "")
        if out:
            import json as _json
            s = out.strip()
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                s = s[start : end + 1]
            data = _json.loads(s)
            intent = str(data.get("intent", "other")).lower()
            conf = float(data.get("confidence", 0.5))
            if intent not in {"greeting","support","sales","complaint","gratitude","other"}:
                intent = "other"
            return intent, max(0.0, min(1.0, conf))
    except Exception:
        pass

    # Fallback: rule-based
    if not text:
        return ("greeting", 0.5)
    t = text.lower().strip()
    if any(w in t for w in ["hello", "hi", "hey", "namaste", "नमस्ते", "hola"]):
        return ("greeting", 0.9)
    if any(w in t for w in ["help", "support", "assist", "issue", "problem", "error"]):
        return ("support", 0.8)
    if any(w in t for w in ["price", "pricing", "buy", "purchase", "cost", "subscribe"]):
        return ("sales", 0.7)
    if any(w in t for w in ["complaint", "angry", "bad", "refund", "cancel"]):
        return ("complaint", 0.7)
    if any(w in t for w in ["thanks", "thank you", "great", "awesome"]):
        return ("gratitude", 0.7)
    return ("other", 0.4)


def main():
    r = connect_redis(REDIS_URL)
    logger.info("Worker started. Waiting for jobs…")
    metrics.increment("worker.started")
    
    while True:
        try:
            item = r.blpop(QUEUE_KEY, timeout=5)
            if not item:
                continue
            _, data = item
            
            start_time = time.time()
            metrics.increment("worker.jobs.received")
            
            try:
                payload = orjson.loads(data)
            except Exception:
                try:
                    payload = json.loads(data)
                except Exception as e:
                    logger.error(f"Failed to parse job: {e}")
                    metrics.increment("worker.jobs.parse_error")
                    continue

            for msg in extract_messages(payload):
                sender_raw = str(msg["sender_id"])
                sender_id = int(sender_raw) if sender_raw.isdigit() else sender_raw
                text = msg.get("text")
                mid = msg.get("mid")
                atts = msg.get("attachments") or []
                # If no text but attachment present, describe it minimally
                if not text and atts:
                    types = list({(a.get("type") or (a.get("mime_type") if isinstance(a, dict) else None) or "attachment") for a in atts})
                    text = f"[{', '.join(types)} received]"

                # Handle data deletion command before persisting
                normalized = (text or "").strip().lower()
                if normalized in {"delete my data", "delete my info", "delete data", "remove my data"}:
                    logger.info(f"Data deletion requested by user {sender_id}")
                    metrics.increment("worker.data_deletion.requested")
                    
                    # Mark seen and confirm deletion
                    try:
                        send_mark_seen(sender_raw, META_PAGE_ACCESS_TOKEN)
                    except Exception as e:
                        logger.warning(f"Failed to mark seen: {e}")
                    
                    conn = get_conn() if POSTGRES_URL else None
                    if conn and isinstance(sender_id, int):
                        try:
                            delete_user_data(conn, sender_id)
                            logger.info(f"Successfully deleted data for user {sender_id}")
                            metrics.increment("worker.data_deletion.success")
                        except Exception as e:
                            logger.error(f"Deletion error for user {sender_id}: {e}")
                            metrics.increment("worker.data_deletion.error")
                    
                    ok, err = send_instagram_text(str(sender_id), "Your data has been deleted. ✅", META_PAGE_ACCESS_TOKEN)
                    if not ok:
                        logger.error(f"Failed to send deletion confirmation: {err}")
                        metrics.increment("worker.send.error")
                    else:
                        metrics.increment("worker.send.success")
                    # Skip regular processing for this message
                    continue

                # Persist + RAG
                conn = get_conn() if POSTGRES_URL else None
                thread_id = None
                if conn and isinstance(sender_id, int):
                    try:
                        ensure_user(conn, sender_id, ig_username=msg.get("username"))
                        thread_id = ensure_thread(conn, sender_id)
                        insert_message(conn, thread_id, "user", text or "", {"timestamp": msg.get("timestamp")})
                        try:
                            emb = embed(text or "")
                            insert_memory_embedding(conn, sender_id, (text or "")[:500], emb, kind="message")
                        except Exception as e:
                            logger.warning(f"Failed to create embedding: {e}")
                    except Exception as e:
                        logger.error(f"DB error for user {sender_id}: {e}")
                        metrics.increment("worker.db.error")

                # Deduplicate per-message (5 min)
                try:
                    if mid and not r.sadd(DEDUP_PROCESSED, mid):
                        continue
                    if mid:
                        r.expire(DEDUP_PROCESSED, 300)
                except Exception:
                    pass

                # Mark seen before generating to reduce notification spam
                try:
                    send_mark_seen(sender_raw, META_PAGE_ACCESS_TOKEN)
                except Exception as e:
                    logger.warning(f"Failed to mark seen for {sender_id}: {e}")

                # Show typing indicator
                try:
                    send_typing_on(sender_raw, META_PAGE_ACCESS_TOKEN)
                except Exception as e:
                    logger.warning(f"Failed to send typing indicator for {sender_id}: {e}")

                intent, confidence = classify_intent(text or "")
                logger.info(f"Classified intent for user {sender_id}: {intent} (confidence: {confidence:.2f})")
                
                reply = generate_reply_smart(sender_id if isinstance(sender_id, int) else 0, text)
                ok, err = send_instagram_text(str(sender_id), reply, META_PAGE_ACCESS_TOKEN)
                
                duration_ms = (time.time() - start_time) * 1000
                
                if not ok:
                    logger.error(f"Failed to send message to {sender_id}: {err}")
                    metrics.increment("worker.send.error")
                else:
                    logger.info(f"Successfully replied to {sender_id} in {duration_ms:.0f}ms")
                    metrics.increment("worker.send.success")
                    metrics.histogram("worker.message.duration_ms", duration_ms)
                if conn and thread_id:
                    try:
                        insert_message(conn, thread_id, "assistant", reply, {})
                        # Insert analytics and update last intent
                        try:
                            provider = os.getenv("LLM_PROVIDER", "none")
                            model = os.getenv("GROQ_MODEL", os.getenv("OLLAMA_MODEL", "basic"))
                            # naive latency placeholder; could measure precise timings
                            latency_ms = 0
                            insert_analytics(conn, thread_id, latency_ms, f"{provider}:{model}", confidence, {"intent": intent})
                            update_thread_intent(conn, thread_id, intent)
                        except Exception as e:
                            logger.warning(f"Failed to insert analytics: {e}")
                    except Exception as e:
                        logger.error(f"Failed to persist assistant message: {e}")
        except KeyboardInterrupt:
            logger.info("Worker stopping (KeyboardInterrupt)…")
            metrics.increment("worker.stopped")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            metrics.increment("worker.error")
            time.sleep(1)


if __name__ == "__main__":
    main()
