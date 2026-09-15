"""
Base abstractions for retrieval reranking.

Rerankers receive candidates produced by the retrieval layer and
return those candidates ordered by relevance to the query.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field


class RerankCandidate(BaseModel):
    """
    A candidate document/chunk returned by an upstream retriever.

    The model intentionally keeps metadata flexible because different
    retrievers may return different document-level information.
    """

    model_config = ConfigDict(
        extra="allow"
    )

    id: str

    content: str

    score: float = 0.0

    original_score: float | None = None

    document_id: str | None = None

    chunk_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    rank: int | None = None

    original_rank: int | None = None


class RerankResult(BaseModel):
    """
    Result returned by a reranker.
    """

    candidate: RerankCandidate

    score: float

    rank: int

    original_rank: int | None = None

    reason: str | None = None


class BaseReranker(ABC):
    """
    Abstract interface for all reranking implementations.

    Implementations can use:

        - lexical scoring
        - cross-encoder models
        - hosted reranking APIs
        - LLM-based relevance scoring
        - custom domain-specific models
    """

    name: str = "base"

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: Sequence[RerankCandidate],
        *,
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """
        Rerank retrieval candidates against a query.

        Args:
            query:
                The original or rewritten user query.

            candidates:
                Candidates returned by the retrieval layer.

            top_k:
                Optional maximum number of candidates to return.

        Returns:
            Candidates ordered from most relevant to least relevant.
        """
        raise NotImplementedError

    def _prepare_candidates(
        self,
        candidates: Sequence[RerankCandidate],
    ) -> list[RerankCandidate]:
        """
        Normalize candidate ranking information before reranking.
        """

        prepared: list[RerankCandidate] = []

        for index, candidate in enumerate(candidates, start=1):
            candidate_copy = candidate.model_copy(
                deep=True
            )

            if candidate_copy.original_score is None:
                candidate_copy.original_score = (
                    candidate_copy.score
                )

            if candidate_copy.original_rank is None:
                candidate_copy.original_rank = (
                    candidate_copy.rank or index
                )

            prepared.append(candidate_copy)

        return prepared

    @staticmethod
    def _limit_results(
        results: list[RerankResult],
        top_k: int | None,
    ) -> list[RerankResult]:
        """
        Apply the requested result limit and normalize ranks.
        """

        if top_k is not None:
            top_k = max(0, top_k)
            results = results[:top_k]

        for index, result in enumerate(
            results,
            start=1,
        ):
            result.rank = index

        return results