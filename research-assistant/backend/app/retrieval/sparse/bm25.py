from __future__ import annotations

from typing import Any

import numpy as np

from app.knowledge.indexing.keyword import KeywordIndexer
from app.retrieval.models import SparseSearchResult


class BM25Retriever:
    """
    Sparse keyword retriever backed by the shared KeywordIndexer.

    Architecture:

        query
          ↓
        KeywordIndexer
          ↓
        BM25
          ↓
        SparseSearchResult

    The retriever deliberately does not instantiate BM25Okapi.

    BM25 is an implementation detail of KeywordIndexer.

    This keeps the retrieval layer independent from the concrete
    keyword-search backend and allows the underlying implementation
    to later be replaced by PostgreSQL FTS, Elasticsearch, OpenSearch,
    or another search backend.
    """

    def __init__(
        self,
        keyword_index: KeywordIndexer | None = None,
    ) -> None:
        """
        Initialize the sparse retriever.

        Args:
            keyword_index:
                Shared application-level keyword index.

        Raises:
            ValueError:
                If no shared KeywordIndexer is supplied.

        Important:
            A private keyword index is intentionally NOT created here.
            Retrieval must use the KeywordIndexer owned by IndexRegistry.
        """

        if keyword_index is None:
            raise ValueError(
                "keyword_index must be provided. "
                "BM25Retriever must use the shared KeywordIndexer "
                "owned by IndexRegistry."
            )

        self.keyword_index = keyword_index

    # ==================================================================
    # PUBLIC SEARCH API
    # ==================================================================

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SparseSearchResult]:
        """
        Perform sparse keyword retrieval.

        Args:
            query:
                Natural-language search query.

            top_k:
                Maximum number of results.

            filters:
                Optional metadata filters.

        Returns:
            SparseSearchResult objects ordered by keyword relevance.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if not isinstance(top_k, int):
            return []

        if top_k <= 0:
            return []

        try:
            indexed_results = await self.keyword_index.search(
                query=query,
                top_k=top_k,
                filters=filters,
            )
        except Exception:
            return []

        if not indexed_results:
            return []

        results: list[SparseSearchResult] = []

        for indexed_result in indexed_results:
            if indexed_result is None:
                continue

            # ----------------------------------------------------------
            # Resolve chunk ID
            # ----------------------------------------------------------

            chunk_id = getattr(
                indexed_result,
                "chunk_id",
                None,
            )

            if chunk_id is None:
                continue

            result_id = str(chunk_id).strip()

            if not result_id:
                continue

            # ----------------------------------------------------------
            # Resolve score
            # ----------------------------------------------------------

            raw_score = getattr(
                indexed_result,
                "score",
                None,
            )

            try:
                score = float(raw_score)
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                continue

            if not np.isfinite(score):
                continue

            # ----------------------------------------------------------
            # Build retrieval-domain result
            # ----------------------------------------------------------

            try:
                result = SparseSearchResult(
                    id=result_id,
                    score=score,
                )
            except Exception:
                continue

            results.append(result)

            if len(results) >= top_k:
                break

        return results

    # ==================================================================
    # ASYNC RETRIEVE COMPATIBILITY API
    # ==================================================================

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SparseSearchResult]:
        """
        Compatibility API for the canonical retriever interface.
        """

        return await self.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )


__all__ = [
    "BM25Retriever",
]