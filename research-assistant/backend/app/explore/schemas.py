from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.adaptive_rag import (
    AdaptiveRAGResponse,
    RAGStrategy,
    RetrievalMode,
)
from app.schemas.retrieval import RetrievalResponse


class ExploreRequest(BaseModel):
    """
    Public API request for the Explore endpoint.

    Explore is the application-level entry point. It can either execute
    retrieval directly or route the query through Adaptive RAG.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Research or knowledge query.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of results to retrieve.",
    )

    retrieval_mode: RetrievalMode = Field(
        default=RetrievalMode.HYBRID,
        description="Retrieval strategy used by the retrieval layer.",
    )

    adaptive: bool = Field(
        default=True,
        description="Whether to execute the query through Adaptive RAG.",
    )

    strategy: RAGStrategy | None = Field(
        default=None,
        description="Optional Adaptive RAG strategy override.",
    )

    max_iterations: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum Adaptive RAG iterations.",
    )

    confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for adaptive execution.",
    )

    paper_id: str | None = Field(
        default=None,
        description="Optional paper identifier.",
    )

    document_id: str | None = Field(
        default=None,
        description="Optional document identifier.",
    )

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional retrieval filters.",
    )

    enable_graph: bool = Field(
        default=False,
        description="Enable graph-based augmentation.",
    )

    enable_multi_query: bool = Field(
        default=False,
        description="Enable multi-query expansion.",
    )

    enable_correction: bool = Field(
        default=True,
        description="Enable corrective retrieval.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request metadata.",
    )


class ExploreResponse(BaseModel):
    """
    Public API response returned by the Explore endpoint.
    """

    model_config = ConfigDict(from_attributes=True)

    query: str

    retrieval: RetrievalResponse | None = None

    adaptive_rag: AdaptiveRAGResponse | None = None

    answer: str | None = None

    sources: list[Any] = Field(
        default_factory=list,
    )

    confidence: float | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    duration_ms: float | None = None

    success: bool = True