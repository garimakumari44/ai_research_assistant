"""
Routing policy for Adaptive RAG.

Determines which retrieval strategy should be used for a query.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RetrievalStrategy(str, Enum):
    DIRECT = "direct"
    ITERATIVE = "iterative"
    MULTI_QUERY = "multi_query"
    CORRECTIVE = "corrective"
    GRAPH_AUGMENTED = "graph_augmented"


@dataclass(frozen=True)
class RoutingDecision:
    strategy: RetrievalStrategy
    reason: str
    confidence: float


class RoutingPolicy:
    """
    Selects an appropriate RAG strategy based on query characteristics.

    This policy intentionally uses deterministic heuristics. A more
    sophisticated router can later be backed by an LLM without changing
    the controller interface.
    """

    def __init__(
        self,
        *,
        direct_threshold: float = 0.85,
        iterative_threshold: float = 0.60,
        graph_threshold: float = 0.70,
    ) -> None:
        self.direct_threshold = direct_threshold
        self.iterative_threshold = iterative_threshold
        self.graph_threshold = graph_threshold

    def route(
        self,
        query: str,
        *,
        query_complexity: float = 0.5,
        requires_multi_hop: bool = False,
        requires_entity_relationships: bool = False,
        previous_confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """
        Select a retrieval strategy.

        Parameters
        ----------
        query:
            User query.

        query_complexity:
            Normalized complexity score in [0, 1].

        requires_multi_hop:
            Whether answering likely requires multiple retrieval steps.

        requires_entity_relationships:
            Whether the query benefits from graph/entity traversal.

        previous_confidence:
            Confidence from a previous retrieval/generation iteration.

        metadata:
            Optional query metadata.
        """

        query = query.strip()

        if not query:
            return RoutingDecision(
                strategy=RetrievalStrategy.DIRECT,
                reason="Empty or invalid query; defaulting to direct retrieval.",
                confidence=0.0,
            )

        complexity = self._clamp(query_complexity)

        if requires_entity_relationships:
            return RoutingDecision(
                strategy=RetrievalStrategy.GRAPH_AUGMENTED,
                reason=(
                    "The query requires entity relationships or "
                    "knowledge-graph traversal."
                ),
                confidence=max(complexity, self.graph_threshold),
            )

        if requires_multi_hop:
            return RoutingDecision(
                strategy=RetrievalStrategy.ITERATIVE,
                reason="The query requires multi-hop retrieval.",
                confidence=max(complexity, self.iterative_threshold),
            )

        if self._looks_like_multi_query_problem(query):
            return RoutingDecision(
                strategy=RetrievalStrategy.MULTI_QUERY,
                reason=(
                    "The query contains multiple information needs or "
                    "requires multiple semantic perspectives."
                ),
                confidence=0.75,
            )

        if previous_confidence is not None:
            previous_confidence = self._clamp(previous_confidence)

            if previous_confidence < 0.40:
                return RoutingDecision(
                    strategy=RetrievalStrategy.CORRECTIVE,
                    reason=(
                        "Previous retrieval produced low confidence; "
                        "corrective retrieval is required."
                    ),
                    confidence=1.0 - previous_confidence,
                )

        if complexity >= self.direct_threshold:
            return RoutingDecision(
                strategy=RetrievalStrategy.ITERATIVE,
                reason=(
                    "Query complexity is high enough to justify "
                    "iterative retrieval."
                ),
                confidence=complexity,
            )

        return RoutingDecision(
            strategy=RetrievalStrategy.DIRECT,
            reason="Query can be handled using direct retrieval.",
            confidence=max(
                0.5,
                1.0 - complexity,
            ),
        )

    @staticmethod
    def _looks_like_multi_query_problem(query: str) -> bool:
        """
        Detect simple signals that a query contains multiple information
        requirements.
        """

        lowered = query.lower()

        multi_query_patterns = (
            "compare",
            "comparison",
            "difference between",
            "advantages and disadvantages",
            "pros and cons",
            "compare and contrast",
            "both",
            "respectively",
            "multiple",
        )

        return any(
            pattern in lowered
            for pattern in multi_query_patterns
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))