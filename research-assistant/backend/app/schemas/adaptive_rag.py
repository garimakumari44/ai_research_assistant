"""
Pydantic schemas for the Adaptive RAG API.

These schemas define the HTTP contract between the frontend
and the Adaptive RAG orchestration layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RAGStrategy(str, Enum):
    DIRECT = "direct"
    ITERATIVE = "iterative"
    MULTI_QUERY = "multi_query"
    CORRECTIVE = "corrective"
    GRAPH_AUGMENTED = "graph_augmented"


class RoutingDecision(str, Enum):
    DIRECT = "direct"
    RETRIEVE = "retrieve"
    REFINE = "refine"
    RETRY = "retry"
    STOP = "stop"


class RetrievalMode(str, Enum):
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    GRAPH = "graph"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    GENERATING = "generating"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class AdaptiveRAGRequest(BaseModel):
    """
    Request submitted by the frontend to execute Adaptive RAG.
    """

    model_config = ConfigDict(extra="allow")

    query: str = Field(
        ...,
        min_length=1,
        description="User's natural-language query.",
    )

    conversation_id: str | None = None

    execution_id: str | None = None

    collection_id: str | None = None

    document_ids: list[str] | None = None

    adaptive: bool = True

    strategy: RAGStrategy | None = None

    max_iterations: int = Field(
        default=3,
        ge=1,
        le=20,
    )

    confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    retrieval_mode: RetrievalMode = RetrievalMode.VECTOR

    enable_graph: bool = False

    enable_multi_query: bool = False

    enable_correction: bool = True

    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


class RetrievedChunk(BaseModel):
    id: str

    document_id: str | None = None

    document_name: str | None = None

    content: str

    score: float | None = None

    rank: int | None = None

    metadata: dict[str, Any] | None = None


class RetrievalStep(BaseModel):
    step: int

    query: str

    mode: RetrievalMode

    strategy: RAGStrategy | None = None

    chunks: list[RetrievedChunk] = Field(default_factory=list)

    result_count: int = 0

    duration_ms: float | None = None


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


class QueryPlan(BaseModel):
    strategy: RAGStrategy

    reasoning: str | None = None

    steps: list[str] = Field(default_factory=list)

    estimated_iterations: int | None = None

    retrieval_required: bool = True

    graph_required: bool = False

    multi_query_required: bool = False

    corrective_retrieval: bool = False


# ---------------------------------------------------------------------------
# Confidence / evaluation
# ---------------------------------------------------------------------------


class ConfidenceScore(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: ConfidenceLevel

    threshold: float | None = None

    reasons: list[str] = Field(default_factory=list)

    grounded: bool = False


class EvaluationResult(BaseModel):
    confidence: ConfidenceScore

    answerable: bool

    grounded: bool

    complete: bool

    relevant: bool

    should_continue: bool

    should_retrieve_again: bool

    feedback: list[str] = Field(default_factory=list)

    missing_information: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class AdaptiveRAGState(BaseModel):
    execution_id: str

    query: str

    status: ExecutionStatus

    iteration: int = 0

    max_iterations: int = 3

    strategy: RAGStrategy

    routing_decision: RoutingDecision | None = None

    plan: QueryPlan | None = None

    retrieval_steps: list[RetrievalStep] = Field(
        default_factory=list
    )

    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list
    )

    answer: str | None = None

    confidence: ConfidenceScore | None = None

    evaluation: EvaluationResult | None = None

    error: str | None = None

    started_at: datetime | None = None

    completed_at: datetime | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class AdaptiveRAGResponse(BaseModel):
    execution_id: str

    status: ExecutionStatus

    query: str

    answer: str | None = None

    strategy: RAGStrategy

    routing_decision: RoutingDecision | None = None

    state: AdaptiveRAGState | None = None

    plan: QueryPlan | None = None

    confidence: ConfidenceScore | None = None

    evaluation: EvaluationResult | None = None

    sources: list[RetrievedChunk] = Field(
        default_factory=list
    )

    retrieval_steps: list[RetrievalStep] = Field(
        default_factory=list
    )

    iterations: int = 0

    duration_ms: float | None = None

    error: str | None = None


# ---------------------------------------------------------------------------
# Execution endpoints
# ---------------------------------------------------------------------------


class AdaptiveRAGExecution(BaseModel):
    execution_id: str

    query: str

    status: ExecutionStatus

    strategy: RAGStrategy

    iteration: int = 0

    confidence: float | None = None

    created_at: datetime | None = None

    completed_at: datetime | None = None


class AdaptiveRAGExecutionList(BaseModel):
    items: list[AdaptiveRAGExecution] = Field(
        default_factory=list
    )

    total: int

    page: int = 1

    page_size: int = 20


# ---------------------------------------------------------------------------
# Health / configuration
# ---------------------------------------------------------------------------


class AdaptiveRAGHealth(BaseModel):
    status: str

    adaptive_rag_enabled: bool

    available_strategies: list[RAGStrategy]

    version: str | None = None


class AdaptiveRAGConfig(BaseModel):
    default_strategy: RAGStrategy

    default_top_k: int

    default_max_iterations: int

    default_confidence_threshold: float

    enabled_strategies: list[RAGStrategy]

    enabled_retrieval_modes: list[RetrievalMode]

    graph_enabled: bool

    corrective_retrieval_enabled: bool

    multi_query_enabled: bool