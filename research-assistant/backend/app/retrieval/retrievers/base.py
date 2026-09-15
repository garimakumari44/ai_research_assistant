from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from app.retrieval.models import SearchResult


class Retriever(ABC):
    """
    Unified synchronous interface for all retrieval implementations.

    Concrete retrievers implement `search()` and return canonical
    `SearchResult` objects.
    """

    name: str = "retriever"

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 10,
        *,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[SearchResult]:
        """
        Retrieve the most relevant results for a query.
        """
        raise NotImplementedError

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[SearchResult]:
        """
        Compatibility alias for search().
        """
        return self.search(
            query,
            top_k=top_k,
            filters=filters,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}"
            f")"
        )


__all__ = ["Retriever"]