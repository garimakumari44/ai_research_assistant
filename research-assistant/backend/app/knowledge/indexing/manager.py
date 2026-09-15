from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
from uuid import UUID

from .keyword import KeywordIndexItem
from .vector import VectorIndexItem
from .registry import IndexRegistry


@dataclass(slots=True)
class IndexResult:
    """
    Result returned after indexing a chunk.
    """

    chunk_id: UUID
    vector_indexed: bool
    keyword_indexed: bool


class IndexManager:
    """
    Coordinates all knowledge indexes through the shared IndexRegistry.

    Architecture:

        IndexManager
             │
             ▼
        IndexRegistry
          ├── VectorIndexer
          └── KeywordIndexer

    The registry must be shared with the retrieval layer so that
    indexing and retrieval operate on the same underlying indexes.
    """

    def __init__(
        self,
        index_registry: IndexRegistry,
    ) -> None:
        self.index_registry = index_registry

        # Convenient references to the shared indexes.
        self.vector_indexer = index_registry.vector
        self.keyword_indexer = index_registry.keyword

    async def index_chunk(
        self,
        chunk_id: UUID,
        text: str,
        embedding: Sequence[float],
        metadata: dict[str, Any] | None = None,
    ) -> IndexResult:
        """
        Index a chunk in both shared indexes.
        """

        metadata = metadata or {}

        await self.vector_indexer.upsert(
            chunk_id=chunk_id,
            vector=embedding,
            metadata=metadata,
        )

        await self.keyword_indexer.upsert(
            chunk_id=chunk_id,
            text=text,
            metadata=metadata,
        )

        return IndexResult(
            chunk_id=chunk_id,
            vector_indexed=True,
            keyword_indexed=True,
        )

    async def index_chunks(
        self,
        chunks: Sequence[dict[str, Any]],
    ) -> list[IndexResult]:
        """
        Index multiple chunks.

        Each chunk must contain:

            chunk_id
            text
            embedding

        Optional:

            metadata
        """

        results: list[IndexResult] = []

        for chunk in chunks:
            result = await self.index_chunk(
                chunk_id=chunk["chunk_id"],
                text=chunk["text"],
                embedding=chunk["embedding"],
                metadata=chunk.get("metadata"),
            )

            results.append(result)

        return results

    async def delete_chunk(self, chunk_id: UUID) -> bool:
        """
        Delete a chunk from all shared indexes.
        """

        vector_deleted = await self.vector_indexer.delete(chunk_id)
        keyword_deleted = await self.keyword_indexer.delete(chunk_id)

        return vector_deleted or keyword_deleted

    async def exists(self, chunk_id: UUID) -> bool:
        """
        Check whether a chunk exists in either shared index.
        """

        vector_exists = await self.vector_indexer.exists(chunk_id)
        keyword_exists = await self.keyword_indexer.exists(chunk_id)

        return vector_exists or keyword_exists

    async def get_stats(self) -> dict[str, int]:
        """
        Return statistics for the shared indexes.
        """

        return await self.index_registry.get_stats()

    async def clear(self) -> None:
        """
        Clear all shared indexes.
        """

        await self.index_registry.clear()


__all__ = [
    "IndexManager",
    "IndexResult",
]