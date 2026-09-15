from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence
from uuid import UUID

import numpy as np

from app.indexing.vector_store.faiss_index import FAISSIndex


@dataclass(slots=True)
class VectorIndexItem:
    """
    Represents one chunk stored in the vector index.

    The VectorIndexItem is the authoritative application-level
    representation of an indexed chunk.
    """

    chunk_id: UUID
    vector: Sequence[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorSearchResult:
    """
    Result returned by vector similarity search.
    """

    chunk_id: UUID
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorIndexer:
    """
    Application-level vector index abstraction.

    The `_items` dictionary is the authoritative application-level
    state. FAISS is the search acceleration layer.

    Architecture:

        VectorIndexer
              |
              v
        FAISSIndex
              |
              v
            FAISS
    """

    def __init__(
        self,
        *,
        dimension: int = 384,
        faiss_index: FAISSIndex | None = None,
    ) -> None:
        if not isinstance(dimension, int):
            raise TypeError("dimension must be an integer")

        if dimension <= 0:
            raise ValueError("dimension must be greater than 0")

        self.dimension = dimension

        self._faiss = (
            faiss_index
            if faiss_index is not None
            else FAISSIndex(dimension=dimension)
        )

        faiss_dimension = getattr(
            self._faiss,
            "dimension",
            None,
        )

        if (
            faiss_dimension is not None
            and int(faiss_dimension) != self.dimension
        ):
            raise ValueError(
                "FAISS index dimension mismatch: "
                f"expected {self.dimension}, "
                f"received {faiss_dimension}"
            )

        self._items: dict[str, VectorIndexItem] = {}

    # ==================================================================
    # PROPERTIES
    # ==================================================================

    @property
    def faiss(self) -> FAISSIndex:
        """
        Return the underlying FAISS index.
        """
        return self._faiss

    @property
    def index(self) -> FAISSIndex:
        """
        Backwards-compatible alias for the underlying FAISS index.
        """
        return self._faiss

    # ==================================================================
    # UPSERT
    # ==================================================================

    async def upsert(
        self,
        chunk_id: UUID,
        vector: Sequence[float],
        metadata: dict[str, Any] | None = None,
    ) -> VectorIndexItem:
        """
        Insert or replace one vector.
        """

        normalized_chunk_id = self._validate_chunk_id(chunk_id)

        normalized_vector = self._validate_vector(vector)

        item = VectorIndexItem(
            chunk_id=normalized_chunk_id,
            vector=normalized_vector,
            metadata=dict(metadata or {}),
        )

        self._items[str(normalized_chunk_id)] = item

        self._rebuild_faiss()

        return item

    async def upsert_many(
        self,
        items: Sequence[VectorIndexItem],
    ) -> list[VectorIndexItem]:
        """
        Insert or replace multiple vectors.

        FAISS is rebuilt once after all items have been updated.
        """

        if items is None:
            raise ValueError("items must not be None")

        normalized_items: list[VectorIndexItem] = []

        for item in items:
            if not isinstance(item, VectorIndexItem):
                raise TypeError(
                    "upsert_many() expects VectorIndexItem instances"
                )

            normalized_chunk_id = self._validate_chunk_id(
                item.chunk_id
            )

            normalized_vector = self._validate_vector(
                item.vector
            )

            normalized_item = VectorIndexItem(
                chunk_id=normalized_chunk_id,
                vector=normalized_vector,
                metadata=dict(item.metadata or {}),
            )

            normalized_items.append(normalized_item)

        for item in normalized_items:
            self._items[str(item.chunk_id)] = item

        if normalized_items:
            self._rebuild_faiss()

        return normalized_items

    # ==================================================================
    # RESTORE ITEMS
    # ==================================================================

    def restore_items(
        self,
        items: Sequence[VectorIndexItem],
    ) -> None:
        """
        Restore the authoritative application-level vector state.

        This is used during FastAPI startup and Celery worker startup
        when vectors are loaded from persistent storage.

        Unlike `upsert_many()`, this method explicitly represents a
        restoration operation.

        Existing state is replaced completely.
        """

        if items is None:
            raise ValueError("items must not be None")

        restored_items: dict[str, VectorIndexItem] = {}

        for item in items:
            if not isinstance(item, VectorIndexItem):
                raise TypeError(
                    "restore_items() expects VectorIndexItem instances"
                )

            normalized_chunk_id = self._validate_chunk_id(
                item.chunk_id
            )

            normalized_vector = self._validate_vector(
                item.vector
            )

            normalized_item = VectorIndexItem(
                chunk_id=normalized_chunk_id,
                vector=normalized_vector,
                metadata=dict(item.metadata or {}),
            )

            key = str(normalized_chunk_id)

            if key in restored_items:
                raise ValueError(
                    "Duplicate chunk ID during vector restoration: "
                    f"{key}"
                )

            restored_items[key] = normalized_item

        self._items = restored_items

        self._rebuild_faiss()

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 10,
    ) -> list[VectorSearchResult]:
        """
        Perform vector similarity search.
        """

        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")

        if top_k <= 0:
            return []

        if not self._items:
            return []

        normalized_query = self._validate_vector(
            query_vector
        )

        raw_results = self._faiss.search(
            normalized_query,
            top_k,
        )

        if not raw_results:
            return []

        results: list[VectorSearchResult] = []

        for raw_result in raw_results:
            if not isinstance(raw_result, dict):
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

            item = self._items.get(str(raw_id))

            if item is None:
                continue

            results.append(
                VectorSearchResult(
                    chunk_id=item.chunk_id,
                    score=score,
                    metadata=dict(item.metadata),
                )
            )

            if len(results) >= top_k:
                break

        return results

    # ==================================================================
    # GET
    # ==================================================================

    async def get(
        self,
        chunk_id: UUID,
    ) -> VectorIndexItem | None:
        """
        Retrieve an indexed vector by chunk ID.
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
        Check whether a chunk exists.
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
        Delete a vector from the index.
        """

        normalized_chunk_id = self._validate_chunk_id(
            chunk_id
        )

        key = str(normalized_chunk_id)

        if key not in self._items:
            return False

        del self._items[key]

        self._rebuild_faiss()

        return True

    # ==================================================================
    # COUNT
    # ==================================================================

    async def count(self) -> int:
        """
        Return the number of indexed vectors.
        """

        return len(self._items)

    # ==================================================================
    # CLEAR
    # ==================================================================

    async def clear(self) -> None:
        """
        Remove all vectors and reset FAISS.
        """

        self._items.clear()

        self._faiss.reset()

    # ==================================================================
    # REBUILD
    # ==================================================================

    def _rebuild_faiss(self) -> None:
        """
        Rebuild FAISS from the authoritative application state.
        """

        self._faiss.reset()

        if not self._items:
            return

        embeddings: list[Sequence[float]] = []
        ids: list[str] = []

        for item in self._items.values():
            embeddings.append(item.vector)
            ids.append(str(item.chunk_id))

        self._faiss.add(
            embeddings,
            ids,
        )

    # ==================================================================
    # RESTORE FAISS STATE
    # ==================================================================

    def restore_faiss_state(
        self,
        *,
        index: Any,
        ids: Sequence[str],
    ) -> None:
        """
        Restore a persisted FAISS index directly.

        This method is useful for infrastructure-level restoration.

        Normally startup should use `restore_items()` because the
        application-level `_items` state must also be reconstructed.
        """

        if index is None:
            raise ValueError("index must not be None")

        if ids is None:
            raise ValueError("ids must not be None")

        ids_list = [
            str(item_id)
            for item_id in ids
        ]

        index_total = int(
            getattr(index, "ntotal", -1)
        )

        if len(ids_list) != index_total:
            raise ValueError(
                "Persisted FAISS index and ID mapping "
                "have different sizes: "
                f"{index_total} vectors vs "
                f"{len(ids_list)} IDs"
            )

        index_dimension = getattr(
            index,
            "d",
            None,
        )

        if (
            index_dimension is not None
            and int(index_dimension) != self.dimension
        ):
            raise ValueError(
                "Persisted FAISS index dimension mismatch: "
                f"expected {self.dimension}, "
                f"received {index_dimension}"
            )

        self._faiss.index = index
        self._faiss.ids = ids_list

    # ==================================================================
    # SNAPSHOT
    # ==================================================================

    def items(self) -> list[VectorIndexItem]:
        """
        Return a snapshot of all indexed items.
        """

        return list(self._items.values())

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_chunk_id(
        chunk_id: UUID,
    ) -> UUID:
        """
        Validate a chunk UUID.
        """

        if not isinstance(chunk_id, UUID):
            raise TypeError(
                "chunk_id must be a UUID"
            )

        return chunk_id

    def _validate_vector(
        self,
        vector: Sequence[float],
    ) -> np.ndarray:
        """
        Validate and normalize one embedding vector.
        """

        if vector is None:
            raise ValueError(
                "vector must not be None"
            )

        try:
            array = np.asarray(
                vector,
                dtype=np.float32,
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "vector must contain numeric values"
            ) from exc

        if array.size == 0:
            raise ValueError(
                "vector must not be empty"
            )

        if array.ndim == 2:
            if array.shape[0] != 1:
                raise ValueError(
                    "vector must represent exactly one embedding"
                )

            array = array[0]

        elif array.ndim != 1:
            raise ValueError(
                "vector must be one-dimensional"
            )

        if array.size != self.dimension:
            raise ValueError(
                "Vector dimension mismatch: "
                f"expected {self.dimension}, "
                f"received {array.size}"
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(
                "vector contains non-finite values"
            )

        return np.ascontiguousarray(
            array,
            dtype=np.float32,
        )


__all__ = [
    "VectorIndexItem",
    "VectorSearchResult",
    "VectorIndexer",
]