from openai import OpenAI
from functools import lru_cache
from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_openai_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT,
    )