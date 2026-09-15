"""
Cross-Encoder reranker implementation.

Uses SentenceTransformers CrossEncoder models such as:

- BAAI/bge-reranker-base
- cross-encoder/ms-marco-MiniLM-L-6-v2

Contract
--------
Input:
    query: str
    chunks: list[RetrievedChunk]

Output:
    RankingResult

The reranker owns ranking logic only. It does not perform retrieval,
document resolution, metadata filtering, or API conversion.
"""

from __future__ import annotations

import logging
import time

import torch
from sentence_transformers import CrossEncoder

from app.retrieval.config import retrieval_config
from app.retrieval.ranking.models import (
    RankedChunk,
    RankingResult,
    RetrievedChunk,
)

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-encoder based reranker.

    Scores (query, document) pairs and sorts documents by relevance.

    Contract:

        query
            +
        list[RetrievedChunk]
            ↓
        CrossEncoder
            ↓
        RankingResult
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ) -> None:
        self.model_name = (
            model_name
            or retrieval_config.CROSS_ENCODER_MODEL
        )

        self.device = (
            device
            or (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        self._model: CrossEncoder | None = None

    # ==================================================================
    # MODEL
    # ==================================================================

    @property
    def model(self) -> CrossEncoder:
        """
        Lazy-load the CrossEncoder model.
        """

        if self._model is None:
            logger.info(
                "Loading CrossEncoder model '%s' on %s",
                self.model_name,
                self.device,
            )

            self._model = CrossEncoder(
                self.model_name,
                device=self.device,
            )

        return self._model

    # ==================================================================
    # RERANK
    # ==================================================================

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> RankingResult:
        """
        Rerank retrieved chunks using the CrossEncoder.

        Parameters
        ----------
        query:
            Retrieval query.

        chunks:
            Canonical RetrievedChunk objects.

        top_k:
            Maximum number of chunks returned.

        Returns
        -------
        RankingResult
            Canonical ranking result containing RankedChunk objects.
        """

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query must not be empty."
            )

        if chunks is None:
            chunks = []

        chunks = list(chunks)

        if not chunks:
            return RankingResult(
                query=query,
                chunks=[],
                total_candidates=0,
                returned_chunks=0,
                reranker=self.model_name,
                processing_time_ms=0.0,
            )

        if top_k is None:
            top_k = retrieval_config.FINAL_TOP_K

        top_k = max(
            1,
            min(
                int(top_k),
                len(chunks),
            ),
        )

        start = time.perf_counter()

        # --------------------------------------------------------------
        # Build query/document pairs
        # --------------------------------------------------------------

        pairs = [
            (
                query,
                chunk.text,
            )
            for chunk in chunks
        ]

        # --------------------------------------------------------------
        # CrossEncoder prediction
        # --------------------------------------------------------------

        scores = self.model.predict(
            pairs,
            batch_size=retrieval_config.RERANK_BATCH_SIZE,
            show_progress_bar=False,
        )

        # --------------------------------------------------------------
        # Normalize scores
        # --------------------------------------------------------------

        ranked_chunks: list[RankedChunk] = []

        for chunk, score in zip(
            chunks,
            scores,
        ):
            ranked_chunks.append(
                RankedChunk(
                    **chunk.model_dump(),
                    rerank_score=float(score),
                )
            )

        # --------------------------------------------------------------
        # Sort by reranker score
        # --------------------------------------------------------------

        ranked_chunks.sort(
            key=lambda chunk: (
                chunk.rerank_score
            ),
            reverse=True,
        )

        # --------------------------------------------------------------
        # Assign rank
        # --------------------------------------------------------------

        for rank, chunk in enumerate(
            ranked_chunks,
            start=1,
        ):
            chunk.rank = rank

        # --------------------------------------------------------------
        # Apply top-k
        # --------------------------------------------------------------

        ranked_chunks = ranked_chunks[
            :top_k
        ]

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            "CrossEncoder reranked %d candidates "
            "and returned %d results in %.2f ms. "
            "model=%s",
            len(chunks),
            len(ranked_chunks),
            elapsed_ms,
            self.model_name,
        )

        return RankingResult(
            query=query,
            chunks=ranked_chunks,
            total_candidates=len(chunks),
            returned_chunks=len(ranked_chunks),
            reranker=self.model_name,
            processing_time_ms=elapsed_ms,
        )


__all__ = [
    "CrossEncoderReranker",
]