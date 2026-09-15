
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from app.llm.models import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    StreamingChunk,
)


class BaseLLMProvider(ABC):
    """
    Canonical interface for the application's LLM provider.

    The application currently uses OpenRouter exclusively.

    All higher-level components should depend on this interface rather
    than directly importing a provider SDK.
    """

    def __init__(self, model_name: str) -> None:
        if not model_name or not model_name.strip():
            raise ValueError("model_name must not be empty.")

        self.model_name = model_name.strip()

    # ============================================================
    # PROVIDER INFORMATION
    # ============================================================

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the stable provider identifier."""
        raise NotImplementedError

    # ============================================================
    # SHARED HELPERS
    # ============================================================

    @staticmethod
    def convert_messages(
        messages: list,
    ) -> list[dict[str, str]]:
        """
        Convert internal ChatMessage objects into API-compatible
        message dictionaries.
        """

        return [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in messages
        ]

    async def count_tokens(self, text: str) -> int:
        """
        Conservative token-count estimate.

        Providers may override this with a tokenizer-backed implementation.
        """

        if not text:
            return 0

        return max(1, len(text) // 4)

    # ============================================================
    # GENERATION
    # ============================================================

    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """Generate a complete response."""
        raise NotImplementedError

    # ============================================================
    # STREAMING
    # ============================================================

    @abstractmethod
    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[StreamingChunk, None]:
        """Stream a response."""
        raise NotImplementedError

    # ============================================================
    # HEALTH
    # ============================================================

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider availability."""
        raise NotImplementedError

    # ============================================================
    # MODELS
    # ============================================================

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return available/supported models."""
        raise NotImplementedError

    # ============================================================
    # CONTEXT MANAGER
    # ============================================================

    async def __aenter__(self) -> "BaseLLMProvider":
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:
        close_method = getattr(self, "close", None)

        if close_method is not None:
            result = close_method()

            if hasattr(result, "__await__"):
                await result

