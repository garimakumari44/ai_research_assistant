
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================================================
# ENUMS
# ============================================================================


class RetrievalMode(str, Enum):
    """
    Low-level retrieval engine.

    This answers:

        HOW do we retrieve candidates?
    """

    DENSE = "dense"
    BM25 = "bm25"
    HYBRID = "hybrid"


class RetrievalStrategy(str, Enum):
    """
    High-level Adaptive RAG execution strategy.

    This answers:

        HOW should retrieval behave overall?
    """

    DIRECT = "direct"
    MULTI_QUERY = "multi_query"
    ITERATIVE = "iterative"
    CORRECTIVE = "corrective"
    GRAPH_AUGMENTED = "graph_augmented"

    # Compatibility strategies used by older planner implementations.
    BROAD = "broad"
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class QueryType(str, Enum):
    """
    Low-level retrieval query type.
    """

    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class QueryIntent(str, Enum):
    """
    Semantic intent of the user query.
    """

    GENERAL = "general"
    FACTUAL = "factual"

    DEFINITIONAL = "definitional"
    EXPLANATORY = "explanatory"
    METHOD = "method"
    DATASET = "dataset"
    LITERATURE = "literature"
    COMPARATIVE = "comparative"
    MULTI_HOP = "multi_hop"

    ANALYTICAL = "analytical"
    EXPLORATORY = "exploratory"
    SUMMARIZATION = "summarization"


class QueryComplexity(str, Enum):
    """
    Estimated retrieval complexity.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# ADAPTIVE RAG CONFIGURATION
# ============================================================================


class AdaptiveRAGConfig(BaseModel):
    """
    Configuration for Adaptive RAG planning.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    default_strategy: RetrievalStrategy = RetrievalStrategy.DIRECT

    default_top_k: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    max_context_chunks: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    default_similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    # Reranking remains available globally.
    # Individual retrieval requests can explicitly enable it.
    enable_reranking: bool = True

    enable_query_expansion: bool = True
    enable_multi_query: bool = True
    enable_multi_hop: bool = True

    max_queries: int = Field(
        default=3,
        ge=1,
        le=10,
    )


# ============================================================================
# QUERY CLASSIFICATION
# ============================================================================


class QueryClassification(BaseModel):
    """
    Deterministic semantic classification.

    Classification describes WHAT the user is asking.

    It does not choose the retrieval engine.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    intent: QueryIntent = QueryIntent.FACTUAL

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    signals: List[str] = Field(
        default_factory=list,
    )

    requires_multiple_documents: bool = False
    requires_broad_search: bool = False
    requires_multi_hop: bool = False


# ============================================================================
# QUERY REWRITE
# ============================================================================


class QueryRewrite(BaseModel):
    """
    Retrieval-oriented query rewrite.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    original_query: str = ""

    rewritten_query: str = ""

    search_queries: List[str] = Field(
        default_factory=list,
    )

    keywords: List[str] = Field(
        default_factory=list,
    )

    expanded_terms: List[str] = Field(
        default_factory=list,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    @property
    def queries(self) -> List[str]:
        """
        Backwards-compatible alias.
        """

        return self.search_queries

    @property
    def primary_query(self) -> str:
        """
        Return the best retrieval query.
        """

        if self.rewritten_query:
            return self.rewritten_query

        if self.search_queries:
            return self.search_queries[0]

        return self.original_query


# ============================================================================
# LOW-LEVEL SEARCH RESULTS
# ============================================================================


class DenseSearchResult(BaseModel):
    """
    Native dense retrieval result.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
    )

    score: float = 0.0


class SparseSearchResult(BaseModel):
    """
    Native sparse/BM25 retrieval result.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
    )

    score: float = 0.0


class HybridSearchResult(BaseModel):
    """
    Result produced by dense + sparse fusion.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
    )

    dense_score: float = 0.0
    sparse_score: float = 0.0
    fusion_score: float = 0.0
    score: float = 0.0


class RRFResult(BaseModel):
    """
    Reciprocal Rank Fusion result.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
    )

    score: float = 0.0

    rank: int = Field(
        default=1,
        ge=1,
    )


class SearchResult(BaseModel):
    """
    Canonical low-level retrieval result.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: str = Field(
        ...,
        min_length=1,
    )

    score: float = 0.0

    text: str = ""

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    retrieval_method: RetrievalMode = RetrievalMode.HYBRID

    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    rerank_score: Optional[float] = None

    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    source_id: Optional[str] = None
    paper_id: Optional[str] = None


class RetrieverResult(SearchResult):
    """
    Backwards-compatible result name.
    """

    pass


# ============================================================================
# FILTERS
# ============================================================================


class RetrievalFilters(BaseModel):
    """
    Structured metadata filters.
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
    )

    paper_id: Optional[str] = None
    document_id: Optional[str] = None
    source_id: Optional[str] = None
    chunk_id: Optional[str] = None

    source_type: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None

    year_from: Optional[int] = Field(
        default=None,
        ge=0,
    )

    year_to: Optional[int] = Field(
        default=None,
        ge=0,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def validate_year_range(self) -> "RetrievalFilters":
        if (
            self.year_from is not None
            and self.year_to is not None
            and self.year_from > self.year_to
        ):
            raise ValueError(
                "year_from cannot be greater than year_to"
            )

        return self


# ============================================================================
# RETRIEVAL QUERY
# ============================================================================


class RetrievalQuery(BaseModel):
    """
    Canonical retrieval request.

    This is the contract between the API/service layer and the
    RetrievalPipeline.

    Reranking is disabled by default because it requires loading the
    CrossEncoder model and its transformer/PyTorch runtime.

    Workflows that explicitly require reranking can still pass:

        enable_reranking=True
    """

    model_config = ConfigDict(
        extra="allow"
    )

    query: str

    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    filters: dict[str, Any] = Field(
        default_factory=dict,
    )

    mode: RetrievalMode = RetrievalMode.HYBRID

    vector_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    keyword_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    # IMPORTANT:
    # Keep reranking opt-in for lightweight retrieval paths such as
    # Explore. Explicit research workflows can still enable it.
    enable_reranking: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# RETRIEVED DOCUMENT
# ============================================================================


class RetrievedDocument(BaseModel):
    """
    Canonical document/chunk returned by retrieval.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: str = Field(
        ...,
        min_length=1,
    )

    text: str = ""

    score: float = 0.0

    source_id: Optional[str] = None
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    paper_id: Optional[str] = None

    source: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# FINAL RETRIEVAL RESULT
# ============================================================================


class RetrievalResult(BaseModel):
    """
    Final pipeline-level retrieval result.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    document: RetrievedDocument

    rank: int = Field(
        ...,
        ge=1,
    )

    score: float = 0.0

    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    rerank_score: Optional[float] = None

    retrieval_method: RetrievalMode = RetrievalMode.HYBRID

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# RETRIEVAL RESPONSE
# ============================================================================


class RetrievalResponse(BaseModel):
    """
    Complete retrieval response.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    query: str

    results: List[RetrievalResult] = Field(
        default_factory=list,
    )

    total_results: int = 0

    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def validate_total_results(self) -> "RetrievalResponse":
        self.total_results = len(self.results)
        return self

    @property
    def documents(self) -> List[RetrievedDocument]:
        return [
            result.document
            for result in self.results
        ]


# ============================================================================
# ADAPTIVE RAG PLAN
# ============================================================================


class RetrievalPlan(BaseModel):
    """
    Execution plan produced by Adaptive RAG.

    strategy = overall Adaptive RAG behavior

    mode = low-level retrieval engine

    rerank = whether this specific plan requires CrossEncoder reranking.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    strategy: RetrievalStrategy = (
        RetrievalStrategy.DIRECT
    )

    mode: RetrievalMode = RetrievalMode.HYBRID

    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    filters: Dict[str, Any] = Field(
        default_factory=dict,
    )

    query_variants: List[str] = Field(
        default_factory=list,
    )

    max_queries: int = Field(
        default=1,
        ge=1,
        le=10,
    )

    # IMPORTANT:
    # Reranking is opt-in at the plan level as well.
    rerank: bool = False

    expand_query: bool = False

    multi_hop: bool = False

    use_evidence_collection: bool = True

    fallback_strategies: List[RetrievalStrategy] = Field(
        default_factory=list,
    )

    reasoning: str = ""

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    @property
    def use_reranker(self) -> bool:
        return self.rerank


# ============================================================================
# QUERY ANALYSIS
# ============================================================================


class QueryAnalysis(BaseModel):
    """
    Structured query analysis used by Adaptive RAG.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    query: str = ""

    original_query: str = ""

    normalized_query: str = ""

    intent: QueryIntent = QueryIntent.FACTUAL

    complexity: QueryComplexity = QueryComplexity.LOW

    query_type: QueryType = QueryType.HYBRID

    classification_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    terms: List[str] = Field(
        default_factory=list,
    )

    keywords: List[str] = Field(
        default_factory=list,
    )

    phrases: List[str] = Field(
        default_factory=list,
    )

    filters: Dict[str, Any] = Field(
        default_factory=dict,
    )

    requires_retrieval: bool = True

    requires_multiple_documents: bool = False

    requires_broad_search: bool = False

    requires_multi_hop: bool = False

    requires_reranking: bool = False

    requires_multiple_queries: bool = False

    is_question: bool = False

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def normalize_query_fields(self) -> "QueryAnalysis":

        if not self.query:
            if self.normalized_query:
                self.query = self.normalized_query
            elif self.original_query:
                self.query = self.original_query

        if not self.original_query:
            self.original_query = self.query

        if not self.normalized_query:
            self.normalized_query = self.query.strip().lower()

        if (
            self.classification_confidence == 0.0
            and self.confidence != 0.0
        ):
            self.classification_confidence = self.confidence

        elif (
            self.confidence == 0.0
            and self.classification_confidence != 0.0
        ):
            self.confidence = self.classification_confidence

        if not self.terms and self.keywords:
            self.terms = list(self.keywords)

        if not self.keywords and self.terms:
            self.keywords = list(self.terms)

        return self


# ============================================================================
# ROUTING DECISION
# ============================================================================


class RetrievalDecision(BaseModel):
    """
    Low-level retrieval routing decision.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    mode: RetrievalMode = RetrievalMode.HYBRID

    query_type: QueryType = QueryType.HYBRID

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    reason: str = ""

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "RetrievalMode",
    "RetrievalStrategy",
    "QueryType",
    "QueryIntent",
    "QueryComplexity",
    "QueryClassification",
    "QueryRewrite",
    "AdaptiveRAGConfig",
    "DenseSearchResult",
    "SparseSearchResult",
    "HybridSearchResult",
    "RRFResult",
    "SearchResult",
    "RetrieverResult",
    "RetrievalFilters",
    "RetrievalQuery",
    "RetrievedDocument",
    "RetrievalResult",
    "RetrievalResponse",
    "RetrievalPlan",
    "QueryAnalysis",
    "RetrievalDecision",
]

