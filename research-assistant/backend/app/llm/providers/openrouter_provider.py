
from __future__ import annotations

from typing import Any, AsyncGenerator

from openai import AsyncOpenAI

from app.llm.base import BaseLLMProvider
from app.llm.config import settings
from app.llm.models import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ProviderType,
    StreamingChunk,
    Usage,
)


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter provider using OpenRouter's OpenAI-compatible API.

    OpenRouter is the only LLM provider supported by the application.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        base_url: str | None = None,
        http_referer: str | None = None,
        app_name: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:

        resolved_api_key = (
            api_key
            or settings.get_openrouter_api_key()
        )

        resolved_model = (
            model
            or settings.openrouter_model
        )

        if not resolved_api_key:
            raise ValueError(
                "OpenRouter API key is not configured."
            )

        super().__init__(resolved_model)

        self.api_key = resolved_api_key

        self.base_url = (
            base_url
            or settings.openrouter_base_url
        )

        self.http_referer = (
            http_referer
            or settings.openrouter_http_referer
        )

        self.app_name = (
            app_name
            or settings.openrouter_app_name
        )

        self.timeout = (
            timeout
            if timeout is not None
            else settings.timeout
        )

        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.max_retries
        )

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            default_headers={
                "HTTP-Referer": self.http_referer,
                "X-Title": self.app_name,
            },
        )

    # ============================================================
    # PROVIDER INFORMATION
    # ============================================================

    @property
    def provider_name(self) -> str:
        return ProviderType.OPENROUTER.value

    def get_model(self) -> str:
        return self.model_name

    def get_provider_name(self) -> str:
        return self.provider_name

    # ============================================================
    # REQUEST BUILDING
    # ============================================================

    def _build_request(
        self,
        request: LLMRequest,
        *,
        stream: bool = False,
    ) -> dict[str, Any]:

        config = request.config

        payload: dict[str, Any] = {
            "model": request.model or self.model_name,
            "messages": self.convert_messages(
                request.messages
            ),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "stream": stream,
        }

        if config.stop_sequences:
            payload["stop"] = config.stop_sequences

        # Provider-specific OpenRouter options can be passed
        # through request metadata.
        provider_options = request.metadata.get(
            "provider_options"
        )

        if isinstance(provider_options, dict):
            payload.update(provider_options)

        return payload

    # ============================================================
    # GENERATE
    # ============================================================

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        if not request.messages:
            raise ValueError(
                "OpenRouter request must contain at least one message."
            )

        payload = self._build_request(
            request,
            stream=False,
        )

        response = await self.client.chat.completions.create(
            **payload
        )

        if not response.choices:
            raise RuntimeError(
                "OpenRouter returned no choices."
            )

        message = response.choices[0].message

        content = message.content

        if content is None:
            raise RuntimeError(
                "OpenRouter returned an empty response."
            )

        usage = self._normalize_usage(
            getattr(response, "usage", None)
        )

        response_model = (
            getattr(response, "model", None)
            or request.model
            or self.model_name
        )

        return LLMResponse(
            text=content.strip(),
            provider=ProviderType.OPENROUTER,
            model=response_model,
            usage=usage,
            metadata={
                "request_id": getattr(
                    response,
                    "id",
                    None,
                ),
                "finish_reason": getattr(
                    response.choices[0],
                    "finish_reason",
                    None,
                ),
            },
        )

    # ============================================================
    # STREAM
    # ============================================================

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[StreamingChunk, None]:

        if not request.messages:
            raise ValueError(
                "OpenRouter request must contain at least one message."
            )

        payload = self._build_request(
            request,
            stream=True,
        )

        response = await self.client.chat.completions.create(
            **payload
        )

        async for chunk in response:

            if not chunk.choices:
                continue

            choice = chunk.choices[0]

            delta = choice.delta

            text = getattr(
                delta,
                "content",
                None,
            )

            finish_reason = getattr(
                choice,
                "finish_reason",
                None,
            )

            if text:
                yield StreamingChunk(
                    text=text,
                    finished=False,
                )

            if finish_reason is not None:
                yield StreamingChunk(
                    text="",
                    finished=True,
                    metadata={
                        "finish_reason": finish_reason,
                    },
                )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    async def health_check(self) -> bool:

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "Reply with OK.",
                    }
                ],
                temperature=0.0,
                max_tokens=5,
                stream=False,
            )

            return bool(response.choices)

        except Exception:
            return False

    # ============================================================
    # MODEL LIST
    # ============================================================

    async def list_models(self) -> list[ModelInfo]:

        try:
            response = await self.client.models.list()

            models: list[ModelInfo] = []

            for model in response.data:

                model_id = getattr(
                    model,
                    "id",
                    None,
                )

                if not model_id:
                    continue

                context_window = getattr(
                    model,
                    "context_length",
                    0,
                ) or 0

                models.append(
                    ModelInfo(
                        provider=ProviderType.OPENROUTER,
                        model_name=model_id,
                        context_window=int(
                            context_window
                        ),
                        supports_streaming=True,
                    )
                )

            return models

        except Exception as exc:
            raise RuntimeError(
                "Failed to retrieve models from OpenRouter."
            ) from exc

    # ============================================================
    # USAGE NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_usage(
        usage: Any,
    ) -> Usage:

        if usage is None:
            return Usage()

        prompt_tokens = getattr(
            usage,
            "prompt_tokens",
            0,
        ) or 0

        completion_tokens = getattr(
            usage,
            "completion_tokens",
            0,
        ) or 0

        total_tokens = getattr(
            usage,
            "total_tokens",
            0,
        ) or 0

        return Usage(
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            total_tokens=int(total_tokens),
        )

    # ============================================================
    # CLOSE
    # ============================================================

    async def close(self) -> None:
        await self.client.close()

    # ============================================================
    # CONTEXT MANAGER
    # ============================================================

    async def __aenter__(self) -> "OpenRouterProvider":
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:
        await self.close()

