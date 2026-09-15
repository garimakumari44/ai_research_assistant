from __future__ import annotations

from dataclasses import dataclass

from .keyword import KeywordIndexer
from .vector import VectorIndexer


@dataclass(slots=True)
class IndexRegistry:
    """
    Shared registry for all knowledge indexes.

    The registry owns the actual index instances and ensures that
    indexing and retrieval use the same in-memory indexes.

    Architecture:

        IndexRegistry
          ├── VectorIndexer
          └── KeywordIndexer

    Later, these implementations can be replaced with persistent
    backends such as pgvector and PostgreSQL FTS without changing
    the retrieval architecture.
    """

    vector: VectorIndexer
    keyword: KeywordIndexer

    @classmethod
    def create(
        cls,
        vector: VectorIndexer | None = None,
        keyword: KeywordIndexer | None = None,
    ) -> "IndexRegistry":
        """
        Create a registry with shared index instances.

        Optional instances can be injected for testing or for
        replacing the underlying implementations.
        """

        return cls(
            vector=vector or VectorIndexer(),
            keyword=keyword or KeywordIndexer(),
        )

    async def clear(self) -> None:
        """
        Clear all registered indexes.
        """

        await self.vector.clear()
        await self.keyword.clear()

    async def get_stats(self) -> dict[str, int]:
        """
        Return statistics for all registered indexes.
        """

        return {
            "vector_count": await self.vector.count(),
            "keyword_count": await self.keyword.count(),
        }

    async def exists(self, chunk_id) -> bool:
        """
        Check whether a chunk exists in either index.
        """

        return (
            await self.vector.exists(chunk_id)
            or await self.keyword.exists(chunk_id)
        )