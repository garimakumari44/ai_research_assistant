from __future__ import annotations

from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """
    Local embedding generator using SentenceTransformers.

    Default model:
        BAAI/bge-small-en-v1.5

    Embedding dimension:
        384

    The model is loaded explicitly without the Hugging Face
    low-memory/meta-tensor loading path because that path can
    produce:

        NotImplementedError:
        Cannot copy out of meta tensor; no data!

    on CPU environments.

    Designed for:

        - Query embedding
        - Document/chunk embedding
        - Batch embedding
        - Semantic similarity
        - FAISS vector search
    """

    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
    DEFAULT_DEVICE = "cpu"
    DEFAULT_BATCH_SIZE = 32
    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        *,
        device: str = DEFAULT_DEVICE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        model: SentenceTransformer | None = None,
    ) -> None:

        if not isinstance(
            model_name,
            str,
        ) or not model_name.strip():

            raise ValueError(
                "model_name must not be empty."
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        self.model_name = model_name.strip()
        self.device = device
        self.batch_size = batch_size

        if model is not None:

            self.model = model

        else:

            self.model = self._load_model()

        self.dimension = self._resolve_dimension()

    # ======================================================================
    # MODEL LOADING
    # ======================================================================

    def _load_model(
        self,
    ) -> SentenceTransformer:
        """
        Load SentenceTransformer safely.

        The important part is:

            model_kwargs={"low_cpu_mem_usage": False}

        This prevents the transformers/accelerate loader from
        constructing the model on the meta device and subsequently
        attempting:

            model.to("cpu")

        which causes the meta-tensor exception seen in the backend.
        """

        model_kwargs = {
            "low_cpu_mem_usage": False,
        }

        try:

            return SentenceTransformer(
                self.model_name,
                device=self.device,
                model_kwargs=model_kwargs,
            )

        except NotImplementedError as exc:

            message = str(exc)

            if (
                "meta tensor" not in message.lower()
                and "to_empty" not in message.lower()
            ):
                raise

            # --------------------------------------------------------------
            # Second attempt.
            #
            # Some SentenceTransformer/transformers combinations can still
            # activate meta loading. Retry with an explicit CPU device.
            # --------------------------------------------------------------

            if self.device != "cpu":

                return SentenceTransformer(
                    self.model_name,
                    device="cpu",
                    model_kwargs={
                        "low_cpu_mem_usage": False,
                    },
                )

            raise RuntimeError(
                "SentenceTransformer could not load "
                f"'{self.model_name}' without using meta tensors. "
                "Please verify the installed torch, transformers, "
                "sentence-transformers, and accelerate versions."
            ) from exc

    # ======================================================================
    # MODEL INFORMATION
    # ======================================================================

    def _resolve_dimension(
        self,
    ) -> int:

        try:

            dimension = (
                self.model
                .get_sentence_embedding_dimension()
            )

        except AttributeError as exc:

            raise RuntimeError(
                "Embedding model does not expose "
                "get_sentence_embedding_dimension()."
            ) from exc

        if dimension is None:

            raise RuntimeError(
                "Unable to determine embedding dimension."
            )

        dimension = int(
            dimension
        )

        if dimension <= 0:

            raise RuntimeError(
                f"Invalid embedding dimension: {dimension}"
            )

        return dimension

    # ======================================================================
    # SINGLE TEXT EMBEDDING
    # ======================================================================

    def embed_text(
        self,
        text: str,
    ) -> np.ndarray:

        if not isinstance(
            text,
            str,
        ):
            return np.empty(
                0,
                dtype=np.float32,
            )

        text = text.strip()

        if not text:
            return np.empty(
                0,
                dtype=np.float32,
            )

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return self._validate_embedding(
            embedding
        )

    # ======================================================================
    # BATCH EMBEDDING
    # ======================================================================

    def embed_texts(
        self,
        texts: list[str],
    ) -> np.ndarray:

        if not texts:

            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        cleaned_texts = [
            text.strip()
            if isinstance(
                text,
                str,
            )
            else ""
            for text in texts
        ]

        embeddings = self.model.encode(
            cleaned_texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        return self._validate_batch_embeddings(
            embeddings,
            expected_count=len(
                cleaned_texts
            ),
        )

    # ======================================================================
    # QUERY EMBEDDING
    # ======================================================================

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray:

        return self.embed_text(
            query
        )

    # ======================================================================
    # GENERIC GENERATE API
    # ======================================================================

    def generate(
        self,
        text: str,
    ) -> np.ndarray:

        return self.embed_text(
            text
        )

    # ======================================================================
    # VALIDATION
    # ======================================================================

    def _validate_embedding(
        self,
        embedding: Any,
    ) -> np.ndarray:

        if embedding is None:

            return np.empty(
                0,
                dtype=np.float32,
            )

        vector = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if vector.ndim != 1:

            vector = vector.reshape(
                -1
            )

        if vector.size == 0:

            return np.empty(
                0,
                dtype=np.float32,
            )

        if vector.size != self.dimension:

            raise ValueError(
                "Embedding dimension mismatch: "
                f"expected {self.dimension}, "
                f"received {vector.size}"
            )

        if not np.all(
            np.isfinite(
                vector
            )
        ):

            raise ValueError(
                "Embedding contains non-finite values."
            )

        return vector

    def _validate_batch_embeddings(
        self,
        embeddings: np.ndarray,
        *,
        expected_count: int,
    ) -> np.ndarray:

        if embeddings.size == 0:

            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        if embeddings.ndim != 2:

            raise ValueError(
                "Batch embeddings must be "
                "a 2-dimensional array."
            )

        actual_count, actual_dimension = (
            embeddings.shape
        )

        if actual_count != expected_count:

            raise ValueError(
                "Embedding count mismatch: "
                f"expected {expected_count}, "
                f"received {actual_count}"
            )

        if actual_dimension != self.dimension:

            raise ValueError(
                "Embedding dimension mismatch: "
                f"expected {self.dimension}, "
                f"received {actual_dimension}"
            )

        if not np.all(
            np.isfinite(
                embeddings
            )
        ):

            raise ValueError(
                "Batch embeddings contain "
                "non-finite values."
            )

        return embeddings.astype(
            np.float32,
            copy=False,
        )

    # ======================================================================
    # PROPERTIES
    # ======================================================================

    @property
    def model_dimension(
        self,
    ) -> int:

        return self.dimension

    @property
    def name(
        self,
    ) -> str:

        return self.model_name

    # ======================================================================
    # UTILITY
    # ======================================================================

    def is_compatible_with(
        self,
        dimension: int,
    ) -> bool:

        return self.dimension == dimension


__all__ = [
    "EmbeddingGenerator",
]