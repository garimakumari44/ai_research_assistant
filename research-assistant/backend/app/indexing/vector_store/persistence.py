from __future__ import annotations

import json
import os
from typing import Any, List, Sequence

import faiss
import numpy as np

from app.core.logging import logger


class FAISSPersistence:
    """
    Handles persistence of the local FAISS vector index.

    Persisted state consists of:

    1. FAISS index
    2. Vector ID mapping
    3. Raw embedding vectors

    Raw vectors are persisted because the application-level
    VectorIndexer keeps the authoritative vector/metadata state
    in its `_items` dictionary. FAISS alone cannot reconstruct
    that application-level state safely.
    """

    def __init__(
        self,
        storage_path: str = "storage/faiss",
    ) -> None:
        self.storage_path = storage_path

        os.makedirs(
            self.storage_path,
            exist_ok=True,
        )

        self.index_file = os.path.join(
            self.storage_path,
            "index.faiss",
        )

        self.ids_file = os.path.join(
            self.storage_path,
            "ids.json",
        )

        self.vectors_file = os.path.join(
            self.storage_path,
            "vectors.npy",
        )

    # ==================================================================
    # SAVE
    # ==================================================================

    def save(
        self,
        index: Any,
        ids: List[str],
        vectors: Sequence[Sequence[float]] | None = None,
    ) -> None:
        """
        Persist the FAISS index, IDs, and optionally raw vectors.

        Args:
            index:
                FAISS index instance.

            ids:
                IDs in the exact order represented by the FAISS index.

            vectors:
                Raw embedding vectors in the same order as `ids`.

        Raises:
            ValueError:
                If vectors are supplied but their count does not match IDs.
        """

        if index is None:
            raise ValueError(
                "index must not be None"
            )

        if ids is None:
            raise ValueError(
                "ids must not be None"
            )

        normalized_ids = [
            str(item_id)
            for item_id in ids
        ]

        try:
            faiss.write_index(
                index,
                self.index_file,
            )

            with open(
                self.ids_file,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    normalized_ids,
                    file,
                    indent=4,
                )

            if vectors is not None:
                vector_array = np.asarray(
                    vectors,
                    dtype=np.float32,
                )

                if vector_array.ndim != 2:
                    raise ValueError(
                        "Persisted vectors must be a 2D array"
                    )

                if len(vector_array) != len(
                    normalized_ids
                ):
                    raise ValueError(
                        "Vectors and IDs count mismatch: "
                        f"{len(vector_array)} vectors vs "
                        f"{len(normalized_ids)} IDs"
                    )

                if (
                    vector_array.shape[1]
                    != int(index.d)
                ):
                    raise ValueError(
                        "Vector dimension mismatch: "
                        f"FAISS={index.d}, "
                        f"vectors={vector_array.shape[1]}"
                    )

                np.save(
                    self.vectors_file,
                    vector_array,
                )

            elif os.path.exists(
                self.vectors_file
            ):
                os.remove(
                    self.vectors_file
                )

            logger.info(
                "FAISS index saved successfully: "
                f"{len(normalized_ids)} vectors"
            )

        except Exception as exc:
            logger.exception(
                "Failed saving FAISS index"
            )
            raise exc

    # ==================================================================
    # LOAD
    # ==================================================================

    def load(self) -> dict[str, Any] | None:
        """
        Load persisted FAISS state.

        Returns:

            {
                "index": FAISS index,
                "ids": [...],
                "vectors": np.ndarray | None,
            }

        Returns None when no persisted index exists.
        """

        if not self.exists():
            logger.warning(
                "Persisted FAISS index not found"
            )
            return None

        try:
            index = faiss.read_index(
                self.index_file
            )

            with open(
                self.ids_file,
                "r",
                encoding="utf-8",
            ) as file:
                ids = json.load(file)

            if not isinstance(
                ids,
                list,
            ):
                raise ValueError(
                    "Persisted IDs must be a JSON list"
                )

            ids = [
                str(item_id)
                for item_id in ids
            ]

            if len(ids) != int(
                index.ntotal
            ):
                raise ValueError(
                    "Persisted FAISS index and ID mapping "
                    "have different sizes: "
                    f"{index.ntotal} vectors vs "
                    f"{len(ids)} IDs"
                )

            vectors = None

            if os.path.exists(
                self.vectors_file
            ):
                vectors = np.load(
                    self.vectors_file,
                    allow_pickle=False,
                )

                if vectors.ndim != 2:
                    raise ValueError(
                        "Persisted vectors must be a 2D array"
                    )

                if len(vectors) != len(ids):
                    raise ValueError(
                        "Persisted vectors and IDs "
                        "have different sizes: "
                        f"{len(vectors)} vectors vs "
                        f"{len(ids)} IDs"
                    )

                if vectors.shape[1] != int(
                    index.d
                ):
                    raise ValueError(
                        "Persisted vector dimension mismatch: "
                        f"FAISS={index.d}, "
                        f"vectors={vectors.shape[1]}"
                    )

                vectors = np.ascontiguousarray(
                    vectors,
                    dtype=np.float32,
                )

            logger.info(
                "FAISS index loaded successfully: "
                f"{len(ids)} vectors"
            )

            return {
                "index": index,
                "ids": ids,
                "vectors": vectors,
            }

        except Exception as exc:
            logger.exception(
                "Failed loading FAISS index"
            )
            raise exc

    # ==================================================================
    # EXISTS
    # ==================================================================

    def exists(self) -> bool:
        """
        Check whether the complete persisted FAISS state exists.

        A complete state requires:

        - index.faiss
        - ids.json
        - vectors.npy
        """

        return (
            os.path.exists(
                self.index_file
            )
            and os.path.exists(
                self.ids_file
            )
            and os.path.exists(
                self.vectors_file
            )
        )

    # ==================================================================
    # DELETE
    # ==================================================================

    def delete(self) -> None:
        """
        Delete all persisted FAISS state.
        """

        for path in (
            self.index_file,
            self.ids_file,
            self.vectors_file,
        ):
            if os.path.exists(path):
                os.remove(path)

        logger.info(
            "FAISS persistence deleted"
        )


__all__ = [
    "FAISSPersistence",
]