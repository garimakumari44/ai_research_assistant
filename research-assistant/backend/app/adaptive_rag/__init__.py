"""
Adaptive RAG package.

Provides the planning, routing, evaluation, state management,
and orchestration components for the Adaptive RAG system.
"""

from .controller import AdaptiveRAGController

from .evaluator import (
    AdaptiveRAGEvaluator,
    RetrievalEvaluation,
)

from .exceptions import (
    AdaptiveRAGConfigurationError,
    AdaptiveRAGError,
    AdaptiveRAGEvaluationError,
    AdaptiveRAGGenerationError,
    AdaptiveRAGMaxRetriesExceeded,
    AdaptiveRAGPlanningError,
    AdaptiveRAGRetrievalError,
    AdaptiveRAGRoutingError,
    AdaptiveRAGStateError,
)

from .domain_models import (
    AdaptiveRAGConfig,
    QueryAnalysis,
    QueryComplexity,
    QueryIntent,
    RetrievalPlan,
    RetrievalStrategy,
    RouteDecision,
)

from .planner import AdaptiveRAGPlanner
from .router import AdaptiveRAGRouter

from .state import (
    AdaptiveRAGState,
    RetrievedChunk,
    RetrievalAttempt,
)


__all__ = [
    "AdaptiveRAGController",

    "AdaptiveRAGEvaluator",
    "RetrievalEvaluation",

    "AdaptiveRAGConfig",

    "QueryAnalysis",
    "QueryComplexity",
    "QueryIntent",
    "RetrievalPlan",
    "RetrievalStrategy",
    "RouteDecision",

    "AdaptiveRAGState",
    "RetrievedChunk",
    "RetrievalAttempt",

    "AdaptiveRAGPlanner",
    "AdaptiveRAGRouter",

    "AdaptiveRAGError",
    "AdaptiveRAGConfigurationError",
    "AdaptiveRAGEvaluationError",
    "AdaptiveRAGGenerationError",
    "AdaptiveRAGMaxRetriesExceeded",
    "AdaptiveRAGPlanningError",
    "AdaptiveRAGRetrievalError",
    "AdaptiveRAGRoutingError",
    "AdaptiveRAGStateError",
]
