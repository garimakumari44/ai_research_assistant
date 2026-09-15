from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas.adaptive_rag import AdaptiveRAGResponse
from app.schemas.retrieval import RetrievalResponse


@dataclass(slots=True)
class ExploreContext:
    """
    Internal normalized context used by ExploreService.

    This keeps the API contract separate from the internal orchestration
    contract used by RetrievalService and AdaptiveRAGController.
    """

    query: str

    top_k: int = 5

    retrieval_mode: str = "hybrid"

    adaptive: bool = True

    strategy: str | None = None

    max_iterations: int = 3

    confidence_threshold: float = 0.75

    paper_id: str | None = None

    document_id: str | None = None

    filters: dict[str, Any] = field(default_factory=dict)

    enable_graph: bool = False

    enable_multi_query: bool = False

    enable_correction: bool = True

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExploreResult:
    """
    Internal result produced by ExploreService.

    Exactly one of `retrieval` or `adaptive_rag` is normally populated,
    depending on whether adaptive execution was requested.
    """

    query: str

    retrieval: RetrievalResponse | None = None

    adaptive_rag: AdaptiveRAGResponse | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    duration_ms: float | None = None