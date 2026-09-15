from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable
from uuid import UUID

from rank_bm25 import BM25Okapi


@dataclass(slots=True)
class KeywordIndexItem:
    """
    Represents one item stored in the keyword index.

    Attributes:
        chunk_id:
            Stable identifier of the indexed chunk.

        text:
            Original chunk text used for keyword retrieval.

        metadata:
            Application-level metadata associated with the chunk.
    """

    chunk_id: UUID
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KeywordSearchResult:
    """
    Result returned by keyword/BM25 search.

    Attributes:
        chunk_id:
            Identifier of the matched chunk.

        score:
            BM25 relevance score.

        metadata:
            Metadata associated with the matched chunk.
    """

    chunk_id: UUID
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class KeywordIndexer:
    """
    Application-level keyword/full-text index abstraction.

    The index owns the searchable keyword state and exposes a stable
    application-level interface to the retrieval layer.

    BM25 is currently used as the local search implementation.

    Architecture:

        KeywordIndexer
              |
              v
          BM25Okapi

    The retrieval layer depends only on KeywordIndexer and therefore
    does not need to know whether the underlying implementation is:

        - BM25
        - PostgreSQL FTS
        - Elasticsearch
        - OpenSearch
        - another search backend

    The `_items` dictionary is the authoritative application-level
    state. The BM25 index is rebuilt from that state whenever the
    corpus changes.

    This implementation is appropriate for the current in-memory
    development backend. For large production corpora, the same
    interface can later be backed by PostgreSQL FTS or a dedicated
    search engine.
    """

    def __init__(self) -> None:
        """
        Initialize an empty keyword index.
        """

        self._items: dict[str, KeywordIndexItem] = {}

        # BM25 search index.

        self._bm25: BM25Okapi | None = None

        # IDs in exactly the same order as the BM25 corpus.

        self._ordered_ids: list[str] = []

        # Tokenized corpus corresponding to `_ordered_ids`.

        self._tokenized_corpus: list[list[str]] = []

    # ==================================================================
    # UPSERT
    # ==================================================================

    async def upsert(
        self,
        chunk_id: UUID,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> KeywordIndexItem:
        """
        Insert or replace a keyword index item.

        The application-level item is authoritative. The BM25 index
        is rebuilt after the item is updated.
        """

        normalized_chunk_id = self._validate_chunk_id(chunk_id)
        normalized_text = self._validate_text(text)

        item = KeywordIndexItem(
            chunk_id=normalized_chunk_id,
            text=normalized_text,
            metadata=dict(metadata or {}),
        )

        self._items[str(normalized_chunk_id)] = item

        self._rebuild()

        return item

    # ==================================================================
    # UPSERT MANY
    # ==================================================================

    async def upsert_many(
        self,
        items: list[KeywordIndexItem],
    ) -> list[KeywordIndexItem]:
        """
        Insert or replace multiple keyword index items.

        The BM25 index is rebuilt only once after all items have been
        updated.
        """

        if items is None:
            raise ValueError(
                "items must not be None"
            )

        normalized_items: list[KeywordIndexItem] = []

        for item in items:
            if not isinstance(item, KeywordIndexItem):
                raise TypeError(
                    "upsert_many() expects KeywordIndexItem instances"
                )

            normalized_chunk_id = self._validate_chunk_id(
                item.chunk_id
            )

            normalized_text = self._validate_text(
                item.text
            )

            normalized_item = KeywordIndexItem(
                chunk_id=normalized_chunk_id,
                text=normalized_text,
                metadata=dict(item.metadata or {}),
            )

            normalized_items.append(normalized_item)

        for item in normalized_items:
            self._items[str(item.chunk_id)] = item

        if normalized_items:
            self._rebuild()

        return normalized_items

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[KeywordSearchResult]:
        """
        Perform keyword/BM25 similarity search.

        Args:
            query:
                User search query.

            top_k:
                Maximum number of results to return.

            filters:
                Optional metadata filters.

        Returns:
            KeywordSearchResult objects ordered by descending BM25
            relevance score.

        Notes:
            The BM25 index is searched first. Metadata filters are then
            applied to the candidates while preserving relevance order.
        """

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string"
            )

        query = query.strip()

        if not query:
            return []

        if not isinstance(top_k, int):
            raise TypeError(
                "top_k must be an integer"
            )

        if top_k <= 0:
            return []

        if not self._items:
            return []

        if self._bm25 is None:
            return []

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # BM25 returns one score per item in exactly the same order as
        # `_ordered_ids`.

        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        results: list[KeywordSearchResult] = []

        for index in ranked_indexes:
            if len(results) >= top_k:
                break

            if index >= len(self._ordered_ids):
                continue

            score = float(scores[index])

            # Ignore invalid numerical values.

            if not self._is_finite(score):
                continue

            chunk_id_string = self._ordered_ids[index]

            item = self._items.get(chunk_id_string)

            if item is None:
                continue

            if filters and not self._matches_filters(
                item,
                filters,
            ):
                continue

            results.append(
                KeywordSearchResult(
                    chunk_id=item.chunk_id,
                    score=score,
                    metadata=dict(item.metadata),
                )
            )

        return results

    # ==================================================================
    # GET
    # ==================================================================

    async def get(
        self,
        chunk_id: UUID,
    ) -> KeywordIndexItem | None:
        """
        Retrieve one indexed keyword item.
        """

        normalized_chunk_id = self._validate_chunk_id(
            chunk_id
        )

        return self._items.get(
            str(normalized_chunk_id)
        )

    # ==================================================================
    # EXISTS
    # ==================================================================

    async def exists(
        self,
        chunk_id: UUID,
    ) -> bool:
        """
        Check whether a chunk exists in the keyword index.
        """

        normalized_chunk_id = self._validate_chunk_id(
            chunk_id
        )

        return (
            str(normalized_chunk_id)
            in self._items
        )

    # ==================================================================
    # DELETE
    # ==================================================================

    async def delete(
        self,
        chunk_id: UUID,
    ) -> bool:
        """
        Delete a chunk from the keyword index.

        The BM25 index is rebuilt after deletion.
        """

        normalized_chunk_id = self._validate_chunk_id(
            chunk_id
        )

        key = str(normalized_chunk_id)

        if key not in self._items:
            return False

        del self._items[key]

        self._rebuild()

        return True

    # ==================================================================
    # CLEAR
    # ==================================================================

    async def clear(self) -> None:
        """
        Clear the entire keyword index.
        """

        self._items.clear()
        self._bm25 = None
        self._ordered_ids.clear()
        self._tokenized_corpus.clear()

    # ==================================================================
    # COUNT
    # ==================================================================

    async def count(self) -> int:
        """
        Return the number of indexed chunks.
        """

        return len(self._items)

    # ==================================================================
    # SNAPSHOT
    # ==================================================================

    def items(self) -> list[KeywordIndexItem]:
        """
        Return a snapshot of all indexed items.

        A new list is returned so callers cannot mutate the internal
        dictionary through the returned collection.
        """

        return list(
            self._items.values()
        )

    # ==================================================================
    # REBUILD
    # ==================================================================

    def _rebuild(self) -> None:
        """
        Rebuild the BM25 search index from authoritative state.

        `_items` remains the source of truth.

        The following structures must always have identical ordering:

            _ordered_ids
            _tokenized_corpus
            BM25 corpus
        """

        self._ordered_ids = []
        self._tokenized_corpus = []
        self._bm25 = None

        if not self._items:
            return

        for key, item in self._items.items():
            tokens = self._tokenize(item.text)

            self._ordered_ids.append(key)
            self._tokenized_corpus.append(tokens)

        # BM25Okapi cannot meaningfully operate on an empty corpus.

        if not self._tokenized_corpus:
            return

        self._bm25 = BM25Okapi(
            self._tokenized_corpus
        )

    # ==================================================================
    # TOKENIZATION
    # ==================================================================

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Tokenize text for BM25.

        This intentionally uses a deterministic lightweight tokenizer.

        A production deployment can later replace this with a more
        sophisticated analyzer without changing the KeywordIndexer
        public interface.
        """

        if not isinstance(text, str):
            return []

        normalized = text.lower().strip()

        if not normalized:
            return []

        return normalized.split()

    # ==================================================================
    # FILTERING
    # ==================================================================

    @classmethod
    def _matches_filters(
        cls,
        item: KeywordIndexItem,
        filters: dict[str, Any],
    ) -> bool:
        """
        Determine whether an item satisfies metadata filters.

        Current semantics:

            {"document_id": value}
            {"source": value}
            {"page": value}

        Nested metadata can also be addressed using dotted paths:

            {"document.id": value}

        For scalar values, equality is used.

        For iterable filter values, membership is used.
        """

        if not filters:
            return True

        for key, expected in filters.items():
            actual = cls._get_filter_value(
                item,
                key,
            )

            if isinstance(expected, (list, tuple, set, frozenset)):
                if actual not in expected:
                    return False
            else:
                if actual != expected:
                    return False

        return True

    @staticmethod
    def _get_filter_value(
        item: KeywordIndexItem,
        key: str,
    ) -> Any:
        """
        Resolve a filter value from the index item.

        Direct item attributes are checked first, followed by metadata.
        Dotted metadata paths are supported.
        """

        if key == "chunk_id":
            return item.chunk_id

        if key == "text":
            return item.text

        if hasattr(item, key):
            return getattr(item, key)

        current: Any = item.metadata

        for part in key.split("."):
            if not isinstance(current, dict):
                return None

            if part not in current:
                return None

            current = current[part]

        return current

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_chunk_id(
        chunk_id: UUID,
    ) -> UUID:
        """
        Validate a chunk identifier.
        """

        if not isinstance(chunk_id, UUID):
            raise TypeError(
                "chunk_id must be a UUID"
            )

        return chunk_id

    @staticmethod
    def _validate_text(
        text: str,
    ) -> str:
        """
        Validate and normalize indexed text.
        """

        if not isinstance(text, str):
            raise TypeError(
                "text must be a string"
            )

        normalized = text.strip()

        if not normalized:
            raise ValueError(
                "text must not be empty"
            )

        return normalized

    @staticmethod
    def _is_finite(
        value: float,
    ) -> bool:
        """
        Check whether a floating-point score is finite.
        """

        return value == value and abs(value) != float("inf")


__all__ = [
    "KeywordIndexItem",
    "KeywordSearchResult",
    "KeywordIndexer",
]