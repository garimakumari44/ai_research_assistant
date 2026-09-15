"""
Evidence quality scoring.

This module evaluates individual retrieval results using signals such as:

- Retrieval score
- Reranking score
- Text quality
- Metadata completeness
- Provenance completeness

The scorer does not depend on a specific vector database or reranker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .provenance import EvidenceProvenance, ProvenanceBuilder


@dataclass(slots=True)
class EvidenceScore:
    """Normalized evidence quality score."""

    score: float
    retrieval_score: float = 0.0
    rerank_score: float = 0.0
    text_quality: float = 0.0
    provenance_quality: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "score": self.score,
            "retrieval_score": self.retrieval_score,
            "rerank_score": self.rerank_score,
            "text_quality": self.text_quality,
            "provenance_quality": self.provenance_quality,
        }


class EvidenceScorer:
    """
    Scores individual evidence items.

    Scores are normalized to [0, 1].
    """

    def __init__(
        self,
        *,
        retrieval_weight: float = 0.30,
        rerank_weight: float = 0.35,
        text_weight: float = 0.20,
        provenance_weight: float = 0.15,
    ) -> None:
        total = (
            retrieval_weight
            + rerank_weight
            + text_weight
            + provenance_weight
        )

        if total <= 0:
            raise ValueError("Evidence score weights must sum to a positive value.")

        self.retrieval_weight = retrieval_weight / total
        self.rerank_weight = rerank_weight / total
        self.text_weight = text_weight / total
        self.provenance_weight = provenance_weight / total

    def score(self, result: Any) -> EvidenceScore:
        """
        Calculate the quality score for a retrieval result.
        """

        retrieval_score = self._extract_score(
            result,
            "retrieval_score",
            fallback_names=("score", "similarity"),
        )

        rerank_score = self._extract_score(
            result,
            "rerank_score",
            fallback_names=("reranker_score",),
        )

        text = self._extract_text(result)
        text_quality = self._text_quality(text)

        provenance = ProvenanceBuilder.build(result)
        provenance_quality = self._provenance_quality(provenance)

        final_score = (
            retrieval_score * self.retrieval_weight
            + rerank_score * self.rerank_weight
            + text_quality * self.text_weight
            + provenance_quality * self.provenance_weight
        )

        return EvidenceScore(
            score=_clamp(final_score),
            retrieval_score=retrieval_score,
            rerank_score=rerank_score,
            text_quality=text_quality,
            provenance_quality=provenance_quality,
        )

    def _extract_score(
        self,
        result: Any,
        primary: str,
        *,
        fallback_names: tuple[str, ...] = (),
    ) -> float:
        """Extract a numeric score from a result."""

        names = (primary, *fallback_names)

        for name in names:
            value = self._get_value(result, name)

            if value is None:
                continue

            try:
                return _normalize_score(float(value))
            except (TypeError, ValueError):
                continue

        return 0.0

    def _extract_text(self, result: Any) -> str:
        """Extract text/context from a retrieval result."""

        for name in (
            "content",
            "context",
            "text",
            "chunk_text",
            "document_text",
        ):
            value = self._get_value(result, name)

            if value:
                return str(value)

        return ""

    def _text_quality(self, text: str) -> float:
        """
        Estimate whether the evidence contains useful textual content.

        This is intentionally lightweight. Semantic relevance belongs to
        the retriever/reranker rather than this heuristic.
        """

        if not text:
            return 0.0

        length = len(text.strip())

        if length < 20:
            return 0.2

        if length < 100:
            return 0.5

        if length < 300:
            return 0.75

        return 1.0

    def _provenance_quality(
        self,
        provenance: EvidenceProvenance,
    ) -> float:
        """Estimate provenance completeness."""

        fields = (
            provenance.document_id,
            provenance.chunk_id,
            provenance.paper_id,
            provenance.source_uri,
            provenance.title,
            provenance.page_number,
            provenance.section,
        )

        present = sum(value is not None for value in fields)

        return min(present / 4.0, 1.0)

    @staticmethod
    def _get_value(result: Any, name: str) -> Any:
        """Read a value from either a mapping or an object."""

        if isinstance(result, Mapping):
            return result.get(name)

        return getattr(result, name, None)


def _normalize_score(value: float) -> float:
    """
    Normalize arbitrary retrieval scores into [0, 1].

    Most retrieval systems already return normalized scores. Values outside
    that range are clipped rather than transformed because score semantics
    differ across retrievers.
    """

    if value != value:
        return 0.0

    return _clamp(value)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))