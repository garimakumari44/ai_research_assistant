from __future__ import annotations

from typing import Any

from app.indexing.embeddings.generator import EmbeddingGenerator
from app.knowledge.indexing.vector import VectorIndexer
from app.retrieval.advanced.models import RetrievalSource
from app.retrieval.models import RetrievedDocument
from app.retrieval.sources.base import BaseRetrievalSource


class VectorSource(BaseRetrievalSource):
    """
    Dense vector retrieval source.

    Architecture:

        query
          ↓
        EmbeddingGenerator
          ↓
        VectorIndexer
          ↓
        FAISS
          ↓
        VectorSearchResult
          ↓
        RetrievedDocument

    The VectorIndexer remains the application-level owner of the
    vector index. This source is only an adapter for the Explore
    retrieval layer.
    """

    source_type = RetrievalSource.VECTOR_DB

    def __init__(
        self,
        vector_index: VectorIndexer,
        embedder: EmbeddingGenerator | None = None,
    ) -> None:
        super().__init__()

        self.vector_index = vector_index

        self.embedder = (
            embedder
            or EmbeddingGenerator()
        )

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """
        Perform dense semantic retrieval.
        """

        del filters

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
            embedding = self.embedder.embed_query(
                query
            )
        except Exception:
            return []

        if embedding is None:
            return []

        try:
            results = await self.vector_index.search(
                embedding,
                top_k=top_k,
            )
        except Exception:
            return []

        documents: list[RetrievedDocument] = []

        for result in results:
            document = RetrievedDocument(
                id=str(result.chunk_id),
                content="",
                source=self.source_type.value,
                score=float(result.score),
                metadata=dict(
                    result.metadata or {}
                ),
            )

            documents.append(document)

        return documents