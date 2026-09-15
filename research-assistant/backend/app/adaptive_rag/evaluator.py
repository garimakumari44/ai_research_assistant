"""
Adaptive RAG evaluator.

Evaluates retrieval quality and determines whether the current
retrieval result is sufficient for answer generation.

The evaluator does NOT:
- perform retrieval
- generate answers
- modify the database
- call an LLM directly

It only evaluates the current Adaptive RAG state.
"""

from __future__ import annotations

from statistics import mean

from pydantic import BaseModel, Field

from .exceptions import AdaptiveRAGEvaluationError
from .state import AdaptiveRAGState, RetrievedChunk


class RetrievalEvaluation(BaseModel):
    """
    Result of evaluating retrieved context.
    """

    sufficient: bool = False

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    chunk_count: int = 0

    best_score: float = 0.0

    average_score: float = 0.0

    score_spread: float = 0.0

    needs_reranking: bool = False

    needs_retrieval: bool = True

    needs_replanning: bool = False

    reasoning: str = ""


class AdaptiveRAGEvaluator:
    """
    Evaluates retrieval quality for Adaptive RAG.
    """

    def __init__(
        self,
        *,
        minimum_score: float = 0.3,
        strong_score: float = 0.7,
        minimum_chunks: int = 2,
    ) -> None:
        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError(
                "minimum_score must be between 0 and 1."
            )

        if not 0.0 <= strong_score <= 1.0:
            raise ValueError(
                "strong_score must be between 0 and 1."
            )

        if minimum_chunks < 1:
            raise ValueError(
                "minimum_chunks must be at least 1."
            )

        self.minimum_score = minimum_score
        self.strong_score = strong_score
        self.minimum_chunks = minimum_chunks

    def evaluate(
        self,
        state: AdaptiveRAGState,
    ) -> RetrievalEvaluation:
        """
        Evaluate the current retrieval state.
        """

        try:
            chunks = state.retrieved_chunks

            if not chunks:
                return RetrievalEvaluation(
                    sufficient=False,
                    confidence=0.0,
                    chunk_count=0,
                    best_score=0.0,
                    average_score=0.0,
                    score_spread=0.0,
                    needs_reranking=False,
                    needs_retrieval=True,
                    needs_replanning=True,
                    reasoning=(
                        "No chunks were retrieved. "
                        "Another retrieval attempt is required."
                    ),
                )

            scores = self._extract_scores(chunks)

            best_score = max(scores)
            average_score = mean(scores)
            score_spread = max(scores) - min(scores)

            sufficient = self._is_sufficient(
                chunks=chunks,
                best_score=best_score,
                average_score=average_score,
            )

            needs_reranking = self._needs_reranking(
                chunks=chunks,
                best_score=best_score,
                average_score=average_score,
            )

            needs_replanning = (
                not sufficient
                and not needs_reranking
            )

            confidence = self._calculate_confidence(
                best_score=best_score,
                average_score=average_score,
                chunk_count=len(chunks),
            )

            reasoning = self._build_reasoning(
                sufficient=sufficient,
                needs_reranking=needs_reranking,
                needs_replanning=needs_replanning,
                chunk_count=len(chunks),
                best_score=best_score,
                average_score=average_score,
            )

            return RetrievalEvaluation(
                sufficient=sufficient,
                confidence=confidence,
                chunk_count=len(chunks),
                best_score=best_score,
                average_score=average_score,
                score_spread=score_spread,
                needs_reranking=needs_reranking,
                needs_retrieval=not sufficient,
                needs_replanning=needs_replanning,
                reasoning=reasoning,
            )

        except Exception as exc:
            if isinstance(
                exc,
                AdaptiveRAGEvaluationError,
            ):
                raise

            raise AdaptiveRAGEvaluationError(
                f"Failed to evaluate retrieval results: {exc}"
            ) from exc

    def evaluate_chunks(
        self,
        chunks: list[RetrievedChunk],
    ) -> RetrievalEvaluation:
        """
        Evaluate a chunk list without requiring a complete state.
        """

        temporary_state = AdaptiveRAGState(
            query="evaluation",
            retrieved_chunks=chunks,
        )

        return self.evaluate(temporary_state)

    def is_sufficient(
        self,
        state: AdaptiveRAGState,
    ) -> bool:
        """
        Convenience method for checking context sufficiency.
        """

        return self.evaluate(state).sufficient

    def _is_sufficient(
        self,
        *,
        chunks: list[RetrievedChunk],
        best_score: float,
        average_score: float,
    ) -> bool:
        """
        Determine whether retrieved context is good enough.
        """

        if not chunks:
            return False

        if best_score < self.minimum_score:
            return False

        if len(chunks) < self.minimum_chunks:
            return best_score >= self.strong_score

        return (
            best_score >= self.minimum_score
            and average_score >= self.minimum_score
        )

    def _needs_reranking(
        self,
        *,
        chunks: list[RetrievedChunk],
        best_score: float,
        average_score: float,
    ) -> bool:
        """
        Determine whether reranking could improve context quality.
        """

        if len(chunks) < 3:
            return False

        if best_score >= self.strong_score:
            return False

        return (
            average_score >= self.minimum_score
            and best_score > average_score
        )

    @staticmethod
    def _extract_scores(
        chunks: list[RetrievedChunk],
    ) -> list[float]:
        """
        Extract and sanitize retrieval scores.
        """

        scores: list[float] = []

        for chunk in chunks:
            score = float(chunk.score)

            score = max(
                0.0,
                min(1.0, score),
            )

            scores.append(score)

        return scores

    @staticmethod
    def _calculate_confidence(
        *,
        best_score: float,
        average_score: float,
        chunk_count: int,
    ) -> float:
        """
        Calculate an overall retrieval confidence.

        Best score receives more weight than average score.
        """

        score_confidence = (
            (best_score * 0.6)
            + (average_score * 0.4)
        )

        quantity_bonus = min(
            0.1,
            chunk_count / 100,
        )

        return min(
            1.0,
            score_confidence + quantity_bonus,
        )

    @staticmethod
    def _build_reasoning(
        *,
        sufficient: bool,
        needs_reranking: bool,
        needs_replanning: bool,
        chunk_count: int,
        best_score: float,
        average_score: float,
    ) -> str:

        if sufficient:
            return (
                f"Retrieved {chunk_count} chunks with "
                f"best score {best_score:.3f} and "
                f"average score {average_score:.3f}. "
                "Context is sufficient for generation."
            )

        if needs_reranking:
            return (
                f"Retrieved {chunk_count} chunks with "
                f"best score {best_score:.3f} and "
                f"average score {average_score:.3f}. "
                "Context may benefit from reranking."
            )

        if needs_replanning:
            return (
                f"Retrieved {chunk_count} chunks but retrieval "
                f"quality is insufficient "
                f"(best={best_score:.3f}, "
                f"average={average_score:.3f}). "
                "A new retrieval strategy is recommended."
            )

        return "Retrieval evaluation completed."