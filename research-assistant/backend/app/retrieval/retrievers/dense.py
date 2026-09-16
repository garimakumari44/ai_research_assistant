from __future__ import annotations

from typing import Any

import numpy as np

from app.core.config import settings
from app.indexing.embeddings.generator import EmbeddingGenerator
from app.indexing.vector_store.faiss_index import FAISSIndex
from app.retrieval.interfaces.retriever import Retriever
from app.retrieval.models import DenseSearchResult


class DenseRetriever:
    """
    Dense semantic retriever backed by FAISS.

    Implements the canonical Retriever interface.

    Pipeline:

        query
          ↓
        EmbeddingGenerator
          ↓
        FAISSIndex
          ↓
        DenseSearchResult

    The embedding model is loaded lazily.

    Creating DenseRetriever() does NOT load the BGE model.
    BGE is loaded only when search() actually needs to generate
    a query embedding.

    The retriever returns only retrieval candidates.

    Document resolution is handled by RetrievalPipeline.
    """

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
        vector_store: FAISSIndex | None = None,
    ) -> None:

        # --------------------------------------------------------------
        # Create the embedding generator.
        #
        # EmbeddingGenerator is now lazy, so this does NOT load BGE.
        # --------------------------------------------------------------

        self.embedder = (
            embedder
            or EmbeddingGenerator()
        )

        # --------------------------------------------------------------
        # Embedding dimension
        #
        # Read the dimension from application configuration instead of
        # accessing the embedding model. This prevents BGE/Sentence
        # Transformers from being loaded during DenseRetriever creation.
        # --------------------------------------------------------------

        dimension = settings.EMBEDDING_DIMENSION

        self.vector_store = (
            vector_store
            or FAISSIndex(
                dimension=dimension
            )
        )

    # ======================================================================
    # SEARCH
    # ======================================================================

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[DenseSearchResult]:
        """
        Perform dense semantic retrieval.

        Filters are accepted to satisfy the common Retriever interface.

        Dense filtering itself is not performed here because FAISS only
        knows vector IDs. Metadata filtering is handled by the higher-level
        RetrievalPipeline after document resolution.

        The BGE model is loaded lazily when embed_query() is called.
        """

        del filters

        # ------------------------------------------------------------------
        # Validate query
        # ------------------------------------------------------------------

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        # ------------------------------------------------------------------
        # Validate top_k
        # ------------------------------------------------------------------

        if not isinstance(top_k, int):
            return []

        if top_k <= 0:
            return []

        # ------------------------------------------------------------------
        # Generate embedding
        #
        # THIS is where BGE may be loaded for the first time.
        # ------------------------------------------------------------------

        try:
            query_embedding = self.embedder.embed_query(
                query
            )
        except Exception:
            return []

        if query_embedding is None:
            return []

        # ------------------------------------------------------------------
        # Convert embedding
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
            return []

        if embedding.size == 0:
            return []

        if not np.all(
            np.isfinite(embedding)
        ):
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

        # ------------------------------------------------------------------
        # Validate dimension
        #
        # Use configuration rather than the embedding model so this check
        # does not trigger model initialization.
        # ------------------------------------------------------------------

        expected_dimension = settings.EMBEDDING_DIMENSION

        if vector.size != expected_dimension:
            return []

        # ------------------------------------------------------------------
        # FAISS search
        # ------------------------------------------------------------------

        try:
            raw_results = self.vector_store.search(
                vector,
                top_k,
            )
        except Exception:
            return []

        if not raw_results:
            return []

        # ------------------------------------------------------------------
        # Convert FAISS results
        # ------------------------------------------------------------------

        results: list[DenseSearchResult] = []

        for raw_result in raw_results:

            if not isinstance(
                raw_result,
                dict,
            ):
                continue

            raw_id = raw_result.get("id")
            raw_score = raw_result.get("score")

            if raw_id is None:
                continue

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

            results.append(
                DenseSearchResult(
                    id=str(raw_id),
                    score=score,
                )
            )

            if len(results) >= top_k:
                break

        return results

    # ======================================================================
    # ASYNC COMPATIBILITY API
    # ======================================================================

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[DenseSearchResult]:
        """
        Async-compatible Retriever API.

        Dense retrieval is currently synchronous/CPU-bound, so this simply
        delegates to search().
        """

        return self.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )


__all__ = [
    "DenseRetriever",
]