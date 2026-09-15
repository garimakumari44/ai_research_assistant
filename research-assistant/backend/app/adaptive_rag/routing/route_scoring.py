from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional


class RouteDecision(str, Enum):
    """High-level retrieval route."""

    DIRECT = "direct"
    MULTI_QUERY = "multi_query"
    ITERATIVE = "iterative"
    CORRECTIVE = "corrective"
    HYBRID = "hybrid"
    NO_RETRIEVAL = "no_retrieval"


@dataclass(frozen=True, slots=True)
class RouteFeatures:
    """
    Normalized features used to score candidate retrieval routes.

    All numeric values are expected to be in [0, 1].
    """

    query_complexity: float = 0.0
    ambiguity: float = 0.0
    expected_information_need: float = 0.0
    freshness_requirement: float = 0.0
    domain_specificity: float = 0.0
    multi_hop_requirement: float = 0.0
    contradiction_risk: float = 0.0
    source_diversity_need: float = 0.0
    latency_sensitivity: float = 0.0
    token_budget: float = 1.0

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{field_name} must be between 0 and 1, got {value}"
                )


@dataclass(frozen=True, slots=True)
class RouteScore:
    """Score assigned to one routing candidate."""

    route: RouteDecision
    score: float
    rationale: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"score must be between 0 and 1, got {self.score}"
            )


class RouteScorer:
    """
    Scores retrieval routes from query-level features.

    The scorer deliberately contains no LLM calls and no retrieval logic.
    This makes routing cheap, testable and deterministic.
    """

    DEFAULT_WEIGHTS: Mapping[str, Mapping[str, float]] = {
        RouteDecision.DIRECT.value: {
            "simplicity": 0.40,
            "latency": 0.30,
            "information_need": 0.20,
            "ambiguity_penalty": 0.10,
        },
        RouteDecision.MULTI_QUERY.value: {
            "complexity": 0.25,
            "ambiguity": 0.30,
            "diversity": 0.25,
            "information_need": 0.20,
        },
        RouteDecision.ITERATIVE.value: {
            "complexity": 0.30,
            "multi_hop": 0.30,
            "information_need": 0.20,
            "contradiction": 0.10,
            "domain_specificity": 0.10,
        },
        RouteDecision.CORRECTIVE.value: {
            "contradiction": 0.35,
            "ambiguity": 0.20,
            "information_need": 0.20,
            "domain_specificity": 0.15,
            "diversity": 0.10,
        },
        RouteDecision.HYBRID.value: {
            "complexity": 0.25,
            "ambiguity": 0.20,
            "multi_hop": 0.20,
            "diversity": 0.20,
            "information_need": 0.15,
        },
        RouteDecision.NO_RETRIEVAL.value: {
            "latency": 0.70,
            "simplicity": 0.30,
        },
    }

    def __init__(
        self,
        weights: Optional[Mapping[str, Mapping[str, float]]] = None,
    ) -> None:
        self._weights = dict(weights or self.DEFAULT_WEIGHTS)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def score(
        self,
        features: RouteFeatures,
        route: RouteDecision,
    ) -> RouteScore:
        """Calculate a normalized score for a route."""

        if route == RouteDecision.DIRECT:
            simplicity = 1.0 - features.query_complexity

            score = (
                simplicity * 0.40
                + features.latency_sensitivity * 0.30
                + (1.0 - features.expected_information_need) * 0.20
                + (1.0 - features.ambiguity) * 0.10
            )

            rationale = "Simple, low-ambiguity queries favor direct retrieval."

        elif route == RouteDecision.MULTI_QUERY:
            score = (
                features.query_complexity * 0.25
                + features.ambiguity * 0.30
                + features.source_diversity_need * 0.25
                + features.expected_information_need * 0.20
            )

            rationale = (
                "Ambiguous or broad queries benefit from multiple query "
                "formulations and diverse retrieval."
            )

        elif route == RouteDecision.ITERATIVE:
            score = (
                features.query_complexity * 0.30
                + features.multi_hop_requirement * 0.30
                + features.expected_information_need * 0.20
                + features.contradiction_risk * 0.10
                + features.domain_specificity * 0.10
            )

            rationale = (
                "Complex multi-hop information needs favor iterative "
                "retrieve-evaluate-refine cycles."
            )

        elif route == RouteDecision.CORRECTIVE:
            score = (
                features.contradiction_risk * 0.35
                + features.ambiguity * 0.20
                + features.expected_information_need * 0.20
                + features.domain_specificity * 0.15
                + features.source_diversity_need * 0.10
            )

            rationale = (
                "High contradiction or evidence-risk favors corrective "
                "retrieval and evidence validation."
            )

        elif route == RouteDecision.HYBRID:
            score = (
                features.query_complexity * 0.25
                + features.ambiguity * 0.20
                + features.multi_hop_requirement * 0.20
                + features.source_diversity_need * 0.20
                + features.expected_information_need * 0.15
            )

            rationale = (
                "Mixed retrieval requirements favor combining multiple "
                "retrieval strategies."
            )

        elif route == RouteDecision.NO_RETRIEVAL:
            score = (
                features.latency_sensitivity * 0.70
                + (1.0 - features.expected_information_need) * 0.30
            )

            rationale = (
                "Very low external information need can avoid retrieval."
            )

        else:
            raise ValueError(f"Unsupported route: {route}")

        # Strong latency requirements should suppress expensive routes.
        expensive_routes = {
            RouteDecision.MULTI_QUERY,
            RouteDecision.ITERATIVE,
            RouteDecision.CORRECTIVE,
            RouteDecision.HYBRID,
        }

        if route in expensive_routes:
            score *= 1.0 - (
                features.latency_sensitivity * 0.25
            )

        # Insufficient budget should suppress expensive strategies.
        if route in expensive_routes:
            budget_penalty = max(0.0, 0.5 - features.token_budget)
            score *= 1.0 - budget_penalty

        return RouteScore(
            route=route,
            score=self._clamp(score),
            rationale=rationale,
        )

    def rank(
        self,
        features: RouteFeatures,
        candidates: Optional[list[RouteDecision]] = None,
    ) -> list[RouteScore]:
        """
        Score and rank candidate routes from highest to lowest.
        """

        candidates = candidates or [
            RouteDecision.DIRECT,
            RouteDecision.MULTI_QUERY,
            RouteDecision.ITERATIVE,
            RouteDecision.CORRECTIVE,
            RouteDecision.HYBRID,
        ]

        scores = [
            self.score(features, route)
            for route in candidates
        ]

        return sorted(
            scores,
            key=lambda item: item.score,
            reverse=True,
        )

    def best_route(
        self,
        features: RouteFeatures,
        candidates: Optional[list[RouteDecision]] = None,
    ) -> RouteScore:
        """Return the highest-scoring route."""

        ranked = self.rank(features, candidates)

        if not ranked:
            raise RuntimeError("No routing candidates available.")

        return ranked[0]