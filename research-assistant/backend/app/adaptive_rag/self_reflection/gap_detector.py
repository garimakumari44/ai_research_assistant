
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Iterable, Mapping, Sequence


class GapSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Gap:
    """
    Represents an information gap discovered during reflection.
    """

    description: str
    severity: GapSeverity
    category: str = "missing_information"
    query_hint: str | None = None
    required_for_answer: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GapDetectionResult:
    """
    Result returned by GapDetector.
    """

    has_gaps: bool
    gaps: tuple[Gap, ...]
    coverage_score: float
    reasoning: tuple[str, ...] = ()

    @property
    def critical(self) -> bool:
        return any(
            gap.severity in {GapSeverity.HIGH, GapSeverity.CRITICAL}
            for gap in self.gaps
        )


class GapDetector:
    """
    Detects missing information between a user query and retrieved evidence.

    This component intentionally does not call an LLM. It provides a
    deterministic first-pass assessment that can be combined with a semantic
    evaluator or LLM-based critic upstream.

    Parameters
    ----------
    min_evidence_items:
        Minimum number of evidence items normally expected.

    min_coverage_score:
        Minimum estimated coverage required before the answer can be considered
        sufficiently supported.

    min_relevance_score:
        Minimum relevance score for an evidence item to count toward coverage.
    """

    _QUESTION_PATTERNS = (
        r"\bwho\b",
        r"\bwhat\b",
        r"\bwhen\b",
        r"\bwhere\b",
        r"\bwhy\b",
        r"\bhow\b",
        r"\bwhich\b",
        r"\bcompare\b",
        r"\bexplain\b",
        r"\blist\b",
        r"\bsummarize\b",
        r"\bdescribe\b",
        r"\banalyze\b",
        r"\bevaluate\b",
    )

    def __init__(
        self,
        *,
        min_evidence_items: int = 1,
        min_coverage_score: float = 0.55,
        min_relevance_score: float = 0.30,
    ) -> None:
        if min_evidence_items < 0:
            raise ValueError("min_evidence_items must be >= 0")

        if not 0.0 <= min_coverage_score <= 1.0:
            raise ValueError("min_coverage_score must be between 0 and 1")

        if not 0.0 <= min_relevance_score <= 1.0:
            raise ValueError("min_relevance_score must be between 0 and 1")

        self.min_evidence_items = min_evidence_items
        self.min_coverage_score = min_coverage_score
        self.min_relevance_score = min_relevance_score

    def detect(
        self,
        query: str,
        evidence: Sequence[Any] | None,
    ) -> GapDetectionResult:
        """
        Detect information gaps.

        Evidence objects may be dictionaries, dataclasses, or arbitrary
        objects exposing common attributes such as:

            content
            text
            score
            relevance_score
            metadata
        """

        normalized_query = self._normalize_text(query)

        if not normalized_query:
            return GapDetectionResult(
                has_gaps=True,
                gaps=(
                    Gap(
                        description="The query is empty or invalid.",
                        severity=GapSeverity.CRITICAL,
                        category="invalid_query",
                        required_for_answer=True,
                    ),
                ),
                coverage_score=0.0,
                reasoning=("No usable query was provided.",),
            )

        items = list(evidence or [])

        if len(items) < self.min_evidence_items:
            return GapDetectionResult(
                has_gaps=True,
                gaps=(
                    Gap(
                        description=(
                            "Insufficient evidence was retrieved to support "
                            "a reliable answer."
                        ),
                        severity=GapSeverity.HIGH,
                        category="insufficient_evidence",
                        query_hint=query,
                    ),
                ),
                coverage_score=0.0,
                reasoning=(
                    f"Retrieved {len(items)} evidence item(s).",
                    f"Required minimum: {self.min_evidence_items}.",
                ),
            )

        usable_items = [
            item
            for item in items
            if self._extract_relevance(item) >= self.min_relevance_score
            and bool(self._extract_content(item))
        ]

        if not usable_items:
            return GapDetectionResult(
                has_gaps=True,
                gaps=(
                    Gap(
                        description=(
                            "Retrieved evidence contains no sufficiently "
                            "relevant usable content."
                        ),
                        severity=GapSeverity.HIGH,
                        category="low_relevance",
                        query_hint=query,
                    ),
                ),
                coverage_score=0.0,
                reasoning=(
                    "All retrieved items were below the relevance threshold "
                    "or contained no usable text.",
                ),
            )

        query_terms = self._important_terms(normalized_query)

        if not query_terms:
            coverage = min(1.0, len(usable_items) / 3.0)
        else:
            covered_terms = set()

            for item in usable_items:
                content = self._normalize_text(self._extract_content(item))
                covered_terms.update(
                    term
                    for term in query_terms
                    if term in content
                )

            coverage = len(covered_terms) / len(query_terms)

        gaps: list[Gap] = []
        reasoning: list[str] = [
            f"Usable evidence items: {len(usable_items)}.",
            f"Estimated lexical coverage: {coverage:.3f}.",
        ]

        if coverage < self.min_coverage_score:
            missing_terms = [
                term
                for term in query_terms
                if not any(
                    term in self._normalize_text(self._extract_content(item))
                    for item in usable_items
                )
            ]

            hint = " ".join(missing_terms[:8]) or query

            severity = (
                GapSeverity.CRITICAL
                if coverage < 0.20
                else GapSeverity.HIGH
                if coverage < 0.35
                else GapSeverity.MEDIUM
            )

            gaps.append(
                Gap(
                    description=(
                        "Retrieved evidence does not adequately cover the "
                        "information requested by the query."
                    ),
                    severity=severity,
                    category="coverage",
                    query_hint=hint,
                    metadata={
                        "missing_terms": missing_terms,
                        "coverage_score": coverage,
                    },
                )
            )

        return GapDetectionResult(
            has_gaps=bool(gaps),
            gaps=tuple(gaps),
            coverage_score=max(0.0, min(1.0, coverage)),
            reasoning=tuple(reasoning),
        )

    def _important_terms(self, query: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z0-9][a-zA-Z0-9_-]{2,}\b", query)

        stop_words = {
            "what",
            "when",
            "where",
            "which",
            "with",
            "from",
            "that",
            "this",
            "have",
            "does",
            "about",
            "into",
            "than",
            "then",
            "they",
            "them",
            "their",
            "there",
            "here",
            "also",
            "would",
            "could",
            "should",
            "explain",
            "describe",
            "please",
        }

        return {
            word.lower()
            for word in words
            if word.lower() not in stop_words
        }

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value).strip().lower(),
        )

    @staticmethod
    def _extract_content(item: Any) -> str:
        if item is None:
            return ""

        if isinstance(item, Mapping):
            for key in ("content", "text", "chunk", "page_content", "document"):
                value = item.get(key)
                if value:
                    return str(value)

            return ""

        for attr in (
            "content",
            "text",
            "chunk",
            "page_content",
            "document",
        ):
            value = getattr(item, attr, None)
            if value:
                return str(value)

        return ""

    @staticmethod
    def _extract_relevance(item: Any) -> float:
        if isinstance(item, Mapping):
            for key in (
                "relevance_score",
                "relevance",
                "score",
                "similarity",
            ):
                value = item.get(key)
                if isinstance(value, (int, float)):
                    return max(0.0, min(1.0, float(value)))

        for attr in (
            "relevance_score",
            "relevance",
            "score",
            "similarity",
        ):
            value = getattr(item, attr, None)
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, float(value)))

        # Unknown score should not automatically invalidate evidence.
        return 1.0

