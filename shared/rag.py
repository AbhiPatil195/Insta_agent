from __future__ import annotations
from typing import List

from fastembed import TextEmbedding


_embedder: TextEmbedding | None = None


def get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        # Small, CPU-friendly, 384-dim
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embedder


def embed(text: str) -> List[float]:
    emb = next(get_embedder().embed([text or ""]))
    return list(map(float, emb))

