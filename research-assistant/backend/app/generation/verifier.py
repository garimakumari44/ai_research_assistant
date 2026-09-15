"""
Answer verification for the generation layer.

Responsibilities:
- Validate generated answers against retrieved evidence.
- Validate citation references.
- Detect obvious unsupported claims using an LLM verifier.
- Produce structured verification results.
- Never expose hidden chain-of-thought.

The verifier is intentionally independent from retrieval.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .citation import CitationManager, CitationValidation
from .llm import BaseLLM, LLMConfig, create_llm
from .prompts import (
    SYSTEM_PROMPT,
    build_verification_prompt,
)
from .synthesizer import EvidenceItem, GeneratedAnswer


class VerificationError(RuntimeError):
    """Raised when answer verification fails."""


@dataclass(slots=True)
class VerificationResult:
    """
    Structured result of answer verification.
    """

    passed: bool

    grounding_score: float

    citation_validation: CitationValidation

    unsupported_claims: list[str] = field(
        default_factory=list
    )

    supported_claims: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    reasons: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class VerificationThresholds:
    """
    Controls the verifier's acceptance criteria.
    """

    minimum_grounding_score: float = 0.70

    require_citations: bool = True

    reject_invalid_citations: bool = True

    reject_empty_answers: bool = True

    max_unsupported_claims: int = 0


class AnswerVerifier:
    """
    Verifies generated answers against retrieved evidence.
    """

    def __init__(
        self,
        llm: BaseLLM | None = None,
        *,
        llm_config: LLMConfig | None = None,
        thresholds: VerificationThresholds | None = None,
    ) -> None:
        self.llm = llm or create_llm(llm_config)

        self.thresholds = (
            thresholds
            or VerificationThresholds()
        )

    async def verify(
        self,
        generated: GeneratedAnswer,
        evidence: Iterable[EvidenceItem],
    ) -> VerificationResult:
        """
        Verify a generated answer.
        """

        evidence_list = list(evidence)

        answer = generated.answer.strip()

        citation_validation = (
            CitationManager.validate(
                answer,
                evidence_list,
                require_citations=(
                    self.thresholds.require_citations
                ),
            )
        )

        warnings = list(
            citation_validation.warnings
        )

        reasons: list[str] = []

        if (
            self.thresholds.reject_empty_answers
            and not answer
        ):
            reasons.append(
                "Generated answer is empty."
            )

            return VerificationResult(
                passed=False,
                grounding_score=0.0,
                citation_validation=citation_validation,
                warnings=warnings,
                reasons=reasons,
            )

        llm_result = await self._verify_with_llm(
            question=generated.question,
            answer=answer,
            evidence=evidence_list,
        )

        grounding_score = self._extract_grounding_score(
            llm_result
        )

        unsupported_claims = (
            self._extract_string_list(
                llm_result,
                "unsupported_claims",
            )
        )

        supported_claims = (
            self._extract_string_list(
                llm_result,
                "supported_claims",
            )
        )

        if (
            self.thresholds.reject_invalid_citations
            and citation_validation.invalid_ids
        ):
            reasons.append(
                "Answer contains invalid citation references."
            )

        if (
            self.thresholds.require_citations
            and not citation_validation.citations
        ):
            reasons.append(
                "Answer does not contain citations."
            )

        if (
            grounding_score
            < self.thresholds.minimum_grounding_score
        ):
            reasons.append(
                "Grounding score is below the required threshold."
            )

        if (
            len(unsupported_claims)
            > self.thresholds.max_unsupported_claims
        ):
            reasons.append(
                "Answer contains unsupported factual claims."
            )

        passed = not reasons

        return VerificationResult(
            passed=passed,
            grounding_score=grounding_score,
            citation_validation=citation_validation,
            unsupported_claims=unsupported_claims,
            supported_claims=supported_claims,
            warnings=warnings,
            reasons=reasons,
            metadata={
                "model": self.llm.config.model,
                "provider": self.llm.config.provider,
                "evidence_count": len(
                    evidence_list
                ),
                "cited_evidence_count": len(
                    citation_validation.valid_ids
                ),
            },
        )

    async def _verify_with_llm(
        self,
        *,
        question: str,
        answer: str,
        evidence: list[EvidenceItem],
    ) -> dict[str, Any]:
        """
        Ask the configured LLM to evaluate factual grounding.

        The LLM is instructed to return JSON only.
        """

        evidence_text = "\n\n".join(
            [
                (
                    f"[{item.id}]\n"
                    f"{item.content}"
                )
                for item in evidence
            ]
        )

        prompt = build_verification_prompt(
            question=question,
            answer=answer,
            evidence=evidence_text,
        )

        prompt += """

Return ONLY valid JSON using this structure:

{
  "grounding_score": 0.0,
  "supported_claims": [],
  "unsupported_claims": [],
  "citation_issues": [],
  "summary": ""
}

grounding_score must be a number between 0 and 1.

Do not include hidden reasoning or chain-of-thought.
Only provide concise verification findings.
"""

        try:
            response = await self.llm.generate(
                prompt,
                system_prompt=SYSTEM_PROMPT,
            )
        except Exception as exc:
            raise VerificationError(
                f"LLM verification failed: {exc}"
            ) from exc

        return self._parse_json_response(
            response
        )

    @staticmethod
    def _parse_json_response(
        response: str,
    ) -> dict[str, Any]:
        """
        Parse JSON from the verifier response.

        Handles models that accidentally surround JSON
        with markdown code fences.
        """

        cleaned = response.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

            cleaned = re.sub(
                r"\s*```$",
                "",
                cleaned,
            )

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError:
            # Try extracting the first JSON object.
            match = re.search(
                r"\{.*\}",
                cleaned,
                flags=re.DOTALL,
            )

            if not match:
                raise VerificationError(
                    "Verifier returned invalid JSON."
                )

            try:
                data = json.loads(
                    match.group(0)
                )
            except json.JSONDecodeError as exc:
                raise VerificationError(
                    "Verifier returned malformed JSON."
                ) from exc

        if not isinstance(data, dict):
            raise VerificationError(
                "Verifier response must be a JSON object."
            )

        return data

    @staticmethod
    def _extract_grounding_score(
        data: dict[str, Any],
    ) -> float:
        """
        Safely extract and clamp the grounding score.
        """

        value = data.get(
            "grounding_score",
            0.0,
        )

        try:
            score = float(value)
        except (
            TypeError,
            ValueError,
        ):
            score = 0.0

        return max(
            0.0,
            min(1.0, score),
        )

    @staticmethod
    def _extract_string_list(
        data: dict[str, Any],
        key: str,
    ) -> list[str]:
        """
        Extract a list of strings from verifier output.
        """

        value = data.get(key, [])

        if not isinstance(value, list):
            return []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    async def verify_answer(
        self,
        question: str,
        answer: str,
        evidence: Iterable[EvidenceItem],
    ) -> VerificationResult:
        """
        Convenience API when the caller does not already have
        a GeneratedAnswer object.
        """

        evidence_list = list(evidence)

        generated = GeneratedAnswer(
            answer=answer,
            question=question,
            evidence_ids=[
                item.id
                for item in evidence_list
            ],
            model=self.llm.config.model,
            provider=self.llm.config.provider,
        )

        return await self.verify(
            generated,
            evidence_list,
        )


def verify_citation_integrity(
    answer: str,
    evidence: Iterable[EvidenceItem],
    *,
    require_citations: bool = True,
) -> CitationValidation:
    """
    Fast citation-only verification.

    This does not make an LLM call.
    """

    return CitationManager.validate(
        answer,
        evidence,
        require_citations=require_citations,
    )