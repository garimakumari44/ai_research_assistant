
from __future__ import annotations

from app.llm.base import BaseLLMProvider
from app.llm.config import settings
from app.llm.models import ProviderType
from app.llm.providers.openrouter_provider import OpenRouterProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Create the application's LLM provider.

    OpenRouter is intentionally the only supported provider.
    """

    if settings.provider != ProviderType.OPENROUTER:
        raise RuntimeError(
            "Only OpenRouter is supported by the application. "
            f"Configured provider: {settings.provider.value!r}"
        )

    return OpenRouterProvider(
        api_key=settings.get_openrouter_api_key(),
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        http_referer=settings.openrouter_http_referer,
        app_name=settings.openrouter_app_name,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
    )

