
"""
Adaptive RAG self-reflection layer.

This package provides post-retrieval and post-generation quality control
components for the Adaptive RAG pipeline.

Components
----------
ReflectionLoop
    Coordinates iterative self-reflection.

Critic
    Produces a structured quality judgment.

GapDetector
    Detects missing information required to answer the query.

RetrievalChecker
    Determines whether retrieved evidence is sufficient and relevant.

AnswerChecker
    Validates the generated answer against the user query and evidence.

HallucinationDetector
    Detects claims that are unsupported or contradicted by evidence.
"""

from .answer_checker import (
    AnswerCheckResult,
    AnswerChecker,
)

from .critic import (
    Critic,
    CriticResult,
    CriticSeverity,
)

from .gap_detector import (
    Gap,
    GapDetector,
    GapSeverity,
)

from .hallucination_detector import (
    HallucinationDetector,
    HallucinationResult,
    UnsupportedClaim,
)

from .reflection_loop import (
    ReflectionConfig,
    ReflectionDecision,
    ReflectionLoop,
    ReflectionResult,
    ReflectionStatus,
)

from .retrieval_checker import (
    RetrievalCheckResult,
    RetrievalChecker,
)

__all__ = [
    "AnswerCheckResult",
    "AnswerChecker",
    "Critic",
    "CriticResult",
    "CriticSeverity",
    "Gap",
    "GapDetector",
    "GapSeverity",
    "HallucinationDetector",
    "HallucinationResult",
    "UnsupportedClaim",
    "ReflectionConfig",
    "ReflectionDecision",
    "ReflectionLoop",
    "ReflectionResult",
    "ReflectionStatus",
    "RetrievalCheckResult",
    "RetrievalChecker",
]

