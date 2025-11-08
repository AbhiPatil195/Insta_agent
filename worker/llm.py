from __future__ import annotations
import os
from typing import Optional
import requests

from shared.config import (
    GROQ_API_KEY,
    OLLAMA_HOST,
    BRAND_PERSONA,
    LANGS_SUPPORTED,
    get_env,
)


def call_groq(system: str, user: str, context: str = "", model: Optional[str] = None) -> Optional[str]:
    api_key = GROQ_API_KEY
    if not api_key:
        return None
    model = model or get_env("GROQ_MODEL", "llama-3.1-8b-instant")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": (context + "\n\n" + user).strip()},
    ]
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 350,
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code >= 400:
            return None
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def call_ollama(system: str, user: str, context: str = "", model: Optional[str] = None) -> Optional[str]:
    host = OLLAMA_HOST
    if not host:
        return None
    model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    url = host.rstrip("/") + "/api/chat"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": (context + "\n\n" + user).strip()},
    ]
    try:
        r = requests.post(url, json={"model": model, "messages": messages, "stream": False}, timeout=60)
        if r.status_code >= 400:
            return None
        data = r.json()
        return data.get("message", {}).get("content")
    except Exception:
        return None


def generate(system_prompt: str, user_prompt: str, context: str = "") -> Optional[str]:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        out = call_groq(system_prompt, user_prompt, context)
        if out:
            return out
        # Fallback to ollama if configured
        out = call_ollama(system_prompt, user_prompt, context)
        if out:
            return out
        return None
    if provider == "ollama":
        out = call_ollama(system_prompt, user_prompt, context)
        if out:
            return out
        return call_groq(system_prompt, user_prompt, context)
    return None


def default_system_prompt() -> str:
    return (
        "You are an AI Instagram Assistant designed to automatically chat with users via Instagram DMs. "
        "You are friendly, empathetic, concise, and brand-consistent. "
        f"Persona: {BRAND_PERSONA}. Supported languages: {LANGS_SUPPORTED}. "
        "Adapt tone to sentiment; include emojis when suitable; avoid disclosing internal details."
    )

