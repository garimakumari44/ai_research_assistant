
from __future__ import annotations

import re
from typing import Any, Sequence

from app.retrieval.retrievers.base import Retriever
from app.retrieval.models import SearchResult


class KeywordRetriever(Retriever):
    """
    Keyword-based retriever.

    The retriever is repository-agnostic. A repository may provide a
    `keyword_search()` method that performs the actual lexical search.

    The canonical retrieval interface is:

        search(
            query,
            top_k=...,
            filters=...
        ) -> Sequence[SearchResult]

    This implementation can later be connected to PostgreSQL full-text
    search, BM25, or another lexical backend without changing the public
    retrieval contract.
    """

    name = "keyword"

    def __init__(
        self,
        repository: Any | None = None,
    ) -> None:
        self.repository = repository

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
        Retrieve keyword-matched documents.

        The repository is expected to expose:

            keyword_search(
                query=query,
                top_k=top_k,
                filters=filters,
            )

        The repository method may return dictionaries, ORM objects, or
        already-normalized SearchResult objects.
        """

        if not query or not query.strip():
            return []

        if top_k <= 0:
            return []

        if self.repository is None:
            return []

        search_method = getattr(
            self.repository,
            "keyword_search",
            None,
        )

        if search_method is None:
            return []

        rows = search_method(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        return self._normalize_results(rows)

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    def _normalize_results(
        self,
        rows: Sequence[Any] | None,
    ) -> list[SearchResult]:
        """
        Convert repository results into canonical SearchResult objects.
        """

        if not rows:
            return []

        results: list[SearchResult] = []

        for row in rows:
            if isinstance(row, SearchResult):
                results.append(row)
                continue

            result = self._row_to_result(row)

            if result is not None:
                results.append(result)

        return results

    @staticmethod
    def _row_to_result(
        row: Any,
    ) -> SearchResult | None:
        """
        Convert a dictionary or object returned by the repository into
        a canonical SearchResult.
        """

        if isinstance(row, dict):
            chunk_id = row.get("chunk_id")
            document_id = row.get("document_id")
            content = row.get("content", "")
            score = row.get("score", 0.0)
            metadata = row.get("metadata", {})

        else:
            chunk_id = getattr(
                row,
                "chunk_id",
                None,
            )

            document_id = getattr(
                row,
                "document_id",
                None,
            )

            content = getattr(
                row,
                "content",
                "",
            )

            score = getattr(
                row,
                "score",
                0.0,
            )

            metadata = getattr(
                row,
                "metadata",
                {})

        if chunk_id is None or document_id is None:
            return None

        if not isinstance(metadata, dict):
            try:
                metadata = dict(metadata or {})
            except (TypeError, ValueError):
                metadata = {}

        return SearchResult(
            chunk_id=str(chunk_id),
            document_id=str(document_id),
            content=str(content),
            score=float(score or 0.0),
            metadata=metadata,
        )

    # ========================================================================
    # TOKENIZATION
    # ========================================================================

    @staticmethod
    def tokenize(
        text: str,
    ) -> set[str]:
        """
        Tokenize text for lightweight lexical processing.

        This utility is useful for tests and future local lexical scoring.
        """

        if not text:
            return set()

        return {
            token.lower()
            for token in re.findall(
                r"\b\w+\b",
                text,
            )
            if len(token) > 1
        }


__all__ = ["KeywordRetriever"]

