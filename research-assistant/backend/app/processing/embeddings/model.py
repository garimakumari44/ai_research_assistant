"""
Embedding model loader.

Responsible for loading and managing embedding models.

The model is loaded lazily:
    - importing this module does NOT import sentence-transformers
    - constructing EmbeddingModel does NOT load the model
    - the model is loaded only when encode() or dimension() is called
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.logging import logger


class EmbeddingModel:
    """
    Lazy SentenceTransformer model wrapper.

    This class intentionally avoids importing or loading
    SentenceTransformer during application startup.

    The actual model is created only when _get_model()
    is first called.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
    ) -> None:
        self.model_name = model_name
        self.device = device

        # IMPORTANT:
        # Do not load the model here.
        self.model: Any | None = None

    # ======================================================================
    # MODEL LOADING
    # ======================================================================

    def _get_model(self) -> Any:
        """
        Return the loaded model.

        The model is initialized only on the first call.
        """

        if self.model is not None:
            return self.model

        self.model = self._load_model()

        return self.model

    def _load_model(self) -> Any:
        """
        Load SentenceTransformer lazily.

        SentenceTransformer is imported inside this method so that
        importing the application does not immediately import the
        heavy ML stack.
        """

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(
                "Loading embedding model: %s",
                self.model_name,
            )

            model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )

            logger.info(
                "Loaded embedding model: %s",
                self.model_name,
            )

            return model

        except Exception:
            logger.exception(
                "Failed loading embedding model: %s",
                self.model_name,
            )
            raise

    # ======================================================================
    # ENCODING
    # ======================================================================

    def encode(
        self,
        texts: list[str],
    ) -> Any:
        """
        Generate normalized embeddings for the supplied texts.

        The model is loaded on first use.
        """

        if not texts:
            return []

        model = self._get_model()

        return model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    # ======================================================================
    # DIMENSION
    # ======================================================================

    def dimension(self) -> int:
        """
        Return the embedding dimension.

        The model is loaded on first use if necessary.
        """

        model = self._get_model()

        return int(
            model.get_sentence_embedding_dimension()
        )


# ======================================================================
# CACHED MODEL FACTORY
# ======================================================================

@lru_cache(maxsize=None)
def get_embedding_model(
    model_name: str = "BAAI/bge-small-en-v1.5",
) -> EmbeddingModel:
    """
    Return a cached lazy EmbeddingModel instance.

    IMPORTANT:
    This function creates only the lightweight wrapper.
    It does NOT load SentenceTransformer/BGE.

    The actual model is loaded later by encode() or dimension().
    """

    return EmbeddingModel(
        model_name=model_name,
        device="cpu",
    )