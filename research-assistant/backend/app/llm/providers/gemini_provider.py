from __future__ import annotations

from typing import AsyncGenerator

from google import genai
from google.genai.types import GenerateContentConfig

from app.llm.base import BaseLLMProvider
from app.llm.config import settings
from app.llm.models import (
    ChatMessage,
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ProviderType,
    StreamingChunk,
    Usage,
)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini implementation.
    """

    def __init__(
        self,
        model_name: str,
    ):
        super().__init__(model_name)

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _build_prompt(
        self,
        messages: list[ChatMessage],
    ) -> str:
        """
        Convert chat messages into a prompt.

        Gemini can accept structured content, but using a
        unified prompt keeps all providers consistent.
        """

        prompt = []

        for message in messages:
            prompt.append(
                f"{message.role.value.upper()}:\n{message.content}"
            )

        return "\n\n".join(prompt)

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        response = await self.client.aio.models.generate_content(
            model=request.model or self.model_name,
            contents=self._build_prompt(request.messages),
            config=GenerateContentConfig(
                temperature=request.config.temperature,
                top_p=request.config.top_p,
                max_output_tokens=request.config.max_tokens,
            ),
        )

        usage = Usage()

        if response.usage_metadata:

            usage.prompt_tokens = (
                response.usage_metadata.prompt_token_count
            )

            usage.completion_tokens = (
                response.usage_metadata.candidates_token_count
            )

            usage.total_tokens = (
                response.usage_metadata.total_token_count
            )

        return LLMResponse(
            text=response.text,
            provider=ProviderType.GEMINI,
            model=request.model or self.model_name,
            usage=usage,
        )

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[StreamingChunk, None]:

        stream = await self.client.aio.models.generate_content_stream(
            model=request.model or self.model_name,
            contents=self._build_prompt(request.messages),
            config=GenerateContentConfig(
                temperature=request.config.temperature,
                top_p=request.config.top_p,
                max_output_tokens=request.config.max_tokens,
            ),
        )

        async for chunk in stream:

            if chunk.text:

                yield StreamingChunk(
                    text=chunk.text,
                    finished=False,
                )

        yield StreamingChunk(
            text="",
            finished=True,
        )

    async def health_check(
        self,
    ) -> bool:

        try:

            await self.client.aio.models.generate_content(
                model=self.model_name,
                contents="Hello",
            )

            return True

        except Exception:

            return False

    async def count_tokens(
        self,
        text: str,
    ) -> int:
        """
        Approximate token count.

        Can later be upgraded to Gemini's tokenizer API.
        """

        return max(1, len(text) // 4)

    async def list_models(
        self,
    ) -> list[ModelInfo]:

        models = await self.client.aio.models.list()

        result = []

        async for model in models:

            result.append(
                ModelInfo(
                    provider=ProviderType.GEMINI,
                    model_name=model.name,
                    context_window=0,
                    supports_streaming=True,
                )
            )

        return result