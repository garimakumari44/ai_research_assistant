"""
Confidence policy for Adaptive RAG.

Combines multiple signals into a normalized confidence score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfidenceScore:
    score: float
    retrieval_score: float
    relevance_score: float
    coverage_score: float
    consistency_score: float
    groundedness_score: float


class ConfidencePolicy:
    """
    Computes a unified confidence score.

    The policy deliberately keeps confidence computation independent
    from the evaluator and controller.
    """

    def __init__(
        self,
        *,
        retrieval_weight: float = 0.20,
        relevance_weight: float = 0.25,
        coverage_weight: float = 0.20,
        consistency_weight: float = 0.15,
        groundedness_weight: float = 0.20,
    ) -> None:
        weights = (
            retrieval_weight,
            relevance_weight,
            coverage_weight,
            consistency_weight,
            groundedness_weight,
        )

        if any(weight < 0 for weight in weights):
            raise ValueError("Confidence weights cannot be negative.")

        total = sum(weights)

        if total <= 0:
            raise ValueError(
                "At least one confidence weight must be greater than zero."
            )

        self.retrieval_weight = retrieval_weight / total
        self.relevance_weight = relevance_weight / total
        self.coverage_weight = coverage_weight / total
        self.consistency_weight = consistency_weight / total
        self.groundedness_weight = groundedness_weight / total

    def calculate(
        self,
        *,
        retrieval_score: float = 0.0,
        relevance_score: float = 0.0,
        coverage_score: float = 0.0,
        consistency_score: float = 0.0,
        groundedness_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ConfidenceScore:
        """
        Calculate a weighted confidence score.
        """

        retrieval_score = self._clamp(retrieval_score)
        relevance_score = self._clamp(relevance_score)
        coverage_score = self._clamp(coverage_score)
        consistency_score = self._clamp(consistency_score)
        groundedness_score = self._clamp(groundedness_score)

        score = (
            retrieval_score * self.retrieval_weight
            + relevance_score * self.relevance_weight
            + coverage_score * self.coverage_weight
            + consistency_score * self.consistency_weight
            + groundedness_score * self.groundedness_weight
        )

        return ConfidenceScore(
            score=round(score, 4),
            retrieval_score=retrieval_score,
            relevance_score=relevance_score,
            coverage_score=coverage_score,
            consistency_score=consistency_score,
            groundedness_score=groundedness_score,
        )

    def is_confident(
        self,
        confidence: float,
        *,
        threshold: float = 0.80,
    ) -> bool:
        return self._clamp(confidence) >= threshold

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))