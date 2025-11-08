from __future__ import annotations
import os
import re
from pathlib import Path
import psycopg

from shared.config import POSTGRES_URL
from shared.db import ensure_user, insert_memory_embedding
from shared.rag import embed


DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100):
    words = text.split()
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        yield chunk
        i += chunk_size - overlap


def main():
    dsn = POSTGRES_URL
    if not dsn:
        raise SystemExit("POSTGRES_URL not set")

    files = list(DOCS_DIR.glob("*.md"))
    if not files:
        print(f"No markdown files found in {DOCS_DIR}")
        return

    conn = psycopg.connect(dsn, autocommit=True)
    ensure_user(conn, 0, ig_username="global", language="en")

    for fp in files:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        for chunk in chunk_text(text):
            emb = embed(chunk)
            insert_memory_embedding(conn, 0, chunk[:1000], emb, kind="faq")
        print(f"Ingested {fp.name}")


if __name__ == "__main__":
    main()

