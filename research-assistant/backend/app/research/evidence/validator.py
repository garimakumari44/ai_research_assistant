
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, Iterable

from app.research.models import Evidence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceValidationResult:
    """
    Deterministic validation result for a set of evidence items.
    """

    accepted: tuple[Evidence, ...]
    rejected: tuple[Evidence, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def acceptance_rate(self) -> float:
        total = len(self.accepted) + len(self.rejected)

        if total == 0:
            return 0.0

        return round(
            len(self.accepted) / total,
            4,
        )


class EvidenceValidator:
    """
    Validates and scores research evidence.

    Validation is deterministic and does not use an LLM.

    Important:
        This validator does not mutate Evidence objects. This avoids
        compatibility problems with frozen dataclasses and immutable
        Pydantic models.
    """

    def __init__(
        self,
        *,
        min_confidence: float = 0.0,
        min_relevance_score: float = 0.0,
        min_content_length: int = 30,
        require_identifier: bool = True,
        require_source: bool = True,
    ) -> None:
        self.min_confidence = self._validate_threshold(
            min_confidence,
            "min_confidence",
        )

        self.min_relevance_score = self._validate_threshold(
            min_relevance_score,
            "min_relevance_score",
        )

        if min_content_length < 1:
            raise ValueError(
                "min_content_length must be greater than zero"
            )

        self.min_content_length = min_content_length
        self.require_identifier = require_identifier
        self.require_source = require_source

    def validate(
        self,
        evidence_items: Iterable[Evidence],
    ) -> EvidenceValidationResult:
        """
        Validate evidence items and return a structured result.
        """

        accepted: list[Evidence] = []
        rejected: list[Evidence] = []
        errors: list[str] = []

        if evidence_items is None:
            return EvidenceValidationResult(
                accepted=(),
                rejected=(),
                errors=(),
            )

        for evidence in evidence_items:
            item_errors = self._validate_item(
                evidence
            )

            if item_errors:
                rejected.append(evidence)

                evidence_id = getattr(
                    evidence,
                    "id",
                    "unknown",
                )

                errors.extend(
                    f"{evidence_id}: {error}"
                    for error in item_errors
                )
            else:
                accepted.append(evidence)

        return EvidenceValidationResult(
            accepted=tuple(accepted),
            rejected=tuple(rejected),
            errors=tuple(errors),
        )

    def validate_and_score(
        self,
        evidence_items: Iterable[Evidence],
    ) -> list[Evidence]:
        """
        Validate evidence and return accepted items ordered by quality.

        Evidence objects are not mutated.
        """

        result = self.validate(evidence_items)

        scored = sorted(
            result.accepted,
            key=self.quality_key,
            reverse=True,
        )

        return scored

    def calculate_confidence(
        self,
        evidence: Evidence,
    ) -> float:
        """
        Calculate deterministic confidence.

        Factors:

            - existing confidence
            - relevance score
            - supporting text quality

        The result is bounded to [0, 1].
        """

        existing_confidence = self._safe_score(
            getattr(
                evidence,
                "confidence",
                0.0,
            )
        )

        relevance = self._safe_score(
            getattr(
                evidence,
                "relevance_score",
                0.0,
            )
        )

        supporting_text = str(
            getattr(
                evidence,
                "supporting_text",
                "",
            )
            or ""
        ).strip()

        if not supporting_text:
            content_quality = 0.0
        elif len(supporting_text) >= 500:
            content_quality = 1.0
        elif len(supporting_text) >= 200:
            content_quality = 0.8
        elif len(supporting_text) >= 100:
            content_quality = 0.6
        else:
            content_quality = 0.4

        score = (
            existing_confidence * 0.4
            + relevance * 0.4
            + content_quality * 0.2
        )

        return round(
            max(0.0, min(1.0, score)),
            4,
        )

    def detect_conflicts(
        self,
        evidence_items: Iterable[Evidence],
    ) -> list[Dict[str, str]]:
        """
        Detect obvious lexical conflicts.

        This is a deterministic heuristic, not a semantic contradiction
        detector. A future NLI/LLM component can replace this method.
        """

        items = list(evidence_items or [])
        conflicts: list[Dict[str, str]] = []

        for index, first in enumerate(items):
            for second in items[index + 1:]:
                if self.is_conflicting(
                    first,
                    second,
                ):
                    conflicts.append(
                        {
                            "evidence_a": str(
                                first.id
                            ),
                            "evidence_b": str(
                                second.id
                            ),
                            "reason": (
                                "Lexically conflicting claims"
                            ),
                        }
                    )

        return conflicts

    def is_conflicting(
        self,
        first: Evidence,
        second: Evidence,
    ) -> bool:
        """
        Detect simple directional conflicts.

        The implementation deliberately avoids ambiguous words such as
        "reduces", because "reduces latency" is positive while
        "reduces accuracy" may be negative.

        This method should not be treated as a true semantic contradiction
        classifier.
        """

        first_claim = self._normalize_claim(
            getattr(first, "claim", "")
        )

        second_claim = self._normalize_claim(
            getattr(second, "claim", "")
        )

        if not first_claim or not second_claim:
            return False

        first_positive = self._contains_any(
            first_claim,
            {
                "improves",
                "improved",
                "increase",
                "increases",
                "increased",
                "enhances",
                "enhanced",
                "outperforms",
                "better than",
            },
        )

        first_negative = self._contains_any(
            first_claim,
            {
                "decreases",
                "decreased",
                "decrease",
                "worse than",
                "fails to improve",
                "underperforms",
                "harms",
                "degrades",
            },
        )

        second_positive = self._contains_any(
            second_claim,
            {
                "improves",
                "improved",
                "increase",
                "increases",
                "increased",
                "enhances",
                "enhanced",
                "outperforms",
                "better than",
            },
        )

        second_negative = self._contains_any(
            second_claim,
            {
                "decreases",
                "decreased",
                "decrease",
                "worse than",
                "fails to improve",
                "underperforms",
                "harms",
                "degrades",
            },
        )

        return (
            (first_positive and second_negative)
            or
            (first_negative and second_positive)
        )

    def quality_key(
        self,
        evidence: Evidence,
    ) -> tuple[float, float]:
        """
        Sorting key for evidence quality.
        """

        return (
            self.calculate_confidence(evidence),
            self._safe_score(
                getattr(
                    evidence,
                    "relevance_score",
                    0.0,
                )
            ),
        )

    def _validate_item(
        self,
        evidence: Evidence,
    ) -> list[str]:
        errors: list[str] = []

        if evidence is None:
            return ["evidence is None"]

        evidence_id = getattr(
            evidence,
            "id",
            None,
        )

        claim = str(
            getattr(
                evidence,
                "claim",
                "",
            )
            or ""
        ).strip()

        supporting_text = str(
            getattr(
                evidence,
                "supporting_text",
                "",
            )
            or ""
        ).strip()

        source_id = getattr(
            evidence,
            "source_id",
            None,
        )

        confidence = self._safe_score(
            getattr(
                evidence,
                "confidence",
                0.0,
            )
        )

        relevance = self._safe_score(
            getattr(
                evidence,
                "relevance_score",
                0.0,
            )
        )

        if self.require_identifier and not evidence_id:
            errors.append(
                "missing evidence identifier"
            )

        if not claim:
            errors.append("empty claim")

        if len(claim) < self.min_content_length:
            errors.append(
                "claim below minimum length"
            )

        if not supporting_text:
            errors.append(
                "missing supporting text"
            )

        if self.require_source and not source_id:
            errors.append(
                "missing source identifier"
            )

        if confidence < self.min_confidence:
            errors.append(
                "confidence below threshold"
            )

        if relevance < self.min_relevance_score:
            errors.append(
                "relevance score below threshold"
            )

        return errors

    @staticmethod
    def validate_single(
        evidence: Evidence,
    ) -> bool:
        """
        Lightweight structural validation.
        """

        if evidence is None:
            return False

        if not getattr(evidence, "id", None):
            return False

        claim = str(
            getattr(
                evidence,
                "claim",
                "",
            )
            or ""
        ).strip()

        if not claim:
            return False

        source_id = getattr(
            evidence,
            "source_id",
            None,
        )

        if not source_id:
            return False

        return True

    @staticmethod
    def _normalize_claim(
        claim: object,
    ) -> str:
        if not isinstance(claim, str):
            return ""

        return " ".join(
            claim.lower().split()
        )

    @staticmethod
    def _contains_any(
        text: str,
        phrases: set[str],
    ) -> bool:
        return any(
            phrase in text
            for phrase in phrases
        )

    @staticmethod
    def _safe_score(
        value: object,
    ) -> float:
        try:
            score = float(value)

            if score != score:
                return 0.0

            if score == float("inf"):
                return 0.0

            if score == float("-inf"):
                return 0.0

            return max(
                0.0,
                min(1.0, score),
            )

        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _validate_threshold(
        value: float,
        name: str,
    ) -> float:
        try:
            threshold = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric"
            ) from exc

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                f"{name} must be between 0 and 1"
            )

        return threshold

