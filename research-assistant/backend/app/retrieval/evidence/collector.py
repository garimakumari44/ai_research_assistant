"""
Evidence collection.

The collector converts raw retrieval/reranking results into a normalized
evidence representation suitable for the RAG generation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .coverage import EvidenceCoverage, EvidenceCoverageCalculator
from .provenance import EvidenceProvenance, ProvenanceBuilder
from .scorer import EvidenceScore, EvidenceScorer


@dataclass(slots=True)
class EvidenceItem:
    """Normalized evidence item."""

    rank: int
    content: str

    score: EvidenceScore
    provenance: EvidenceProvenance

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "content": self.content,
            "score": self.score.to_dict(),
            "provenance": self.provenance.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class EvidenceCollection:
    """Complete evidence package returned by the collector."""

    query: str
    items: list[EvidenceItem]

    coverage: EvidenceCoverage

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "items": [
                item.to_dict()
                for item in self.items
            ],
            "coverage": self.coverage.to_dict(),
        }

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def has_evidence(self) -> bool:
        return bool(self.items)


class EvidenceCollector:
    """
    Collects and normalizes retrieval results.

    Responsibilities:

    1. Normalize result objects
    2. Extract evidence text
    3. Build provenance
    4. Score evidence
    5. Remove duplicates
    6. Calculate query coverage
    7. Return a deterministic evidence package
    """

    def __init__(
        self,
        *,
        scorer: EvidenceScorer | None = None,
        coverage_calculator: EvidenceCoverageCalculator | None = None,
        max_items: int = 10,
        min_score: float = 0.0,
    ) -> None:
        if max_items <= 0:
            raise ValueError("max_items must be greater than zero.")

        self.scorer = scorer or EvidenceScorer()

        self.coverage_calculator = (
            coverage_calculator
            or EvidenceCoverageCalculator(
                scorer=self.scorer,
            )
        )

        self.max_items = max_items
        self.min_score = max(0.0, min(1.0, min_score))

    def collect(
        self,
        query: str,
        results: Sequence[Any] | Iterable[Any],
    ) -> EvidenceCollection:
        """
        Collect evidence from retrieval/reranking results.
        """

        normalized: list[EvidenceItem] = []
        seen: set[str] = set()

        scored_results: list[tuple[Any, EvidenceScore]] = []

        for result in results:
            score = self.scorer.score(result)

            if score.score < self.min_score:
                continue

            scored_results.append((result, score))

        scored_results.sort(
            key=lambda item: item[1].score,
            reverse=True,
        )

        for result, score in scored_results:
            content = self._extract_text(result).strip()

            if not content:
                continue

            dedupe_key = self._dedupe_key(result, content)

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)

            provenance = ProvenanceBuilder.build(result)

            metadata = self._extract_metadata(result)

            normalized.append(
                EvidenceItem(
                    rank=len(normalized) + 1,
                    content=content,
                    score=score,
                    provenance=provenance,
                    metadata=metadata,
                )
            )

            if len(normalized) >= self.max_items:
                break

        coverage = self.coverage_calculator.calculate(
            query=query,
            evidence=normalized,
        )

        return EvidenceCollection(
            query=query,
            items=normalized,
            coverage=coverage,
        )

    def collect_top(
        self,
        query: str,
        results: Sequence[Any] | Iterable[Any],
        *,
        limit: int,
    ) -> EvidenceCollection:
        """
        Collect evidence with a per-request result limit.
        """

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        original_limit = self.max_items

        try:
            self.max_items = min(limit, original_limit)

            return self.collect(
                query=query,
                results=results,
            )
        finally:
            self.max_items = original_limit

    @staticmethod
    def _extract_text(result: Any) -> str:
        """Extract evidence text from a retrieval result."""

        for name in (
            "content",
            "context",
            "text",
            "chunk_text",
            "document_text",
        ):
            value = EvidenceCollector._get_value(result, name)

            if value:
                return str(value)

        return ""

    @staticmethod
    def _extract_metadata(result: Any) -> dict[str, Any]:
        """Extract non-core metadata."""

        value = EvidenceCollector._get_value(
            result,
            "metadata",
        )

        if isinstance(value, Mapping):
            return dict(value)

        return {}

    @staticmethod
    def _dedupe_key(
        result: Any,
        content: str,
    ) -> str:
        """
        Generate a stable deduplication key.

        Prefer chunk/document identifiers where available. Fall back to
        normalized content.
        """

        for name in (
            "chunk_id",
            "document_id",
            "paper_id",
        ):
            value = EvidenceCollector._get_value(
                result,
                name,
            )

            if value is not None:
                return f"{name}:{value}"

        normalized = " ".join(content.lower().split())

        return f"content:{normalized}"

    @staticmethod
    def _get_value(result: Any, name: str) -> Any:
        if isinstance(result, Mapping):
            return result.get(name)

        return getattr(result, name, None)