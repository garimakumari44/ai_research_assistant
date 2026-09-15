from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from app.adaptive_rag.routing.route_scoring import (
    RouteFeatures,
    RouteScore,
    RouteScorer,
)
from app.adaptive_rag.routing.source_selector import (
    SourceSelection,
    SourceSelectionContext,
    SourceSelector,
    SourceType,
)
from app.adaptive_rag.routing.strategy_selector import (
    RetrievalStrategy,
    StrategyContext,
    StrategyDecision,
    StrategySelector,
)


@dataclass(frozen=True, slots=True)
class RoutingRequest:
    """
    Input to the Adaptive RAG router.

    Features should normally be produced by the planner/query analyzer,
    rather than manually populated by callers.
    """

    query: str
    features: RouteFeatures

    source_context: SourceSelectionContext = field(
        default_factory=SourceSelectionContext
    )

    available_strategies: Sequence[RetrievalStrategy] = field(
        default_factory=lambda: tuple(RetrievalStrategy)
    )

    previous_attempts: int = 0
    previous_evidence_score: float = 0.0
    previous_coverage_score: float = 0.0
    previous_contradiction_score: float = 0.0

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.query or not self.query.strip():
            raise ValueError("query cannot be empty")

        if self.previous_attempts < 0:
            raise ValueError(
                "previous_attempts cannot be negative"
            )


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """
    Complete Adaptive RAG routing decision.
    """

    strategy: RetrievalStrategy
    strategy_confidence: float

    sources: tuple[SourceType, ...]
    source_scores: Mapping[SourceType, float]

    route: str
    route_score: float

    rationale: str

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


class AdaptiveRouter:
    """
    Central routing component for Adaptive RAG.

    Responsibilities:

        query features
              ↓
        route scoring
              ↓
        strategy selection
              ↓
        source selection
              ↓
        RoutingDecision

    It does NOT perform retrieval, generation, evidence evaluation,
    planning, or answer generation.
    """

    def __init__(
        self,
        route_scorer: Optional[RouteScorer] = None,
        strategy_selector: Optional[StrategySelector] = None,
        source_selector: Optional[SourceSelector] = None,
    ) -> None:
        self.route_scorer = (
            route_scorer
            or RouteScorer()
        )

        self.strategy_selector = (
            strategy_selector
            or StrategySelector(
                scorer=self.route_scorer
            )
        )

        self.source_selector = (
            source_selector
            or SourceSelector()
        )

    def route(
        self,
        request: RoutingRequest,
    ) -> RoutingDecision:
        """
        Produce an Adaptive RAG routing decision.
        """

        strategy_context = StrategyContext(
            query=request.query,
            features=request.features,
            available_strategies=request.available_strategies,
            previous_attempts=request.previous_attempts,
            previous_evidence_score=request.previous_evidence_score,
            previous_coverage_score=request.previous_coverage_score,
            previous_contradiction_score=(
                request.previous_contradiction_score
            ),
            metadata=request.metadata,
        )

        strategy_decision = self.strategy_selector.select(
            strategy_context
        )

        source_selection = self.source_selector.select(
            request.source_context
        )

        return self._build_decision(
            request=request,
            strategy_decision=strategy_decision,
            source_selection=source_selection,
        )

    def _build_decision(
        self,
        request: RoutingRequest,
        strategy_decision: StrategyDecision,
        source_selection: SourceSelection,
    ) -> RoutingDecision:
        """Build immutable routing result."""

        route = strategy_decision.strategy.value

        rationale = (
            f"Strategy={strategy_decision.strategy.value}; "
            f"confidence={strategy_decision.confidence:.3f}; "
            f"route_score={strategy_decision.route_score:.3f}. "
            f"{strategy_decision.rationale} "
            f"{source_selection.rationale}"
        )

        return RoutingDecision(
            strategy=strategy_decision.strategy,
            strategy_confidence=strategy_decision.confidence,
            sources=source_selection.sources,
            source_scores=source_selection.scores,
            route=route,
            route_score=strategy_decision.route_score,
            rationale=rationale,
            metadata={
                **dict(request.metadata),
                "alternatives": [
                    strategy.value
                    for strategy in strategy_decision.alternatives
                ],
            },
        )

    def score_routes(
        self,
        features: RouteFeatures,
    ) -> list[RouteScore]:
        """
        Expose route scoring for diagnostics and observability.
        """

        return self.route_scorer.rank(features)

    def select_sources(
        self,
        context: SourceSelectionContext,
    ) -> SourceSelection:
        """Expose source selection independently."""

        return self.source_selector.select(context)

    def select_strategy(
        self,
        query: str,
        features: RouteFeatures,
        available_strategies: Optional[
            Sequence[RetrievalStrategy]
        ] = None,
        previous_attempts: int = 0,
        previous_evidence_score: float = 0.0,
        previous_coverage_score: float = 0.0,
        previous_contradiction_score: float = 0.0,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> StrategyDecision:
        """Expose strategy selection independently."""

        context = StrategyContext(
            query=query,
            features=features,
            available_strategies=(
                available_strategies
                or tuple(RetrievalStrategy)
            ),
            previous_attempts=previous_attempts,
            previous_evidence_score=previous_evidence_score,
            previous_coverage_score=previous_coverage_score,
            previous_contradiction_score=(
                previous_contradiction_score
            ),
            metadata=metadata or {},
        )

        return self.strategy_selector.select(context)