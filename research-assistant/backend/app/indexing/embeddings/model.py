from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from app.core.logging import logger


MODEL_NAME = "BAAI/bge-small-en-v1.5"
DEFAULT_DIMENSION = 384


class EmbeddingModel:
    """
    Lazy wrapper around the BGE embedding model.

    IMPORTANT
    ---------
    Importing this module does NOT import SentenceTransformers,
    PyTorch, or load the BGE model.

    Creating EmbeddingModel() also does NOT load the model.

    SentenceTransformer is imported and instantiated only when
    encode() is called.
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
    ) -> None:

        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError(
                "model_name must not be empty."
            )

        self.model_name = model_name.strip()

        # Model is intentionally NOT loaded here.
        self.model: Any | None = None

    # ==================================================================
    # LAZY MODEL ACCESS
    # ==================================================================

    def _get_model(self) -> Any:
        """
        Return the SentenceTransformer model.

        The model is loaded only on the first actual embedding request.
        """

        if self.model is None:
            self.model = self._load_model()

        return self.model

    # ==================================================================
    # MODEL LOADING
    # ==================================================================

    def _load_model(self) -> Any:
        """
        Lazily import and load SentenceTransformer.

        This function is the ONLY place where SentenceTransformer
        should be imported.
        """

        # IMPORTANT:
        # Do NOT move this import to module level.
        from sentence_transformers import SentenceTransformer

        try:
            logger.info(
                f"Loading embedding model: {self.model_name}"
            )

            model = SentenceTransformer(
                self.model_name,
                device="cpu",
                model_kwargs={
                    "low_cpu_mem_usage": False,
                },
            )

            logger.info(
                "Embedding model loaded successfully"
            )

            return model

        except NotImplementedError as exc:

            message = str(exc).lower()

            if (
                "meta tensor" not in message
                and "to_empty" not in message
            ):
                raise

            logger.exception(
                "SentenceTransformer failed because of a meta-tensor "
                "loading problem."
            )

            raise RuntimeError(
                "SentenceTransformer could not load "
                f"'{self.model_name}' without meta tensors. "
                "Please verify the installed torch, transformers, "
                "sentence-transformers, and accelerate versions."
            ) from exc

        except Exception as exc:

            logger.exception(
                "Failed to load embedding model"
            )

            raise exc

    # ==================================================================
    # ENCODE
    # ==================================================================

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Convert text into normalized embeddings.

        Calling this method triggers lazy model loading.
        """

        if not isinstance(texts, list):
            raise TypeError(
                "texts must be a list of strings."
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        cleaned_texts = [
            text.strip()
            if isinstance(text, str)
            else ""
            for text in texts
        ]

        if not cleaned_texts:
            return np.empty(
                (0, DEFAULT_DIMENSION),
                dtype=np.float32,
            )

        embeddings = self._get_model().encode(
            cleaned_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return np.asarray(
            embeddings,
            dtype=np.float32,
        )

    # ==================================================================
    # SINGLE TEXT
    # ==================================================================

    def encode_one(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Encode one text string.

        Model loading happens lazily.
        """

        if not isinstance(text, str):
            return np.empty(
                (0,),
                dtype=np.float32,
            )

        text = text.strip()

        if not text:
            return np.empty(
                (0,),
                dtype=np.float32,
            )

        embedding = self._get_model().encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        vector = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if vector.ndim != 1:
            vector = vector.reshape(-1)

        if vector.size != DEFAULT_DIMENSION:
            raise ValueError(
                "Embedding dimension mismatch: "
                f"expected {DEFAULT_DIMENSION}, "
                f"received {vector.size}"
            )

        if not np.all(np.isfinite(vector)):
            raise ValueError(
                "Embedding contains non-finite values."
            )

        return vector

    # ==================================================================
    # STATUS
    # ==================================================================

    @property
    def is_loaded(self) -> bool:
        """
        Return True if SentenceTransformer has been loaded.
        """

        return self.model is not None

    @property
    def dimension(self) -> int:
        """
        Return the embedding dimension.

        BGE-small-en-v1.5 is known to produce 384-dimensional vectors,
        so this property does not need to load the model.
        """

        return DEFAULT_DIMENSION


# ======================================================================
# CACHED MODEL ACCESS
# ======================================================================

@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """
    Return the singleton lazy EmbeddingModel.

    IMPORTANT:
        Calling this function does NOT load SentenceTransformer.

    The actual model is loaded only when encode() or encode_one()
    is called.
    """

    return EmbeddingModel()


__all__ = [
    "EmbeddingModel",
    "get_embedding_model",
]