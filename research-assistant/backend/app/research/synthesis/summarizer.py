
from __future__ import annotations

from typing import Literal

from app.llm.base import BaseLLMProvider
from app.llm.models import (
    ChatMessage,
    LLMRequest,
    GenerationConfig,
    MessageRole,
)
from app.research.models import ResearchSection


SummaryLevel = Literal[
    "executive",
    "technical",
    "detailed",
]


class ResearchSummarizer:
    """
    Generates LLM-powered summaries from research sections.

    Summary levels:

        - executive
        - technical
        - detailed
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
    ):
        self.llm_provider = llm_provider

    # ============================================================
    # Public API
    # ============================================================

    async def summarize(
        self,
        sections: list[ResearchSection],
        level: SummaryLevel = "technical",
    ) -> str:
        """
        Generate a summary from research sections.
        """

        if not sections:
            return ""

        prompt = self._build_prompt(
            sections=sections,
            level=level,
        )

        request = LLMRequest(
            messages=[
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=self._system_prompt(level),
                ),
                ChatMessage(
                    role=MessageRole.USER,
                    content=prompt,
                ),
            ],
            config=GenerationConfig(
                temperature=0.2,
                max_tokens=2048,
            ),
        )

        response = await self.llm_provider.generate(
            request
        )

        return response.text.strip()

    # ============================================================
    # Prompt Construction
    # ============================================================

    def _system_prompt(
        self,
        level: SummaryLevel,
    ) -> str:
        if level == "executive":
            return """
You are an executive research analyst.

Create a concise, decision-oriented summary.

Focus on:
- Most important findings
- Business implications
- Key risks
- Important conclusions

Do not invent facts.
Use only the supplied research evidence.
""".strip()

        if level == "technical":
            return """
You are a technical research analyst.

Create a structured and accurate technical summary.

Focus on:
- Major findings
- Supporting evidence
- Technical details
- Relationships between findings
- Limitations

Do not invent facts.
Use only the supplied research evidence.
""".strip()

        return """
You are a senior research analyst.

Create a detailed research synthesis.

Include:
- Background
- Major findings
- Supporting evidence
- Important implications
- Risks or limitations
- Overall conclusion

Do not invent facts.
Use only the supplied research evidence.
""".strip()

    def _build_prompt(
        self,
        sections: list[ResearchSection],
        level: SummaryLevel,
    ) -> str:
        parts = [
            f"Create a {level} research summary.",
            "",
            "Research sections:",
            "",
        ]

        for section in sections:
            parts.append(
                f"## {section.title}"
            )

            parts.append(
                section.content
            )

            if section.evidence_ids:
                parts.append(
                    "Evidence IDs: "
                    + ", ".join(section.evidence_ids)
                )

            parts.append("")

        return "\n".join(parts)

