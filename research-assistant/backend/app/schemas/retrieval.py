
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Query Analysis
# ---------------------------------------------------------------------------


class QueryAnalysis(BaseModel):
    """
    Structured analysis of the user's retrieval query.
    """

    model_config = ConfigDict(from_attributes=True)

    original_query: str
    normalized_query: str | None = None

    keywords: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)

    filters: dict[str, Any] = Field(default_factory=dict)

    requires_semantic_search: bool = True
    requires_keyword_search: bool = True


class QueryClassification(BaseModel):
    """
    Classification of a retrieval query.
    """

    model_config = ConfigDict(from_attributes=True)

    query_type: str = "general"
    intent: str = "information_retrieval"

    domain: str | None = None

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    labels: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    """
    Source information for a retrieved chunk.

    Important ID conventions:

    - papers.id -> INTEGER
    - document_chunks.id -> UUID
    - document_chunks.document_id -> UUID
    """

    model_config = ConfigDict(from_attributes=True)

    # papers.id is INTEGER in the database.
    paper_id: int | None = None

    # document/document-chunk identifiers are UUIDs.
    document_id: UUID | None = None

    chunk_id: UUID

    page: int | None = None
    section: str | None = None
    source: str | None = None


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class Evidence(BaseModel):
    """
    Evidence associated with a retrieved result.

    This provides the retrieval layer with a stable structure that can
    later be consumed by citation, reasoning, and report-generation layers.
    """

    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID | None = None

    content: str

    score: float = 0.0

    rank: int | None = None

    provenance: Provenance

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Retrieval Request
# ---------------------------------------------------------------------------


class RetrievalRequest(BaseModel):
    """
    Request payload for knowledge retrieval.

    ID conventions:

    - paper_id -> papers.id -> INTEGER
    - document_id -> UUID
    """

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Natural-language research query.",
    )

    # papers.id is INTEGER.
    paper_id: int | None = Field(
        default=None,
        description="Restrict retrieval to a specific paper ID.",
    )

    # document_id is UUID.
    document_id: UUID | None = Field(
        default=None,
        description="Restrict retrieval to a specific document.",
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results.",
    )

    vector_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight assigned to vector similarity.",
    )

    keyword_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight assigned to keyword relevance.",
    )


# ---------------------------------------------------------------------------
# Retrieval Result
# ---------------------------------------------------------------------------


class RetrievalResult(BaseModel):
    """
    Canonical representation of one retrieved knowledge chunk.

    This is the primary backend/frontend retrieval contract.

    ID conventions:

    - chunk_id -> UUID
    - document_id -> UUID
    - paper_id -> INTEGER
    - section_id -> UUID
    """

    model_config = ConfigDict(from_attributes=True)

    # -----------------------------------------------------------------------
    # Identity
    # -----------------------------------------------------------------------

    chunk_id: UUID

    document_id: UUID

    # papers.id is INTEGER, not UUID.
    paper_id: int | None = None

    section_id: UUID | None = None

    # -----------------------------------------------------------------------
    # Content
    # -----------------------------------------------------------------------

    content: str

    # -----------------------------------------------------------------------
    # Ranking
    # -----------------------------------------------------------------------

    score: float = 0.0

    rank: int = 0

    retrieval_method: str = "hybrid"

    rerank_score: float | None = None

    # -----------------------------------------------------------------------
    # Individual retrieval scores
    # -----------------------------------------------------------------------

    vector_score: float | None = None

    keyword_score: float | None = None

    # -----------------------------------------------------------------------
    # Source information
    # -----------------------------------------------------------------------

    provenance: Provenance | None = None

    # -----------------------------------------------------------------------
    # Optional evidence representation
    # -----------------------------------------------------------------------

    evidence: Evidence | None = None

    # -----------------------------------------------------------------------
    # Extensible metadata
    # -----------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Retrieval Response
# ---------------------------------------------------------------------------


class RetrievalResponse(BaseModel):
    """
    Canonical retrieval API response.
    """

    model_config = ConfigDict(from_attributes=True)

    query: str

    results: list[RetrievalResult] = Field(
        default_factory=list
    )

    total: int = 0

    top_k: int = 10

    retrieval_mode: str = "hybrid"

    # -----------------------------------------------------------------------
    # Query understanding
    # -----------------------------------------------------------------------

    query_analysis: QueryAnalysis | None = None

    query_classification: QueryClassification | None = None

    # -----------------------------------------------------------------------
    # Optional response-level evidence
    # -----------------------------------------------------------------------

    evidence: list[Evidence] = Field(
        default_factory=list
    )

    # -----------------------------------------------------------------------
    # Optional diagnostics
    # -----------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

