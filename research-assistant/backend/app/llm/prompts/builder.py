from __future__ import annotations

from app.llm.models import (
    ChatMessage,
    LLMRequest,
    MessageRole,
)
from app.llm.prompts.citation import get_citation_instructions
from app.llm.prompts.system import (
    SystemPromptType,
    get_system_prompt,
)
from app.llm.prompts.templates import (
    PromptTemplateType,
    get_prompt_template,
)


class PromptBuilder:
    """
    Builds provider-agnostic prompts for the LLM layer.
    """

    @staticmethod
    def build_rag_prompt(
        *,
        question: str,
        context: str,
        history: list[ChatMessage] | None = None,
    ) -> LLMRequest:
        """
        Build a Retrieval-Augmented Generation prompt.
        """

        template = get_prompt_template(
            PromptTemplateType.RAG,
        )

        prompt = template.format(
            context=context,
            question=question,
        )

        system_prompt = "\n\n".join(
            [
                get_system_prompt(SystemPromptType.RAG),
                get_citation_instructions(),
            ]
        )

        messages: list[ChatMessage] = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_prompt,
            )
        ]

        if history:
            messages.extend(history)

        messages.append(
            ChatMessage(
                role=MessageRole.USER,
                content=prompt,
            )
        )

        return LLMRequest(
            messages=messages,
        )

    @staticmethod
    def build_chat_prompt(
        *,
        question: str,
        history: list[ChatMessage] | None = None,
    ) -> LLMRequest:
        """
        Build a standard chat prompt.
        """

        system_prompt = get_system_prompt(
            SystemPromptType.DEFAULT,
        )

        messages: list[ChatMessage] = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_prompt,
            )
        ]

        if history:
            messages.extend(history)

        messages.append(
            ChatMessage(
                role=MessageRole.USER,
                content=question,
            )
        )

        return LLMRequest(
            messages=messages,
        )

    @staticmethod
    def build_summary_prompt(
        *,
        document: str,
    ) -> LLMRequest:
        """
        Build a document summarization prompt.
        """

        template = get_prompt_template(
            PromptTemplateType.SUMMARIZATION,
        )

        prompt = template.format(
            document=document,
        )

        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=get_system_prompt(
                    SystemPromptType.SUMMARIZATION,
                ),
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=prompt,
            ),
        ]

        return LLMRequest(
            messages=messages,
        )