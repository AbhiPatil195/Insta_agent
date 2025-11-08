from __future__ import annotations
import asyncio
from typing import Any
import orjson
from redis.asyncio import from_url as redis_from_url

from shared.config import REDIS_URL

_redis = None
QUEUE_KEY = "insta_jobs"
DEDUP_SET = "insta_msg_dedup"


async def get_redis(url: str | None = None):
    global _redis
    if _redis is None:
        _redis = redis_from_url(url or REDIS_URL, decode_responses=False)
    return _redis


def _extract_ids(event: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for entry in event.get("entry", []) or []:
        # FB/IG messaging style
        for msg in entry.get("messaging", []) or []:
            mid = (msg.get("message") or {}).get("mid") or msg.get("mid")
            if mid:
                ids.append(str(mid))
        # IG changes style
        for change in entry.get("changes", []) or []:
            value = change.get("value", {})
            for m in value.get("messages", []) or []:
                mid = m.get("id") or m.get("mid")
                if mid:
                    ids.append(str(mid))
    return ids


async def enqueue_event(event: dict[str, Any]):
    r = await get_redis()
    data = orjson.dumps(event)
    # Deduplicate by message ids when available (5 minutes TTL)
    ids = _extract_ids(event)
    if ids:
        pipe = r.pipeline()
        push = False
        for mid in ids:
            # set NX returns True if added
            pipe.sadd(DEDUP_SET, mid)
        results = await pipe.execute()
        if any(bool(x) for x in results):
            await r.expire(DEDUP_SET, 300)
            push = True
        if push:
            await r.rpush(QUEUE_KEY, data)
    else:
        # No IDs found; push to be safe
        await r.rpush(QUEUE_KEY, data)
