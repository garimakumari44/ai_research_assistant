from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.adaptive_rag.evaluation.confidence import calculate_confidence
from app.adaptive_rag.evaluation.coverage import calculate_coverage
from app.adaptive_rag.evaluation.diversity import calculate_diversity
from app.adaptive_rag.evaluation.quality import calculate_quality
from app.adaptive_rag.evaluation.relevance import calculate_relevance
from app.adaptive_rag.evaluation.sufficiency import calculate_sufficiency


@dataclass(frozen=True, slots=True)
class RetrievalEvaluation:
    """
    Complete evaluation of one retrieval attempt.

    This object is immutable so downstream Adaptive RAG components cannot
    accidentally mutate evaluation state.
    """

    sufficient: bool

    confidence: float
    relevance: float
    coverage: float
    diversity: float
    quality: float

    result_count: int

    best_score: float
    average_score: float
    score_spread: float

    reason: str

    should_rerank: bool
    should_retrieve_again: bool
    should_replan: bool

    diagnostics: dict[str, Any]


class AdaptiveRAGEvaluator:
    """
    Production evaluation component for Adaptive RAG.

    Responsibilities:

        retrieved evidence
             ↓
        relevance
             ↓
        confidence
             ↓
        coverage
             ↓
        diversity
             ↓
        quality
             ↓
        sufficiency
             ↓
        adaptive decision

    The evaluator does NOT:
        - call an LLM
        - perform retrieval
        - perform reranking
        - mutate AdaptiveRAGState
        - depend on a specific vector database
    """

    def __init__(
        self,
        *,
        minimum_results: int = 1,
        expected_evidence: int = 3,
        quality_threshold: float = 0.65,
        coverage_threshold: float = 0.55,
        confidence_threshold: float = 0.60,
        rerank_threshold: float = 0.60,
        replan_threshold: float = 0.35,
    ) -> None:
        self.minimum_results = max(1, minimum_results)
        self.expected_evidence = max(1, expected_evidence)

        self.quality_threshold = quality_threshold
        self.coverage_threshold = coverage_threshold
        self.confidence_threshold = confidence_threshold

        self.rerank_threshold = rerank_threshold
        self.replan_threshold = replan_threshold

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            result = float(value)

            if result != result:  # NaN
                return default

            if result in (float("inf"), float("-inf")):
                return default

            return result
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _content(chunk: Any) -> str:
        value = getattr(chunk, "content", "")

        if value is None:
            return ""

        return str(value)

    @staticmethod
    def _score(chunk: Any) -> float:
        return AdaptiveRAGEvaluator._safe_float(
            getattr(chunk, "score", 0.0)
        )

    def evaluate(
        self,
        query: str,
        chunks: Sequence[Any],
    ) -> RetrievalEvaluation:
        """
        Evaluate retrieved chunks for a query.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        if chunks is None:
            raise ValueError("chunks must not be None")

        result_count = len(chunks)

        if result_count == 0:
            return RetrievalEvaluation(
                sufficient=False,
                confidence=0.0,
                relevance=0.0,
                coverage=0.0,
                diversity=0.0,
                quality=0.0,
                result_count=0,
                best_score=0.0,
                average_score=0.0,
                score_spread=0.0,
                reason="no_retrieved_evidence",
                should_rerank=False,
                should_retrieve_again=True,
                should_replan=True,
                diagnostics={
                    "query_length": len(query),
                    "result_count": 0,
                },
            )

        contents = [
            self._content(chunk)
            for chunk in chunks
        ]

        scores = [
            self._score(chunk)
            for chunk in chunks
        ]

        relevance_results = [
            calculate_relevance(query, content)
            for content in contents
        ]

        relevance_score = (
            sum(result.score for result in relevance_results)
            / len(relevance_results)
        )

        confidence_result = calculate_confidence(
            scores,
            expected_evidence=self.expected_evidence,
        )

        coverage_result = calculate_coverage(
            query,
            contents,
        )

        diversity_result = calculate_diversity(
            contents,
        )

        quality_result = calculate_quality(
            relevance=relevance_score,
            confidence=confidence_result.confidence,
            coverage=coverage_result.score,
            diversity=diversity_result.score,
        )

        sufficiency_result = calculate_sufficiency(
            quality_score=quality_result.score,
            coverage_score=coverage_result.score,
            confidence_score=confidence_result.confidence,
            result_count=result_count,
            minimum_results=self.minimum_results,
            quality_threshold=self.quality_threshold,
            coverage_threshold=self.coverage_threshold,
            confidence_threshold=self.confidence_threshold,
        )

        best_score = max(scores) if scores else 0.0

        average_score = (
            sum(scores) / len(scores)
            if scores
            else 0.0
        )

        score_spread = (
            max(scores) - min(scores)
            if scores
            else 0.0
        )

        should_rerank = (
            not sufficiency_result.sufficient
            and quality_result.score >= self.rerank_threshold
        )

        should_retrieve_again = not sufficiency_result.sufficient

        should_replan = (
            quality_result.score < self.replan_threshold
            or coverage_result.score < self.coverage_threshold * 0.5
            or result_count == 0
        )

        return RetrievalEvaluation(
            sufficient=sufficiency_result.sufficient,
            confidence=confidence_result.confidence,
            relevance=quality_result.relevance,
            coverage=quality_result.coverage,
            diversity=quality_result.diversity,
            quality=quality_result.score,
            result_count=result_count,
            best_score=round(best_score, 6),
            average_score=round(average_score, 6),
            score_spread=round(score_spread, 6),
            reason=sufficiency_result.reason,
            should_rerank=should_rerank,
            should_retrieve_again=should_retrieve_again,
            should_replan=should_replan,
            diagnostics={
                "confidence": {
                    "score_strength": confidence_result.score_strength,
                    "score_consistency": confidence_result.score_consistency,
                    "evidence_density": confidence_result.evidence_density,
                },
                "coverage": {
                    "covered_terms": coverage_result.covered_terms,
                    "total_terms": coverage_result.total_terms,
                },
                "diversity": {
                    "unique_documents": diversity_result.unique_documents,
                    "duplicate_ratio": diversity_result.duplicate_ratio,
                },
                "sufficiency": {
                    "score": sufficiency_result.score,
                    "reason": sufficiency_result.reason,
                },
                "query_length": len(query),
                "result_count": result_count,
            },
        )