
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RetrievalCheckResult:
    """
    Structured retrieval quality assessment.
    """

    sufficient: bool
    relevance_score: float
    diversity_score: float
    evidence_count: int
    usable_evidence_count: int
    reasons: tuple[str, ...] = ()
    recommended_queries: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


class RetrievalChecker:
    """
    Evaluates whether retrieved evidence is adequate for downstream answering.

    This is deliberately independent from a particular vector database or
    retriever implementation.
    """

    def __init__(
        self,
        *,
        min_items: int = 1,
        min_relevance: float = 0.45,
        min_diversity: float = 0.20,
        max_duplicate_ratio: float = 0.70,
    ) -> None:
        if min_items < 0:
            raise ValueError("min_items must be >= 0")

        for name, value in {
            "min_relevance": min_relevance,
            "min_diversity": min_diversity,
            "max_duplicate_ratio": max_duplicate_ratio,
        }.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        self.min_items = min_items
        self.min_relevance = min_relevance
        self.min_diversity = min_diversity
        self.max_duplicate_ratio = max_duplicate_ratio

    def check(
        self,
        query: str,
        evidence: Sequence[Any] | None,
    ) -> RetrievalCheckResult:
        items = list(evidence or [])

        if not items:
            return RetrievalCheckResult(
                sufficient=False,
                relevance_score=0.0,
                diversity_score=0.0,
                evidence_count=0,
                usable_evidence_count=0,
                reasons=("No evidence was retrieved.",),
                recommended_queries=(query.strip(),) if query.strip() else (),
            )

        relevance_scores = [
            self._score(item)
            for item in items
        ]

        usable_scores = [
            score
            for score in relevance_scores
            if score >= self.min_relevance
        ]

        relevance = (
            sum(relevance_scores) / len(relevance_scores)
            if relevance_scores
            else 0.0
        )

        diversity = self._diversity(items)

        duplicate_ratio = 1.0 - diversity

        reasons: list[str] = []
        recommendations: list[str] = []

        if len(items) < self.min_items:
            reasons.append(
                f"Only {len(items)} evidence item(s) were retrieved; "
                f"minimum is {self.min_items}."
            )
            recommendations.append(query.strip())

        if relevance < self.min_relevance:
            reasons.append(
                f"Average relevance {relevance:.3f} is below "
                f"threshold {self.min_relevance:.3f}."
            )
            recommendations.append(query.strip())

        if diversity < self.min_diversity:
            reasons.append(
                f"Evidence diversity {diversity:.3f} is below "
                f"threshold {self.min_diversity:.3f}."
            )

        if duplicate_ratio > self.max_duplicate_ratio:
            reasons.append(
                "Retrieved evidence contains excessive duplication."
            )

        sufficient = (
            len(items) >= self.min_items
            and relevance >= self.min_relevance
            and diversity >= self.min_diversity
            and bool(usable_scores)
        )

        if sufficient:
            reasons.append("Retrieved evidence passes the configured checks.")

        return RetrievalCheckResult(
            sufficient=sufficient,
            relevance_score=max(0.0, min(1.0, relevance)),
            diversity_score=max(0.0, min(1.0, diversity)),
            evidence_count=len(items),
            usable_evidence_count=len(usable_scores),
            reasons=tuple(reasons),
            recommended_queries=tuple(
                dict.fromkeys(
                    recommendation
                    for recommendation in recommendations
                    if recommendation
                )
            ),
            metadata={
                "duplicate_ratio": duplicate_ratio,
            },
        )

    def _score(self, item: Any) -> float:
        value = self._get(item, (
            "relevance_score",
            "relevance",
            "score",
            "similarity",
        ))

        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))

        return 1.0

    def _diversity(self, items: Sequence[Any]) -> float:
        if len(items) <= 1:
            return 1.0

        signatures: set[str] = set()

        for item in items:
            content = self._content(item)

            if not content:
                signatures.add(f"empty:{id(item)}")
                continue

            words = content.lower().split()
            signature = " ".join(words[:50])
            signatures.add(signature)

        return len(signatures) / len(items)

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

    @staticmethod
    def _get(
        item: Any,
        keys: tuple[str, ...],
    ) -> Any:
        if isinstance(item, Mapping):
            for key in keys:
                if key in item:
                    return item[key]

        for key in keys:
            value = getattr(item, key, None)
            if value is not None:
                return value

        return None

