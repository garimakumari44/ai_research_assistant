
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class UnsupportedClaim:
    claim: str
    confidence: float
    reason: str
    supporting_evidence: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HallucinationResult:
    """
    Result of hallucination/support analysis.
    """

    has_hallucinations: bool
    hallucination_score: float
    unsupported_claims: tuple[UnsupportedClaim, ...]
    supported_claim_ratio: float
    reasons: tuple[str, ...] = ()

    @property
    def safe(self) -> bool:
        return not self.has_hallucinations


class HallucinationDetector:
    """
    Detects potentially unsupported claims in a generated answer.

    The detector uses conservative sentence-to-evidence lexical overlap.

    Production deployments should combine this result with:
        - NLI / entailment models
        - citation validation
        - source provenance
        - LLM-based claim verification

    It intentionally avoids declaring a claim hallucinated merely because
    exact wording differs.
    """

    def __init__(
        self,
        *,
        min_claim_overlap: float = 0.12,
        high_risk_threshold: float = 0.80,
        min_claim_length: int = 5,
    ) -> None:
        if not 0.0 <= min_claim_overlap <= 1.0:
            raise ValueError("min_claim_overlap must be between 0 and 1")

        if not 0.0 <= high_risk_threshold <= 1.0:
            raise ValueError("high_risk_threshold must be between 0 and 1")

        if min_claim_length < 1:
            raise ValueError("min_claim_length must be >= 1")

        self.min_claim_overlap = min_claim_overlap
        self.high_risk_threshold = high_risk_threshold
        self.min_claim_length = min_claim_length

    def detect(
        self,
        answer: str,
        evidence: Sequence[Any] | None,
    ) -> HallucinationResult:
        answer = answer.strip()

        if not answer:
            return HallucinationResult(
                has_hallucinations=True,
                hallucination_score=1.0,
                unsupported_claims=(
                    UnsupportedClaim(
                        claim="",
                        confidence=1.0,
                        reason="The generated answer is empty.",
                    ),
                ),
                supported_claim_ratio=0.0,
                reasons=("No answer was generated.",),
            )

        evidence_text = [
            self._content(item)
            for item in evidence or ()
        ]

        evidence_text = [
            text
            for text in evidence_text
            if text.strip()
        ]

        if not evidence_text:
            return HallucinationResult(
                has_hallucinations=True,
                hallucination_score=1.0,
                unsupported_claims=(
                    UnsupportedClaim(
                        claim=answer,
                        confidence=1.0,
                        reason="No evidence is available against which "
                               "the answer can be verified.",
                    ),
                ),
                supported_claim_ratio=0.0,
                reasons=("Answer cannot be grounded because evidence is empty.",),
            )

        claims = self._split_claims(answer)

        unsupported: list[UnsupportedClaim] = []
        supported_count = 0

        for claim in claims:
            if len(claim.split()) < self.min_claim_length:
                continue

            overlap, supporting = self._best_support(
                claim,
                evidence_text,
            )

            if overlap >= self.min_claim_overlap:
                supported_count += 1
                continue

            risk = max(
                0.0,
                min(
                    1.0,
                    1.0 - overlap,
                ),
            )

            unsupported.append(
                UnsupportedClaim(
                    claim=claim,
                    confidence=risk,
                    reason=(
                        "No sufficiently strong lexical support was found "
                        "in the retrieved evidence."
                    ),
                    supporting_evidence=tuple(supporting[:2]),
                )
            )

        meaningful_claim_count = max(
            1,
            sum(
                1
                for claim in claims
                if len(claim.split()) >= self.min_claim_length
            ),
        )

        supported_ratio = supported_count / meaningful_claim_count

        if unsupported:
            hallucination_score = max(
                claim.confidence
                for claim in unsupported
            )
        else:
            hallucination_score = 0.0

        has_hallucinations = any(
            claim.confidence >= self.high_risk_threshold
            for claim in unsupported
        )

        reasons: list[str] = []

        if unsupported:
            reasons.append(
                f"{len(unsupported)} potentially unsupported claim(s) detected."
            )

        if not has_hallucinations and unsupported:
            reasons.append(
                "Potential support gaps were detected but none exceeded "
                "the high-risk threshold."
            )

        if not unsupported:
            reasons.append("All meaningful claims have evidence overlap.")

        return HallucinationResult(
            has_hallucinations=has_hallucinations,
            hallucination_score=max(
                0.0,
                min(1.0, hallucination_score),
            ),
            unsupported_claims=tuple(unsupported),
            supported_claim_ratio=max(
                0.0,
                min(1.0, supported_ratio),
            ),
            reasons=tuple(reasons),
        )

    def _best_support(
        self,
        claim: str,
        evidence: Sequence[str],
    ) -> tuple[float, list[str]]:
        claim_tokens = self._tokens(claim)

        if not claim_tokens:
            return 0.0, []

        scored: list[tuple[float, str]] = []

        for text in evidence:
            evidence_tokens = self._tokens(text)

            if not evidence_tokens:
                continue

            overlap = len(claim_tokens & evidence_tokens) / len(
                claim_tokens
            )

            scored.append((overlap, text))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        if not scored:
            return 0.0, []

        return scored[0][0], [
            text
            for score, text in scored
            if score > 0
        ]

    def _split_claims(self, answer: str) -> list[str]:
        parts = re.split(
            r"(?<=[.!?])\s+|\n+|;\s+",
            answer,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    def _tokens(self, text: str) -> set[str]:
        words = re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]{2,}\b",
            text.lower(),
        )

        stop_words = {
            "the",
            "and",
            "for",
            "that",
            "this",
            "with",
            "from",
            "are",
            "was",
            "were",
            "have",
            "has",
            "had",
            "been",
            "being",
            "into",
            "about",
            "than",
            "then",
            "they",
            "their",
            "there",
            "which",
            "would",
            "could",
            "should",
            "also",
        }

        return {
            word
            for word in words
            if word not in stop_words
        }

    @staticmethod
    def _content(item: Any) -> str:
        if isinstance(item, Mapping):
            for key in (
                "content",
                "text",
                "chunk",
                "page_content",
            ):
                value = item.get(key)
                if value:
                    return str(value)

        for attr in (
            "content",
            "text",
            "chunk",
            "page_content",
        ):
            value = getattr(item, attr, None)
            if value:
                return str(value)

        return ""

