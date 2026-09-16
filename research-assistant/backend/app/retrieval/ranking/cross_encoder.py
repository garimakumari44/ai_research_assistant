
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

    The implementation is intentionally lazy:

        CrossEncoderReranker()
            ↓
        no PyTorch import
            ↓
        no SentenceTransformers model
            ↓
        lightweight application startup

    The heavy ML stack is loaded only when reranking is actually
    requested through the `rerank()` method.
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

        # --------------------------------------------------------------
        # Device
        # --------------------------------------------------------------
        #
        # IMPORTANT:
        # Do NOT import torch here.
        #
        # Importing torch during application startup can consume a
        # significant amount of memory even when the CrossEncoder is
        # never actually used.
        #
        # If a device is explicitly supplied, respect it.
        # Otherwise default to CPU.
        #
        # The actual model remains lazy-loaded below.
        #

        self.device = device or "cpu"

        # --------------------------------------------------------------
        # Lazy model
        # --------------------------------------------------------------

        self._model = None

    # ==================================================================
    # MODEL
    # ==================================================================

    @property
    def model(self):
        """
        Lazy-load the SentenceTransformers CrossEncoder model.

        SentenceTransformers and PyTorch are intentionally imported
        only when the model is actually requested.

        This keeps the normal API startup and retrieval construction
        lightweight.
        """

        if self._model is None:
            logger.info(
                "Loading CrossEncoder model '%s' on %s",
                self.model_name,
                self.device,
            )

            from sentence_transformers import CrossEncoder

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

        # --------------------------------------------------------------
        # Validate query
        # --------------------------------------------------------------

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query must not be empty."
            )

        # --------------------------------------------------------------
        # Normalize chunks
        # --------------------------------------------------------------

        if chunks is None:
            chunks = []

        chunks = list(chunks)

        # --------------------------------------------------------------
        # Empty result
        # --------------------------------------------------------------

        if not chunks:
            return RankingResult(
                query=query,
                chunks=[],
                total_candidates=0,
                returned_chunks=0,
                reranker=self.model_name,
                processing_time_ms=0.0,
            )

        # --------------------------------------------------------------
        # Determine top-k
        # --------------------------------------------------------------

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
        #
        # Accessing self.model here is the first point at which
        # SentenceTransformers/PyTorch is loaded.
        #

        scores = self.model.predict(
            pairs,
            batch_size=retrieval_config.RERANK_BATCH_SIZE,
            show_progress_bar=False,
        )

        # --------------------------------------------------------------
        # Convert scores into RankedChunk objects
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

        # --------------------------------------------------------------
        # Timing
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Return canonical result
        # --------------------------------------------------------------

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


