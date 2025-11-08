from __future__ import annotations
import os
from typing import Any, Iterable, Optional

import psycopg

from .config import POSTGRES_URL


_conn: Optional[psycopg.Connection] = None


def get_conn() -> Optional[psycopg.Connection]:
    global _conn
    dsn = POSTGRES_URL
    if not dsn:
        return None
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(dsn, autocommit=True)
    return _conn


def ensure_user(conn: psycopg.Connection, user_id: int, ig_username: str | None = None, language: str | None = None):
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into users (id, ig_username, language)
            values (%s, %s, %s)
            on conflict (id) do update set
              ig_username = coalesce(excluded.ig_username, users.ig_username),
              language = coalesce(excluded.language, users.language)
            """,
            (user_id, ig_username, language),
        )


def ensure_thread(conn: psycopg.Connection, user_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            select id::text from threads
            where user_id = %s
            order by updated_at desc
            limit 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            """
            insert into threads (user_id)
            values (%s)
            returning id::text
            """,
            (user_id,),
        )
        return cur.fetchone()[0]


def insert_message(conn: psycopg.Connection, thread_id: str, role: str, text: str, meta: dict[str, Any] | None = None):
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into messages (thread_id, role, text, meta)
            values (%s::uuid, %s, %s, %s::jsonb)
            """,
            (thread_id, role, text, psycopg.types.json.Json(meta or {})),
        )


def _vector_literal(vec: Iterable[float]) -> str:
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def insert_memory_embedding(conn: psycopg.Connection, user_id: int, content: str, embedding: list[float], kind: str = "message"):
    vec = _vector_literal(embedding)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into memory_embeddings (user_id, content, embedding, kind)
            values (%s, %s, %s::vector, %s)
            """,
            (user_id, content, vec, kind),
        )


def search_memory(conn: psycopg.Connection, user_id: int, embedding: list[float], limit: int = 5, include_global: bool = True) -> list[dict[str, Any]]:
    vec = _vector_literal(embedding)
    with conn.cursor() as cur:
        if include_global:
            cur.execute(
                f"""
                select content, 1 - (embedding <#> { '%s' }::vector) as score
                from memory_embeddings
                where user_id in (%s, 0)
                order by embedding <-> { '%s' }::vector
                limit %s
                """,
                (vec, user_id, vec, limit),
            )
        else:
            cur.execute(
                f"""
                select content, 1 - (embedding <#> { '%s' }::vector) as score
                from memory_embeddings
                where user_id = %s
                order by embedding <-> { '%s' }::vector
                limit %s
                """,
                (vec, user_id, vec, limit),
            )
        rows = cur.fetchall() or []
        return [{"content": r[0], "score": float(r[1])} for r in rows]


def insert_analytics(conn: psycopg.Connection, thread_id: str, latency_ms: int, model: str, confidence: float, feedback: dict[str, Any] | None = None):
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into analytics (thread_id, latency_ms, model, confidence, feedback)
            values (%s::uuid, %s, %s, %s, %s::jsonb)
            """,
            (thread_id, latency_ms, model, confidence, psycopg.types.json.Json(feedback or {})),
        )


def update_thread_intent(conn: psycopg.Connection, thread_id: str, intent: str | None):
    if not intent:
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            update threads
            set last_intent = %s, updated_at = now()
            where id = %s::uuid
            """,
            (intent, thread_id),
        )


def delete_user_data(conn: psycopg.Connection, user_id: int):
    """Delete all data for a user: analytics, messages, threads, memory, user."""
    with conn.cursor() as cur:
        # Find thread IDs first
        cur.execute("select id::text from threads where user_id = %s", (user_id,))
        thread_ids = [r[0] for r in (cur.fetchall() or [])]
        # Delete analytics for those threads
        if thread_ids:
            cur.execute(
                "delete from analytics where thread_id = any(%s::uuid[])",
                (thread_ids,),
            )
            # Delete messages for those threads
            cur.execute(
                "delete from messages where thread_id = any(%s::uuid[])",
                (thread_ids,),
            )
            # Delete threads
            cur.execute(
                "delete from threads where id = any(%s::uuid[])",
                (thread_ids,),
            )
        # Delete memory embeddings
        cur.execute("delete from memory_embeddings where user_id = %s", (user_id,))
        # Finally delete the user
        cur.execute("delete from users where id = %s", (user_id,))


def update_message_text(conn: psycopg.Connection, message_id: str, new_text: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            update messages
            set text = %s, created_at = created_at -- no change in time
            where id = %s::uuid
            """,
            (new_text, message_id),
        )
