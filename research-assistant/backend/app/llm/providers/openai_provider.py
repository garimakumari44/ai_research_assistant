from __future__ import annotations

from typing import AsyncGenerator

from openai import AsyncOpenAI

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


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI implementation.
    """

    def __init__(
        self,
        model_name: str,
    ):
        super().__init__(model_name)

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    def _convert_messages(
        self,
        messages: list[ChatMessage],
    ) -> list[dict]:
        """
        Convert internal messages into OpenAI format.
        """

        return [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in messages
        ]

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        response = await self.client.chat.completions.create(
            model=request.model or self.model_name,
            messages=self._convert_messages(request.messages),
            temperature=request.config.temperature,
            max_tokens=request.config.max_tokens,
            top_p=request.config.top_p,
        )

        choice = response.choices[0]

        usage = Usage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return LLMResponse(
            text=choice.message.content or "",
            provider=ProviderType.OPENAI,
            model=response.model,
            usage=usage,
        )

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[StreamingChunk, None]:

        stream = await self.client.chat.completions.create(
            model=request.model or self.model_name,
            messages=self._convert_messages(request.messages),
            temperature=request.config.temperature,
            max_tokens=request.config.max_tokens,
            top_p=request.config.top_p,
            stream=True,
        )

        async for chunk in stream:

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta.content

            if delta:

                yield StreamingChunk(
                    text=delta,
                    finished=False,
                )

        yield StreamingChunk(
            text="",
            finished=True,
        )

    async def health_check(self) -> bool:
        """
        Verify API connectivity.
        """

        try:

            await self.client.models.list()

            return True

        except Exception:

            return False

    async def count_tokens(
        self,
        text: str,
    ) -> int:
        """
        Approximate token count.

        This can later be replaced with tiktoken.
        """

        return max(1, len(text) // 4)

    async def list_models(
        self,
    ) -> list[ModelInfo]:

        models = await self.client.models.list()

        return [
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name=model.id,
                context_window=0,
                supports_streaming=True,
            )
            for model in models.data
        ]