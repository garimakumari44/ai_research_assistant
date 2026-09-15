from __future__ import annotations

import logging
from typing import List

import numpy as np

from app.knowledge.indexing.vector import VectorIndexer
from app.indexing.embeddings.generator import EmbeddingGenerator
from app.retrieval.models import DenseSearchResult


logger = logging.getLogger(__name__)


class DenseRetriever:
    """
    Dense semantic retriever backed by the shared VectorIndexer.

    Architecture:

        query
          ↓
        EmbeddingGenerator
          ↓
        VectorIndexer
          ↓
        vector search
          ↓
        DenseSearchResult
    """

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
        vector_index: VectorIndexer | None = None,
    ) -> None:

        self.embedder = (
            embedder
            if embedder is not None
            else EmbeddingGenerator()
        )

        self.vector_index = vector_index

        if self.vector_index is None:

            raise ValueError(
                "vector_index must be provided. "
                "DenseRetriever must use the shared VectorIndexer "
                "owned by IndexRegistry."
            )

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    async def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[DenseSearchResult]:

        if not isinstance(
            query,
            str,
        ):
            return []

        query = query.strip()

        if not query:
            return []

        if not isinstance(
            top_k,
            int,
        ):
            return []

        if top_k <= 0:
            return []

        # ------------------------------------------------------------------
        # Generate embedding
        # ------------------------------------------------------------------

        try:

            query_embedding = (
                self.embedder.generate(
                    query
                )
            )

        except Exception:

            logger.exception(
                "Dense retrieval embedding generation failed."
            )

            return []

        if query_embedding is None:
            return []

        # ------------------------------------------------------------------
        # Convert to NumPy
        # ------------------------------------------------------------------

        try:

            embedding = np.asarray(
                query_embedding,
                dtype=np.float32,
            )

        except (
            TypeError,
            ValueError,
        ):

            logger.exception(
                "Unable to convert query embedding to NumPy."
            )

            return []

        if embedding.size == 0:
            return []

        if not np.all(
            np.isfinite(
                embedding
            )
        ):

            logger.error(
                "Query embedding contains non-finite values."
            )

            return []

        # ------------------------------------------------------------------
        # Normalize shape
        # ------------------------------------------------------------------

        if embedding.ndim == 1:

            vector = embedding

        elif embedding.ndim == 2:

            if embedding.shape[0] != 1:
                return []

            vector = embedding[0]

        else:

            return []

        if vector.size == 0:
            return []

        if not np.all(
            np.isfinite(
                vector
            )
        ):
            return []

        vector = np.ascontiguousarray(
            vector,
            dtype=np.float32,
        )

        # ------------------------------------------------------------------
        # Shared VectorIndexer
        # ------------------------------------------------------------------

        try:

            search_results = (
                await self.vector_index.search(
                    vector,
                    top_k=top_k,
                )
            )

        except Exception:

            logger.exception(
                "Shared VectorIndexer search failed."
            )

            return []

        if not search_results:
            return []

        # ------------------------------------------------------------------
        # Convert VectorSearchResult → DenseSearchResult
        # ------------------------------------------------------------------

        results: List[
            DenseSearchResult
        ] = []

        for result in search_results:

            if result is None:
                continue

            raw_chunk_id = getattr(
                result,
                "chunk_id",
                None,
            )

            if raw_chunk_id is None:

                raw_chunk_id = getattr(
                    result,
                    "id",
                    None,
                )

            if raw_chunk_id is None:
                continue

            chunk_id = str(
                raw_chunk_id
            ).strip()

            if not chunk_id:
                continue

            raw_score = getattr(
                result,
                "score",
                None,
            )

            try:

                score = float(
                    raw_score
                )

            except (
                TypeError,
                ValueError,
                OverflowError,
            ):

                continue

            if not np.isfinite(
                score
            ):
                continue

            try:

                dense_result = (
                    DenseSearchResult(
                        id=chunk_id,
                        score=score,
                    )
                )

            except Exception:

                logger.exception(
                    "Failed to create DenseSearchResult "
                    "for chunk=%s",
                    chunk_id,
                )

                continue

            results.append(
                dense_result
            )

            if len(results) >= top_k:
                break

        return results


__all__ = [
    "DenseRetriever",
]