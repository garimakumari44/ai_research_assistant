"""
Adaptive RAG runtime state.

The state represents one complete Adaptive RAG execution.

It is intentionally independent of LangGraph or any specific
workflow engine so that it can later be integrated with one.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .domain_models import (
    AdaptiveRAGConfig,
    QueryAnalysis,
    RetrievalPlan,
    RouteDecision,
)


# ---------------------------------------------------------------------------
# Retrieved Chunk
# ---------------------------------------------------------------------------


class RetrievedChunk(BaseModel):
    """
    A chunk returned by a retrieval operation.
    """

    model_config = ConfigDict(extra="allow")

    chunk_id: str
    content: str

    score: float = 0.0

    document_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------------
# Retrieval Attempt
# ---------------------------------------------------------------------------


class RetrievalAttempt(BaseModel):
    """
    Record of a single retrieval attempt.
    """

    model_config = ConfigDict(extra="allow")

    strategy: str
    query: str

    result_count: int = 0
    average_score: float = 0.0
    max_score: float = 0.0

    success: bool = False

    error: str | None = None
    duration_ms: float | None = None


# ---------------------------------------------------------------------------
# Adaptive RAG Runtime State
# ---------------------------------------------------------------------------


class AdaptiveRAGState(BaseModel):
    """
    Complete runtime state of an Adaptive RAG request.

    This is the canonical internal runtime state used by:

        Planner
            ↓
        Controller
            ↓
        Router
            ↓
        Retrieval / Generation
            ↓
        Evaluator

    The API schemas remain separate from this model.
    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
    )

    # -----------------------------------------------------------------------
    # Execution identity
    # -----------------------------------------------------------------------

    request_id: UUID = Field(
        default_factory=uuid4,
    )

    query: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # -----------------------------------------------------------------------
    # Execution lifecycle
    # -----------------------------------------------------------------------

    status: str = "planning"

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    completed_at: datetime | None = None

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------

    config: AdaptiveRAGConfig = Field(
        default_factory=AdaptiveRAGConfig,
    )

    max_iterations: int = 3

    # -----------------------------------------------------------------------
    # Planning
    # -----------------------------------------------------------------------

    analysis: QueryAnalysis | None = None

    plan: RetrievalPlan | None = None

    # -----------------------------------------------------------------------
    # Routing
    # -----------------------------------------------------------------------

    route: RouteDecision | None = None

    # -----------------------------------------------------------------------
    # Strategy
    # -----------------------------------------------------------------------

    strategy: str | None = None

    # -----------------------------------------------------------------------
    # Retrieval
    # -----------------------------------------------------------------------

    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list,
    )

    retrieval_attempts: list[RetrievalAttempt] = Field(
        default_factory=list,
    )

    retrieval_steps: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    context: str | None = None

    # -----------------------------------------------------------------------
    # Generation
    # -----------------------------------------------------------------------

    generated_answer: str | None = None

    # -----------------------------------------------------------------------
    # Evaluation
    # -----------------------------------------------------------------------

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    evaluation: Any | None = None

    # -----------------------------------------------------------------------
    # Iteration / retry control
    # -----------------------------------------------------------------------

    iteration: int = 0

    retry_count: int = 0

    completed: bool = False

    error: str | None = None

    # -----------------------------------------------------------------------
    # Extensible metadata
    # -----------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # =======================================================================
    # Compatibility properties
    # =======================================================================

    @property
    def execution_id(self) -> str:
        """
        Compatibility identifier used by the API/controller.

        The canonical internal identifier remains request_id.
        """

        return str(self.request_id)

    @property
    def answer(self) -> str | None:
        """
        Compatibility alias for generated_answer.
        """

        return self.generated_answer

    @answer.setter
    def answer(self, value: str | None) -> None:
        self.generated_answer = value

    @property
    def routing_decision(self) -> RouteDecision | None:
        """
        Compatibility alias for route.
        """

        return self.route

    @routing_decision.setter
    def routing_decision(
        self,
        value: RouteDecision | None,
    ) -> None:
        self.route = value

    # =======================================================================
    # Retrieval helpers
    # =======================================================================

    def add_retrieval_attempt(
        self,
        attempt: RetrievalAttempt,
    ) -> None:
        """
        Add a retrieval attempt to the execution history.
        """

        self.retrieval_attempts.append(attempt)

    def add_chunks(
        self,
        chunks: list[RetrievedChunk],
    ) -> None:
        """
        Add retrieved chunks to the current runtime context.
        """

        if not chunks:
            return

        self.retrieved_chunks.extend(chunks)

    def clear_chunks(self) -> None:
        """
        Remove all currently retrieved chunks.
        """

        self.retrieved_chunks.clear()

    # =======================================================================
    # Retry helpers
    # =======================================================================

    def increment_retry(self) -> int:
        """
        Increment retry count and return the new value.
        """

        self.retry_count += 1

        return self.retry_count

    # =======================================================================
    # Context evaluation
    # =======================================================================

    def has_sufficient_context(self) -> bool:
        """
        Determine whether the retrieved context is sufficient
        according to the configured minimum retrieval score.
        """

        if not self.retrieved_chunks:
            return False

        return any(
            chunk.score >= self.config.min_retrieval_score
            for chunk in self.retrieved_chunks
        )

    def best_score(self) -> float:
        """
        Return the highest retrieval score currently available.
        """

        if not self.retrieved_chunks:
            return 0.0

        return max(
            chunk.score
            for chunk in self.retrieved_chunks
        )

    # =======================================================================
    # Context construction
    # =======================================================================

    def build_context(self) -> str:
        """
        Build a textual context from retrieved chunks.
        """

        if not self.retrieved_chunks:
            self.context = None
            return ""

        parts: list[str] = []

        for index, chunk in enumerate(
            self.retrieved_chunks,
            start=1,
        ):
            content = chunk.content.strip()

            if not content:
                continue

            parts.append(
                f"[Source {index}]\n{content}"
            )

        self.context = "\n\n".join(parts)

        return self.context

    # =======================================================================
    # Retrieval reset
    # =======================================================================

    def reset_retrieval(self) -> None:
        """
        Reset retrieval-specific state while preserving:

        - query
        - analysis
        - plan
        - route
        - configuration
        - retry count
        - metadata
        """

        self.retrieved_chunks.clear()
        self.retrieval_attempts.clear()
        self.retrieval_steps.clear()

        self.context = None
        self.confidence = 0.0
        self.evaluation = None

    # =======================================================================
    # Completion helpers
    # =======================================================================

    def mark_completed(self) -> None:
        """
        Mark execution as completed.
        """

        self.completed = True
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(
        self,
        error: str,
    ) -> None:
        """
        Mark execution as failed.
        """

        self.completed = False
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now(timezone.utc)


__all__ = [
    "RetrievedChunk",
    "RetrievalAttempt",
    "AdaptiveRAGState",
]