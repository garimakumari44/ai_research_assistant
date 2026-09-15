from __future__ import annotations

from typing import AsyncGenerator

from ollama import AsyncClient

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


class OllamaProvider(BaseLLMProvider):
    """
    Ollama implementation.

    Supports any locally installed model:
    - qwen3
    - llama3
    - mistral
    - deepseek-r1
    - phi4
    """

    def __init__(
        self,
        model_name: str,
    ):
        super().__init__(model_name)

        self.client = AsyncClient(
            host=settings.ollama_base_url,
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _convert_messages(
        self,
        messages: list[ChatMessage],
    ) -> list[dict]:
        """
        Convert internal messages into Ollama format.
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

        response = await self.client.chat(
            model=request.model or self.model_name,
            messages=self._convert_messages(request.messages),
            options={
                "temperature": request.config.temperature,
                "top_p": request.config.top_p,
                "num_predict": request.config.max_tokens,
            },
        )

        usage = Usage(
            prompt_tokens=response.get("prompt_eval_count", 0),
            completion_tokens=response.get("eval_count", 0),
            total_tokens=(
                response.get("prompt_eval_count", 0)
                + response.get("eval_count", 0)
            ),
        )

        return LLMResponse(
            text=response["message"]["content"],
            provider=ProviderType.OLLAMA,
            model=request.model or self.model_name,
            usage=usage,
        )

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[StreamingChunk, None]:

        stream = await self.client.chat(
            model=request.model or self.model_name,
            messages=self._convert_messages(request.messages),
            stream=True,
            options={
                "temperature": request.config.temperature,
                "top_p": request.config.top_p,
                "num_predict": request.config.max_tokens,
            },
        )

        async for chunk in stream:

            content = chunk.get("message", {}).get("content", "")

            if content:

                yield StreamingChunk(
                    text=content,
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

            await self.client.list()

            return True

        except Exception:

            return False

    async def count_tokens(
        self,
        text: str,
    ) -> int:
        """
        Approximate token count.

        Later this can be upgraded to use model-specific
        tokenizers if needed.
        """

        return max(1, len(text) // 4)

    async def list_models(
        self,
    ) -> list[ModelInfo]:

        response = await self.client.list()

        models = []

        for model in response.get("models", []):

            models.append(
                ModelInfo(
                    provider=ProviderType.OLLAMA,
                    model_name=model["name"],
                    context_window=0,
                    supports_streaming=True,
                )
            )

        return models