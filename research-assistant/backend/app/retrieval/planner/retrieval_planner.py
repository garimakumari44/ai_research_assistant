from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.retrieval.models import (
    AdaptiveRAGConfig,
    RetrievalMode,
    RetrievalPlan,
    RetrievalQuery,
)


# ============================================================================
# ENUMS
# ============================================================================


class QueryIntent(str, Enum):
    """
    High-level semantic intent of the query.
    """

    FACTUAL = "factual"
    EXPLANATORY = "explanatory"
    COMPARATIVE = "comparative"
    PROCEDURAL = "procedural"
    NAVIGATIONAL = "navigational"
    ANALYTICAL = "analytical"
    GENERAL = "general"


class QueryComplexity(str, Enum):
    """
    Estimated complexity of a retrieval query.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# QUERY ANALYSIS
# ============================================================================


class QueryAnalysis(BaseModel):
    """
    Result of adaptive query analysis.
    """

    model_config = ConfigDict(
        use_enum_values=False,
        extra="allow",
    )

    intent: QueryIntent = Field(
        default=QueryIntent.GENERAL
    )

    complexity: QueryComplexity = Field(
        default=QueryComplexity.LOW
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    reasoning: str = Field(
        default=""
    )


# ============================================================================
# ADAPTIVE RAG PLANNER
# ============================================================================


class AdaptiveRAGPlanner:
    """
    Adaptive retrieval planner.

    Determines:

    - query intent
    - query complexity
    - retrieval mode
    - top-k
    - whether reranking should be used

    The planner does not execute retrieval itself.
    """

    def __init__(
        self,
        config: AdaptiveRAGConfig | None = None,
    ) -> None:

        self.config = (
            config
            or AdaptiveRAGConfig()
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def plan(
        self,
        query: str,
    ) -> tuple[QueryAnalysis, RetrievalPlan]:
        """
        Analyze a query and create a retrieval plan.
        """

        query = (
            str(query)
            .strip()
        )

        analysis = self._analyze_query(
            query
        )

        retrieval_mode = (
            self._select_mode(
                analysis
            )
        )

        top_k = self._select_top_k(
            analysis
        )

        rerank = self._should_rerank(
            analysis
        )

        plan = self._build_plan(
            mode=retrieval_mode,
            top_k=top_k,
            rerank=rerank,
        )

        return analysis, plan

    # ========================================================================
    # QUERY ANALYSIS
    # ========================================================================

    def _analyze_query(
        self,
        query: str,
    ) -> QueryAnalysis:

        if not query:
            return QueryAnalysis(
                intent=QueryIntent.GENERAL,
                complexity=QueryComplexity.LOW,
                confidence=0.0,
                reasoning="Empty query.",
            )

        normalized = query.lower()

        intent = self._classify_intent(
            normalized
        )

        complexity = self._classify_complexity(
            normalized
        )

        confidence = self._estimate_confidence(
            normalized,
            intent,
            complexity,
        )

        reasoning = (
            f"Detected {intent.value} intent "
            f"with {complexity.value} complexity."
        )

        return QueryAnalysis(
            intent=intent,
            complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
        )

    # ========================================================================
    # INTENT CLASSIFICATION
    # ========================================================================

    @staticmethod
    def _classify_intent(
        query: str,
    ) -> QueryIntent:

        comparative_terms = (
            "compare",
            "comparison",
            "versus",
            "vs",
            "difference",
            "differences",
            "better than",
        )

        explanatory_terms = (
            "why",
            "explain",
            "describe",
            "what is",
            "what are",
            "meaning",
        )

        procedural_terms = (
            "how to",
            "how do",
            "steps",
            "implement",
            "implementation",
            "configure",
            "setup",
            "set up",
        )

        navigational_terms = (
            "where",
            "find",
            "location",
            "source",
        )

        analytical_terms = (
            "analyze",
            "analysis",
            "evaluate",
            "assess",
            "impact",
            "effect",
            "trend",
        )

        factual_terms = (
            "when",
            "who",
            "which",
            "how many",
            "how much",
            "version",
        )

        if any(
            term in query
            for term in comparative_terms
        ):
            return QueryIntent.COMPARATIVE

        if any(
            term in query
            for term in procedural_terms
        ):
            return QueryIntent.PROCEDURAL

        if any(
            term in query
            for term in analytical_terms
        ):
            return QueryIntent.ANALYTICAL

        if any(
            term in query
            for term in explanatory_terms
        ):
            return QueryIntent.EXPLANATORY

        if any(
            term in query
            for term in navigational_terms
        ):
            return QueryIntent.NAVIGATIONAL

        if any(
            term in query
            for term in factual_terms
        ):
            return QueryIntent.FACTUAL

        return QueryIntent.GENERAL

    # ========================================================================
    # COMPLEXITY CLASSIFICATION
    # ========================================================================

    @staticmethod
    def _classify_complexity(
        query: str,
    ) -> QueryComplexity:

        words = query.split()

        length = len(words)

        complex_terms = (
            "compare",
            "versus",
            "difference",
            "tradeoff",
            "trade-off",
            "architecture",
            "evaluate",
            "analysis",
            "analyze",
            "multiple",
            "relationship",
            "relationships",
            "impact",
            "advantages",
            "disadvantages",
        )

        complex_term_count = sum(
            1
            for term in complex_terms
            if term in query
        )

        if (
            length >= 30
            or complex_term_count >= 3
        ):
            return QueryComplexity.HIGH

        if (
            length >= 12
            or complex_term_count >= 1
        ):
            return QueryComplexity.MEDIUM

        return QueryComplexity.LOW

    # ========================================================================
    # CONFIDENCE
    # ========================================================================

    @staticmethod
    def _estimate_confidence(
        query: str,
        intent: QueryIntent,
        complexity: QueryComplexity,
    ) -> float:

        if not query:
            return 0.0

        confidence = 0.60

        if intent != QueryIntent.GENERAL:
            confidence += 0.15

        if complexity != QueryComplexity.LOW:
            confidence += 0.05

        return min(
            confidence,
            0.95,
        )

    # ========================================================================
    # RETRIEVAL MODE
    # ========================================================================

    def _select_mode(
        self,
        analysis: QueryAnalysis,
    ) -> RetrievalMode:

        if analysis.intent in {
            QueryIntent.FACTUAL,
            QueryIntent.NAVIGATIONAL,
        }:
            return RetrievalMode.BM25

        if analysis.intent in {
            QueryIntent.EXPLANATORY,
            QueryIntent.COMPARATIVE,
            QueryIntent.ANALYTICAL,
            QueryIntent.PROCEDURAL,
        }:
            return RetrievalMode.HYBRID

        return RetrievalMode.HYBRID

    # ========================================================================
    # TOP K
    # ========================================================================

    def _select_top_k(
        self,
        analysis: QueryAnalysis,
    ) -> int:

        configured_top_k = getattr(
            self.config,
            "top_k",
            None,
        )

        if not isinstance(
            configured_top_k,
            int,
        ):
            configured_top_k = 10

        if analysis.complexity == QueryComplexity.HIGH:
            return min(
                configured_top_k * 2,
                100,
            )

        if analysis.complexity == QueryComplexity.MEDIUM:
            return min(
                int(
                    configured_top_k * 1.5
                ),
                100,
            )

        return min(
            configured_top_k,
            100,
        )

    # ========================================================================
    # RERANKING
    # ========================================================================

    def _should_rerank(
        self,
        analysis: QueryAnalysis,
    ) -> bool:

        configured = getattr(
            self.config,
            "rerank",
            None,
        )

        if isinstance(
            configured,
            bool,
        ):
            if configured:
                return True

        return analysis.complexity in {
            QueryComplexity.MEDIUM,
            QueryComplexity.HIGH,
        }

    # ========================================================================
    # PLAN BUILDING
    # ========================================================================

    @staticmethod
    def _build_plan(
        mode: RetrievalMode,
        top_k: int,
        rerank: bool,
    ) -> RetrievalPlan:

        plan = RetrievalPlan(
            mode=mode,
            top_k=top_k,
            filters={},
            rerank=rerank,
        )

        return plan


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================


class RetrievalPlanner:
    """
    Backward-compatible wrapper around AdaptiveRAGPlanner.

    Existing code that uses:

        RetrievalPlanner()
        planner.create_plan(query)

    can continue to work.
    """

    def __init__(
        self,
        config: AdaptiveRAGConfig | None = None,
    ) -> None:

        self.adaptive_planner = (
            AdaptiveRAGPlanner(
                config
            )
        )

    def classify_query(
        self,
        query: str,
    ) -> str:

        analysis = (
            self.adaptive_planner
            ._analyze_query(query)
        )

        if analysis.intent == QueryIntent.COMPARATIVE:
            return "semantic"

        if analysis.intent in {
            QueryIntent.EXPLANATORY,
            QueryIntent.PROCEDURAL,
            QueryIntent.ANALYTICAL,
        }:
            return "semantic"

        if analysis.intent in {
            QueryIntent.FACTUAL,
            QueryIntent.NAVIGATIONAL,
        }:
            return "keyword"

        return "mixed"

    def create_plan(
        self,
        query: RetrievalQuery,
    ) -> RetrievalPlan:

        analysis, plan = (
            self.adaptive_planner.plan(
                query.query
            )
        )

        plan.top_k = (
            query.top_k
        )

        plan.filters = dict(
            query.filters or {}
        )

        if getattr(
            query,
            "mode",
            None,
        ) is not None:

            plan.mode = RetrievalMode(
                query.mode
            )

        return plan


__all__ = [
    "QueryIntent",
    "QueryComplexity",
    "QueryAnalysis",
    "AdaptiveRAGPlanner",
    "RetrievalPlanner",
]