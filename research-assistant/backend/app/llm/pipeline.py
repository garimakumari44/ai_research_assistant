
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.llm.models import (
    ChatMessage,
    GenerationConfig,
    LLMRequest,
    LLMResponse,
    MessageRole,
)


# ============================================================
# PIPELINE RESULT
# ============================================================


@dataclass
class LLMPipelineResult:
    """
    Provider-agnostic result consumed by research components.
    """

    content: str

    provider: Optional[str] = None

    model: Optional[str] = None

    prompt: Optional[str] = None

    usage: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    raw_response: Optional[LLMResponse] = None


# ============================================================
# PIPELINE
# ============================================================


class LLMPipeline:
    """
    Application-level LLM orchestration layer.

    All calls ultimately go through OpenRouterProvider.
    """

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
    ) -> None:

        self.provider = (
            provider
            or get_llm_provider()
        )

    # ============================================================
    # MESSAGE NORMALIZATION
    # ============================================================

    @staticmethod
    def _build_messages(
        prompt: str,
        system_prompt: str | None = None,
        messages: Sequence[
            dict[str, Any]
        ] | None = None,
    ) -> list[ChatMessage]:

        normalized: list[ChatMessage] = []

        if system_prompt:
            normalized.append(
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=system_prompt,
                )
            )

        if messages:

            for message in messages:

                role = message.get("role")

                if isinstance(role, MessageRole):
                    message_role = role
                else:
                    message_role = MessageRole(
                        str(role)
                    )

                normalized.append(
                    ChatMessage(
                        role=message_role,
                        content=str(
                            message.get(
                                "content",
                                "",
                            )
                        ),
                    )
                )

        elif prompt:

            normalized.append(
                ChatMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )
            )

        return normalized

    # ============================================================
    # GENERATE
    # ============================================================

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: Sequence[
            dict[str, Any]
        ] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> LLMPipelineResult:

        if not prompt and not messages:
            raise ValueError(
                "LLMPipeline.generate() requires "
                "`prompt` or `messages`."
            )

        built_messages = self._build_messages(
            prompt=prompt,
            system_prompt=system_prompt,
            messages=messages,
        )

        config = GenerationConfig(
            temperature=(
                temperature
                if temperature is not None
                else 0.2
            ),
            max_tokens=(
                max_tokens
                if max_tokens is not None
                else 1024
            ),
            top_p=(
                top_p
                if top_p is not None
                else 1.0
            ),
            stop_sequences=(
                list(stop)
                if stop is not None
                else []
            ),
            stream=False,
        )

        metadata: dict[str, Any] = {}

        if kwargs:
            metadata["provider_options"] = kwargs

        request = LLMRequest(
            messages=built_messages,
            config=config,
            model=model,
            metadata=metadata,
        )

        response = await self.provider.generate(
            request
        )

        if not response.text.strip():
            raise RuntimeError(
                "LLM provider returned an empty response."
            )

        return LLMPipelineResult(
            content=response.text,
            provider=response.provider.value,
            model=response.model,
            prompt=prompt,
            usage=response.usage.model_dump(),
            metadata={
                **response.metadata,
                "message_count": len(
                    built_messages
                ),
            },
            raw_response=response,
        )

    # ============================================================
    # SIMPLE ASK API
    # ============================================================

    async def ask(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:

        result = await self.generate(
            prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return result.content

    # ============================================================
    # CHAT API
    # ============================================================

    async def chat(
        self,
        messages: Sequence[
            dict[str, Any]
        ],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMPipelineResult:

        if not messages:
            raise ValueError(
                "LLMPipeline.chat() requires at least one message."
            )

        return await self.generate(
            prompt="",
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    # ============================================================
    # RESEARCH API
    # ============================================================

    async def research(
        self,
        question: str,
        *,
        context: str | None = None,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMPipelineResult:

        if not question.strip():
            raise ValueError(
                "Research question must not be empty."
            )

        sections: list[str] = []

        if context:
            sections.append(
                "RESEARCH CONTEXT:\n"
                + context
            )

        sections.append(
            "RESEARCH QUESTION:\n"
            + question
        )

        prompt = "\n\n".join(sections)

        return await self.generate(
            prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    # ============================================================
    # JSON API
    # ============================================================

    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:

        json_instruction = (
            "Return ONLY valid JSON. "
            "Do not use markdown code fences. "
            "Do not include explanations outside the JSON."
        )

        combined_system_prompt = (
            f"{system_prompt}\n\n{json_instruction}"
            if system_prompt
            else json_instruction
        )

        result = await self.generate(
            prompt,
            system_prompt=combined_system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        content = result.content.strip()

        if content.startswith("```json"):
            content = content[7:]

        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "OpenRouter returned invalid JSON.\n\n"
                f"Response:\n{result.content}"
            ) from exc

    # ============================================================
    # PROVIDER
    # ============================================================

    @property
    def provider_name(self) -> str:
        return self.provider.provider_name


# ============================================================
# APPLICATION SINGLETON
# ============================================================


_default_pipeline: LLMPipeline | None = None


def get_llm_pipeline() -> LLMPipeline:

    global _default_pipeline

    if _default_pipeline is None:
        _default_pipeline = LLMPipeline()

    return _default_pipeline


# ============================================================
# MODULE-LEVEL HELPERS
# ============================================================


async def generate(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> LLMPipelineResult:

    return await get_llm_pipeline().generate(
        prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


async def ask(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> str:

    return await get_llm_pipeline().ask(
        prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )

