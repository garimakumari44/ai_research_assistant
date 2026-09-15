"""
Adaptive RAG router.

The router determines the next action in an Adaptive RAG workflow.

It does not perform retrieval or generation.
It only makes routing decisions based on the current state.
"""

from __future__ import annotations

from .domain_models import (
    AdaptiveRAGConfig,
    QueryComplexity,
    RouteDecision,
)
from .state import AdaptiveRAGState


class AdaptiveRAGRouter:
    """
    Routes Adaptive RAG execution based on current state.
    """

    def __init__(
        self,
        config: AdaptiveRAGConfig | None = None,
    ) -> None:
        self.config = config or AdaptiveRAGConfig()

    # ==================================================================
    # PUBLIC ROUTING API
    # ==================================================================

    def route(
        self,
        state: AdaptiveRAGState,
    ) -> RouteDecision:
        """
        Determine the next action for the current state.

        The router consumes the state produced by the controller.

        Expected state fields:

            state.analysis
            state.plan
            state.retrieved_chunks
            state.retry_count
            state.error
        """

        # --------------------------------------------------------------
        # Error state
        # --------------------------------------------------------------

        if state.error:
            return self._route_after_error(state)

        # --------------------------------------------------------------
        # Planner has not produced analysis yet
        # --------------------------------------------------------------

        if state.analysis is None:
            return RouteDecision.RETRIEVE

        # --------------------------------------------------------------
        # Query does not require retrieval
        # --------------------------------------------------------------

        if not state.analysis.requires_retrieval:
            return RouteDecision.DIRECT_GENERATION

        # --------------------------------------------------------------
        # Planner has not produced a plan yet
        # --------------------------------------------------------------

        if state.plan is None:
            return RouteDecision.RETRIEVE

        # --------------------------------------------------------------
        # Initial retrieval
        # --------------------------------------------------------------

        if not state.retrieved_chunks:
            return self._route_initial_retrieval(state)

        # --------------------------------------------------------------
        # Retry / replan
        # --------------------------------------------------------------

        if self._needs_retrieval_retry(state):
            return RouteDecision.REPLAN

        # --------------------------------------------------------------
        # Reranking
        # --------------------------------------------------------------

        if self._needs_reranking(state):
            return RouteDecision.RETRIEVE_AND_RERANK

        # --------------------------------------------------------------
        # Sufficient context
        # --------------------------------------------------------------

        if state.has_sufficient_context():
            return RouteDecision.DIRECT_GENERATION

        # --------------------------------------------------------------
        # Insufficient context
        # --------------------------------------------------------------

        return self._route_insufficient_context(state)

    # ==================================================================
    # REPLANNING
    # ==================================================================

    def should_replan(
        self,
        state: AdaptiveRAGState,
    ) -> bool:
        """
        Determine whether a new retrieval plan is required.
        """

        if state.retry_count >= self.config.max_retries:
            return False

        if not state.retrieved_chunks:
            return True

        return (
            state.best_score()
            < self.config.min_retrieval_score
        )

    # ==================================================================
    # INITIAL RETRIEVAL
    # ==================================================================

    def _route_initial_retrieval(
        self,
        state: AdaptiveRAGState,
    ) -> RouteDecision:
        """
        Determine the first retrieval action.
        """

        assert state.plan is not None

        # Multi-hop has highest retrieval priority.
        if state.plan.multi_hop:
            return RouteDecision.MULTI_QUERY

        # Reranking requires retrieval first.
        if state.plan.rerank:
            return RouteDecision.RETRIEVE_AND_RERANK

        # Hybrid retrieval.
        if state.plan.strategy.value == "hybrid":
            return RouteDecision.HYBRID_RETRIEVAL

        # Query expansion / multi-query.
        if state.plan.expand_query:
            return RouteDecision.MULTI_QUERY

        # Standard retrieval.
        return RouteDecision.RETRIEVE

    # ==================================================================
    # RERANKING
    # ==================================================================

    def _needs_reranking(
        self,
        state: AdaptiveRAGState,
    ) -> bool:
        """
        Determine whether retrieved chunks should be reranked.
        """

        if state.plan is None:
            return False

        if not state.plan.rerank:
            return False

        return len(state.retrieved_chunks) > 1

    # ==================================================================
    # RETRIEVAL RETRY
    # ==================================================================

    def _needs_retrieval_retry(
        self,
        state: AdaptiveRAGState,
    ) -> bool:
        """
        Determine whether retrieval quality is too low.
        """

        if state.retry_count >= self.config.max_retries:
            return False

        if not state.retrieved_chunks:
            return True

        return (
            state.best_score()
            < self.config.min_retrieval_score
        )

    # ==================================================================
    # INSUFFICIENT CONTEXT
    # ==================================================================

    def _route_insufficient_context(
        self,
        state: AdaptiveRAGState,
    ) -> RouteDecision:
        """
        Decide what to do when retrieved context is insufficient.
        """

        if state.retry_count >= self.config.max_retries:
            return RouteDecision.DIRECT_GENERATION

        if (
            state.analysis
            and state.analysis.complexity
            == QueryComplexity.HIGH
        ):
            return RouteDecision.REPLAN

        if (
            state.plan
            and state.plan.rerank
        ):
            return RouteDecision.RETRIEVE_AND_RERANK

        return RouteDecision.REPLAN

    # ==================================================================
    # ERROR ROUTING
    # ==================================================================

    def _route_after_error(
        self,
        state: AdaptiveRAGState,
    ) -> RouteDecision:
        """
        Decide whether an error can be retried.
        """

        if (
            state.retry_count
            < self.config.max_retries
        ):
            return RouteDecision.REPLAN

        return RouteDecision.ABORT


__all__ = [
    "AdaptiveRAGRouter",
]