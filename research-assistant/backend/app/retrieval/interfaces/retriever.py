from __future__ import annotations

from typing import Any, Protocol, Sequence

from app.retrieval.models import (
    DenseSearchResult,
    SparseSearchResult,
)


class Retriever(Protocol):
    """
    Canonical interface for low-level retrieval engines.

    Implementations include:

        - DenseRetriever
        - BM25Retriever
        - future GraphRetriever
        - future database retrievers

    The retriever is responsible only for retrieving ranked candidates.

    It does NOT:

        - resolve IDs into full documents
        - perform reranking
        - perform RRF
        - build RetrievalResponse

    Those responsibilities belong to higher-level components.
    """

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[
        DenseSearchResult | SparseSearchResult
    ]:
        """
        Retrieve ranked candidates.

        Args:
            query:
                User search query.

            top_k:
                Maximum number of candidates.

            filters:
                Optional metadata filters.

        Returns:
            Ranked low-level retrieval results.
        """
        ...

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[
        DenseSearchResult | SparseSearchResult
    ]:
        """
        Async-compatible retrieval API.

        Implementations that are naturally synchronous may simply
        delegate to search().
        """
        ...


__all__ = [
    "Retriever",
]