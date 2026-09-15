from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from app.adaptive_rag.routing.route_scoring import (
    RouteDecision,
    RouteFeatures,
    RouteScorer,
)


class RetrievalStrategy(str, Enum):
    """Concrete retrieval strategies."""

    DIRECT = "direct"
    HYBRID = "hybrid"
    MULTI_QUERY = "multi_query"
    ITERATIVE = "iterative"
    CORRECTIVE = "corrective"


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """
    Context supplied to the strategy selector.

    This class is intentionally independent from a specific pipeline state
    implementation so it can be adapted to the rest of the application.
    """

    query: str
    features: RouteFeatures

    available_strategies: Sequence[RetrievalStrategy] = field(
        default_factory=lambda: tuple(RetrievalStrategy)
    )

    previous_attempts: int = 0
    previous_evidence_score: float = 0.0
    previous_coverage_score: float = 0.0
    previous_contradiction_score: float = 0.0

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.query or not self.query.strip():
            raise ValueError("query cannot be empty")

        if self.previous_attempts < 0:
            raise ValueError("previous_attempts cannot be negative")

        for name in (
            "previous_evidence_score",
            "previous_coverage_score",
            "previous_contradiction_score",
        ):
            value = getattr(self, name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1"
                )


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    """Final strategy selection."""

    strategy: RetrievalStrategy
    confidence: float
    route_score: float
    rationale: str
    alternatives: tuple[RetrievalStrategy, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.route_score <= 1.0:
            raise ValueError("route_score must be between 0 and 1")


class StrategySelector:
    """
    Converts high-level route scores into concrete retrieval strategies.
    """

    ROUTE_TO_STRATEGY = {
        RouteDecision.DIRECT: RetrievalStrategy.DIRECT,
        RouteDecision.MULTI_QUERY: RetrievalStrategy.MULTI_QUERY,
        RouteDecision.ITERATIVE: RetrievalStrategy.ITERATIVE,
        RouteDecision.CORRECTIVE: RetrievalStrategy.CORRECTIVE,
        RouteDecision.HYBRID: RetrievalStrategy.HYBRID,
    }

    def __init__(
        self,
        scorer: Optional[RouteScorer] = None,
        confidence_margin: float = 0.08,
    ) -> None:
        self.scorer = scorer or RouteScorer()
        self.confidence_margin = confidence_margin

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _apply_context_adjustments(
        self,
        scores: list,
        context: StrategyContext,
    ) -> list:
        """
        Adjust routing based on previous retrieval attempts.

        This prevents the system from repeatedly selecting the same
        ineffective strategy.
        """

        adjusted = []

        for item in scores:
            score = item.score

            strategy = self.ROUTE_TO_STRATEGY.get(item.route)

            if strategy is None:
                continue

            # If previous retrieval failed, increase corrective/iterative
            # strategies.
            if context.previous_attempts > 0:
                if (
                    strategy == RetrievalStrategy.CORRECTIVE
                    and context.previous_evidence_score < 0.5
                ):
                    score += 0.15

                if (
                    strategy == RetrievalStrategy.ITERATIVE
                    and context.previous_coverage_score < 0.5
                ):
                    score += 0.10

                # Penalize direct retrieval after repeated failure.
                if (
                    strategy == RetrievalStrategy.DIRECT
                    and context.previous_attempts >= 2
                ):
                    score -= 0.15

            # High contradiction strongly favors corrective retrieval.
            if (
                context.previous_contradiction_score > 0.6
                and strategy == RetrievalStrategy.CORRECTIVE
            ):
                score += 0.15

            adjusted.append(
                item.__class__(
                    route=item.route,
                    score=self._clamp(score),
                    rationale=item.rationale,
                )
            )

        return sorted(
            adjusted,
            key=lambda item: item.score,
            reverse=True,
        )

    def select(
        self,
        context: StrategyContext,
    ) -> StrategyDecision:
        """Select the best available retrieval strategy."""

        route_candidates = [
            self._strategy_to_route(strategy)
            for strategy in context.available_strategies
        ]

        route_candidates = [
            route
            for route in route_candidates
            if route is not None
        ]

        if not route_candidates:
            raise RuntimeError(
                "No supported retrieval strategies are available."
            )

        ranked = self.scorer.rank(
            context.features,
            route_candidates,
        )

        ranked = self._apply_context_adjustments(
            ranked,
            context,
        )

        if not ranked:
            raise RuntimeError(
                "Unable to select a retrieval strategy."
            )

        winner = ranked[0]

        winner_strategy = self.ROUTE_TO_STRATEGY[winner.route]

        alternatives = tuple(
            self.ROUTE_TO_STRATEGY[item.route]
            for item in ranked[1:4]
        )

        if len(ranked) > 1:
            margin = max(
                0.0,
                winner.score - ranked[1].score,
            )
        else:
            margin = winner.score

        confidence = self._clamp(
            0.65 * winner.score
            + 0.35 * min(1.0, margin / max(self.confidence_margin, 0.001))
        )

        return StrategyDecision(
            strategy=winner_strategy,
            confidence=confidence,
            route_score=winner.score,
            rationale=winner.rationale,
            alternatives=alternatives,
        )

    @staticmethod
    def _strategy_to_route(
        strategy: RetrievalStrategy,
    ) -> Optional[RouteDecision]:
        mapping = {
            RetrievalStrategy.DIRECT: RouteDecision.DIRECT,
            RetrievalStrategy.MULTI_QUERY: RouteDecision.MULTI_QUERY,
            RetrievalStrategy.ITERATIVE: RouteDecision.ITERATIVE,
            RetrievalStrategy.CORRECTIVE: RouteDecision.CORRECTIVE,
            RetrievalStrategy.HYBRID: RouteDecision.HYBRID,
        }

        return mapping.get(strategy)