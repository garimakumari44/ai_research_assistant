from __future__ import annotations

from typing import Any, Sequence

from app.retrieval.models import SearchResult
from app.retrieval.retrievers.base import Retriever


class HybridRetriever(Retriever):
    """
    Hybrid retriever combining lexical and dense retrieval.

    Uses Reciprocal Rank Fusion (RRF):

        RRF(d) = Σ 1 / (k + rank(d))

    RRF combines rankings without requiring lexical and dense
    similarity scores to be on the same numerical scale.
    """

    name = "hybrid"

    def __init__(
        self,
        *,
        keyword_retriever: Retriever,
        dense_retriever: Retriever,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than zero")

        self.keyword_retriever = keyword_retriever
        self.dense_retriever = dense_retriever
        self.rrf_k = rrf_k

    # ========================================================================
    # PRIMARY RETRIEVAL API
    # ========================================================================

    def search(
        self,
        query: str,
        top_k: int = 10,
        *,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[SearchResult]:
        """
        Execute keyword and dense retrieval, then fuse their rankings.

        The interface is intentionally synchronous because the canonical
        Retriever contract is synchronous.
        """

        if not query or not query.strip():
            return []

        if top_k <= 0:
            return []

        retrieval_k = max(top_k * 2, top_k)

        keyword_results = self.keyword_retriever.search(
            query,
            top_k=retrieval_k,
            filters=filters,
        )

        dense_results = self.dense_retriever.search(
            query,
            top_k=retrieval_k,
            filters=filters,
        )

        fused = self._fuse(
            keyword_results=keyword_results,
            dense_results=dense_results,
        )

        return fused[:top_k]

    # ========================================================================
    # RRF FUSION
    # ========================================================================

    def _fuse(
        self,
        *,
        keyword_results: Sequence[SearchResult],
        dense_results: Sequence[SearchResult],
    ) -> list[SearchResult]:
        """
        Fuse ranked keyword and dense results using Reciprocal Rank Fusion.
        """

        scores: dict[str, float] = {}
        results: dict[str, SearchResult] = {}

        self._add_ranked_results(
            ranked_results=keyword_results,
            scores=scores,
            results=results,
        )

        self._add_ranked_results(
            ranked_results=dense_results,
            scores=scores,
            results=results,
        )

        ordered_ids = sorted(
            scores,
            key=lambda chunk_id: scores[chunk_id],
            reverse=True,
        )

        fused_results: list[SearchResult] = []

        for chunk_id in ordered_ids:
            result = results[chunk_id]
            rrf_score = scores[chunk_id]

            fused_results.append(
                SearchResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    content=result.content,
                    score=rrf_score,
                    metadata={
                        **(result.metadata or {}),
                        "retrieval": "hybrid",
                        "rrf_score": rrf_score,
                    },
                )
            )

        return fused_results

    def _add_ranked_results(
        self,
        *,
        ranked_results: Sequence[SearchResult],
        scores: dict[str, float],
        results: dict[str, SearchResult],
    ) -> None:
        """
        Add one ranked result list to the RRF accumulator.
        """

        for rank, result in enumerate(ranked_results, start=1):
            chunk_id = str(result.chunk_id)

            scores[chunk_id] = (
                scores.get(chunk_id, 0.0)
                + 1.0 / (self.rrf_k + rank)
            )

            results.setdefault(chunk_id, result)


__all__ = ["HybridRetriever"]