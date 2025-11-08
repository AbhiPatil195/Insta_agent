import os


def get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.getenv(key, default)
    if required and not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


META_APP_ID = get_env("META_APP_ID")
META_APP_SECRET = get_env("META_APP_SECRET")
META_VERIFY_TOKEN = get_env("META_VERIFY_TOKEN", "dev-verify-token")
META_PAGE_ID = get_env("META_PAGE_ID")
META_IG_BUSINESS_ID = get_env("META_IG_BUSINESS_ID")
META_PAGE_ACCESS_TOKEN = get_env("META_PAGE_ACCESS_TOKEN")
META_GRAPH_VERSION = get_env("META_GRAPH_VERSION", "21.0")

REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/0")
POSTGRES_URL = get_env("POSTGRES_URL")

GROQ_API_KEY = get_env("GROQ_API_KEY")
OLLAMA_HOST = get_env("OLLAMA_HOST")

KG_URI = get_env("KG_URI")
KG_USER = get_env("KG_USER")
KG_PASSWORD = get_env("KG_PASSWORD")

TELEGRAM_BOT_TOKEN = get_env("TELEGRAM_BOT_TOKEN")
HUMAN_CHAT_ID = get_env("HUMAN_CHAT_ID")

BRAND_PERSONA = get_env("BRAND_PERSONA", "Friendly, helpful, concise, emoji-friendly")
LANGS_SUPPORTED = get_env("LANGS_SUPPORTED", "en,hi,mr")
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
