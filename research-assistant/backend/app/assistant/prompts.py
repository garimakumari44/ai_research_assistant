from __future__ import annotations

from typing import Any, Iterable, List, Optional

from app.assistant.models import (
    AssistantContext,
    AssistantMessage,
)


class AssistantPromptBuilder:
    """
    Builds prompts for the assistant.

    The prompt layer contains no LLM/provider logic.
    """

    DEFAULT_SYSTEM_PROMPT = """
You are an AI research assistant.

Your responsibilities are:

1. Answer the user's question accurately and clearly.
2. Use provided research or retrieval context when available.
3. Do not invent facts, sources, citations, or evidence.
4. Distinguish retrieved evidence from your own reasoning.
5. If the available evidence is insufficient, say so explicitly.
6. Prefer precise technical explanations over vague claims.
7. When sources are provided, ground factual claims in those sources.
8. Do not claim that you accessed information that was not provided.
""".strip()

    RESEARCH_SYSTEM_PROMPT = """
You are a research-oriented AI assistant.

Produce evidence-grounded answers from the supplied research context.

Requirements:

- Separate established findings from interpretation.
- Identify uncertainty and limitations.
- Do not fabricate citations.
- Prefer primary sources when available.
- Compare competing approaches fairly.
- Explain methodological limitations where relevant.
- Use retrieved evidence as the factual foundation.
""".strip()

    RAG_SYSTEM_PROMPT = """
You are a retrieval-augmented AI assistant.

Use the supplied retrieved context to answer the user.

Requirements:

- Prioritize retrieved evidence over unsupported assumptions.
- Do not hallucinate information absent from the context.
- If the context does not answer the question, clearly state that.
- Synthesize multiple relevant sources when possible.
- Keep the final answer directly relevant to the user's request.
""".strip()

    def build_system_prompt(
        self,
        *,
        mode: str = "chat",
        additional_instructions: Optional[str] = None,
    ) -> str:
        if mode == "research":
            prompt = self.RESEARCH_SYSTEM_PROMPT

        elif mode == "rag":
            prompt = self.RAG_SYSTEM_PROMPT

        else:
            prompt = self.DEFAULT_SYSTEM_PROMPT

        if additional_instructions:
            prompt += (
                "\n\nAdditional instructions:\n"
                + additional_instructions.strip()
            )

        return prompt

    def build_messages(
        self,
        context: AssistantContext,
        *,
        system_prompt: Optional[str] = None,
    ) -> List[AssistantMessage]:
        messages: List[AssistantMessage] = []

        prompt = system_prompt or self.build_system_prompt(
            mode=context.request.mode
        )

        messages.append(
            AssistantMessage(
                role="system",
                content=prompt,
            )
        )

        messages.extend(
            context.conversation
        )

        return messages

    def build_user_prompt(
        self,
        context: AssistantContext,
    ) -> str:
        user_message = context.request.message

        retrieval_block = self._build_retrieval_context(
            context.retrieved_context
        )

        research_block = self._build_research_context(
            context.research_result
        )

        sections = [
            f"User request:\n{user_message}",
        ]

        if retrieval_block:
            sections.append(
                retrieval_block
            )

        if research_block:
            sections.append(
                research_block
            )

        return "\n\n".join(
            sections
        )

    # ========================================================================
    # RETRIEVAL
    # ========================================================================

    def _build_retrieval_context(
        self,
        items: Iterable[Any],
    ) -> str:
        items = list(items)

        if not items:
            return ""

        lines = [
            "Retrieved context:"
        ]

        for index, item in enumerate(
            items[:20],
            start=1,
        ):
            data = self._to_dict(item)

            title = (
                data.get("title")
                or data.get("name")
                or f"Retrieved item {index}"
            )

            text = (
                data.get("text")
                or data.get("content")
                or data.get("abstract")
                or data.get("description")
                or ""
            )

            score = data.get(
                "score"
            )

            line = (
                f"[{index}] {title}"
            )

            if score is not None:
                line += (
                    f" (score={score})"
                )

            if text:
                line += (
                    f"\n{text}"
                )

            lines.append(
                line
            )

        return "\n".join(
            lines
        )

    # ========================================================================
    # RESEARCH
    # ========================================================================

    def _build_research_context(
        self,
        research_result: Any,
    ) -> str:
        if research_result is None:
            return ""

        data = self._to_dict(
            research_result
        )

        if not data:
            return ""

        lines = [
            "Research context:"
        ]

        summary = data.get(
            "summary"
        )

        if summary:
            lines.append(
                f"Summary:\n{summary}"
            )

        sections = data.get(
            "sections",
            [],
        )

        if isinstance(
            sections,
            list,
        ):
            for section in sections:
                section_data = self._to_dict(
                    section
                )

                title = section_data.get(
                    "title",
                    "Section",
                )

                content = section_data.get(
                    "content",
                    "",
                )

                if content:
                    lines.append(
                        f"{title}:\n{content}"
                    )

        return "\n\n".join(
            lines
        )

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    @staticmethod
    def _to_dict(
        value: Any,
    ) -> dict[str, Any]:
        if value is None:
            return {}

        if isinstance(
            value,
            dict,
        ):
            return dict(value)

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                result = value.model_dump()

                if isinstance(
                    result,
                    dict,
                ):
                    return result

            except Exception:
                pass

        if hasattr(
            value,
            "__dict__",
        ):
            try:
                return dict(
                    value.__dict__
                )
            except Exception:
                pass

        return {
            "content": str(value)
        }


def get_prompt_builder() -> AssistantPromptBuilder:
    """Return a stateless prompt builder."""

    return AssistantPromptBuilder()