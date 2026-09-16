from __future__ import annotations

from typing import Any

import numpy as np

from app.core.config import settings


class EmbeddingGenerator:
    """
    Provider-aware embedding generator.

    Supported providers:

        local
            Uses SentenceTransformers + BAAI/bge-small-en-v1.5 locally.

        remote
            Uses Hugging Face Inference Providers.

    The public interface remains the same so existing retrieval,
    indexing, research, evaluation, and generation components can
    continue using EmbeddingGenerator without knowing which provider
    is being used.

    Default model:
        BAAI/bge-small-en-v1.5

    Embedding dimension:
        384
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
        model: Any = None,
        provider: str | None = None,
    ) -> None:

        if not isinstance(model_name, str) or not model_name.strip():
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

        # Provider can be explicitly supplied by callers,
        # otherwise it comes from application configuration.
        self.provider = (
            provider or settings.EMBEDDING_PROVIDER
        ).strip().lower()

        if self.provider not in {"local", "remote"}:
            raise ValueError(
                "Unsupported embedding provider: "
                f"{self.provider!r}. "
                "Expected 'local' or 'remote'."
            )

        # Local SentenceTransformer model.
        #
        # IMPORTANT:
        # Do not import SentenceTransformer at module level.
        #
        # This keeps PyTorch/SentenceTransformers out of application
        # startup when using the remote provider.
        self.model = model

        # Remote Hugging Face client.
        #
        # This is also lazy-loaded.
        self._remote_client: Any = None

        # BGE-small is known to be 384 dimensions.
        #
        # This lets us construct EmbeddingGenerator without loading
        # any ML model.
        self.dimension = int(
            settings.EMBEDDING_DIMENSION
        )

        if self.dimension <= 0:
            raise ValueError(
                "EMBEDDING_DIMENSION must be greater than 0."
            )

        # If a custom local model object was supplied, resolve its
        # actual dimension.
        if self.model is not None:
            self.dimension = self._resolve_dimension()

    # ==================================================================
    # PROVIDER
    # ==================================================================

    @property
    def is_local(self) -> bool:
        """Return True when local model inference is configured."""

        return self.provider == "local"

    @property
    def is_remote(self) -> bool:
        """Return True when remote inference is configured."""

        return self.provider == "remote"

    # ==================================================================
    # LOCAL MODEL
    # ==================================================================

    def _get_model(self) -> Any:
        """
        Return the local SentenceTransformer model.

        The model is loaded only when local embedding generation is
        actually requested.
        """

        if not self.is_local:
            raise RuntimeError(
                "Local model requested while embedding provider "
                f"is '{self.provider}'."
            )

        if self.model is None:
            self.model = self._load_model()
            self.dimension = self._resolve_dimension()

        return self.model

    def _load_model(self) -> Any:
        """
        Load SentenceTransformer lazily.

        SentenceTransformers and PyTorch are imported only here.

        This is critical for Render production because remote
        embedding mode must not import the local ML stack.
        """

        from sentence_transformers import SentenceTransformer

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

    # ==================================================================
    # REMOTE HUGGING FACE CLIENT
    # ==================================================================

    def _get_remote_client(self) -> Any:
        """
        Lazily create the Hugging Face InferenceClient.

        Importing huggingface_hub only happens when remote inference
        is actually requested.
        """

        if not self.is_remote:
            raise RuntimeError(
                "Remote client requested while embedding provider "
                f"is '{self.provider}'."
            )

        if self._remote_client is None:

            api_key = settings.EMBEDDING_API_KEY

            if not api_key:
                raise RuntimeError(
                    "EMBEDDING_API_KEY is required when "
                    "EMBEDDING_PROVIDER='remote'."
                )

            from huggingface_hub import InferenceClient

            client_kwargs: dict[str, Any] = {
                "token": api_key,
                "timeout": settings.EMBEDDING_TIMEOUT,
            }

            # If a custom endpoint is supplied, use it.
            #
            # Otherwise Inference Providers automatically route the
            # model through Hugging Face's configured inference
            # provider infrastructure.
            if settings.EMBEDDING_API_URL:
                client_kwargs["model"] = (
                    settings.EMBEDDING_API_URL
                )

            self._remote_client = InferenceClient(
                **client_kwargs
            )

        return self._remote_client

    # ==================================================================
    # REMOTE SINGLE EMBEDDING
    # ==================================================================

    def _remote_embed_text(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Generate one embedding through Hugging Face.
        """

        client = self._get_remote_client()

        result = client.feature_extraction(
            text,
            model=self.model_name,
            normalize=True,
        )

        embedding = np.asarray(
            result,
            dtype=np.float32,
        )

        # Hugging Face may return shape (1, dimension) for a
        # single input. Flatten that into the expected vector.
        if embedding.ndim > 1:
            embedding = embedding.reshape(-1)

        return self._validate_embedding(
            embedding
        )

    # ==================================================================
    # REMOTE BATCH EMBEDDING
    # ==================================================================

    def _remote_embed_texts(
        self,
        texts: list[str],
    ) -> np.ndarray:
        """
        Generate multiple embeddings through Hugging Face.
        """

        if not texts:
            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        client = self._get_remote_client()

        result = client.feature_extraction(
            texts,
            model=self.model_name,
            normalize=True,
        )

        embeddings = np.asarray(
            result,
            dtype=np.float32,
        )

        # A single-item batch can occasionally arrive as
        # a one-dimensional array.
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(
                1,
                -1,
            )

        return self._validate_batch_embeddings(
            embeddings,
            expected_count=len(texts),
        )

    # ==================================================================
    # SINGLE TEXT EMBEDDING
    # ==================================================================

    def embed_text(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Generate an embedding for one text.
        """

        if not isinstance(text, str):
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

        # --------------------------------------------------------------
        # REMOTE
        # --------------------------------------------------------------

        if self.is_remote:
            return self._remote_embed_text(
                text
            )

        # --------------------------------------------------------------
        # LOCAL
        # --------------------------------------------------------------

        embedding = self._get_model().encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return self._validate_embedding(
            embedding
        )

    # ==================================================================
    # BATCH EMBEDDING
    # ==================================================================

    def embed_texts(
        self,
        texts: list[str],
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        """

        if not texts:
            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        cleaned_texts = [
            text.strip()
            if isinstance(text, str)
            else ""
            for text in texts
        ]

        # --------------------------------------------------------------
        # REMOTE
        # --------------------------------------------------------------

        if self.is_remote:
            return self._remote_embed_texts(
                cleaned_texts
            )

        # --------------------------------------------------------------
        # LOCAL
        # --------------------------------------------------------------

        embeddings = self._get_model().encode(
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

    # ==================================================================
    # QUERY EMBEDDING
    # ==================================================================

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray:
        """
        Generate a query embedding.
        """

        return self.embed_text(
            query
        )

    # ==================================================================
    # GENERIC GENERATE API
    # ==================================================================

    def generate(
        self,
        text: Any,
    ) -> Any:
        """
        Backward-compatible embedding API.

        Supports:

            generate("some text")
                -> np.ndarray

        and the existing indexing pipeline contract:

            generate([
                {"id": "...", "text": "..."},
                ...
            ])
                -> [
                    {"id": "...", "text": "...", "embedding": ...},
                    ...
                ]
        """

        # --------------------------------------------------------------
        # Single string
        # --------------------------------------------------------------

        if isinstance(text, str):
            return self.embed_text(
                text
            )

        # --------------------------------------------------------------
        # Batch/indexing input
        # --------------------------------------------------------------

        if isinstance(text, list):

            if not text:
                return []

            # Existing indexing pipeline passes dictionaries.
            if all(
                isinstance(item, dict)
                for item in text
            ):

                valid_items = []

                for item in text:

                    item_text = (
                        item.get("text")
                        or item.get("content")
                        or item.get("chunk_text")
                        or ""
                    )

                    valid_items.append(
                        item_text
                        if isinstance(
                            item_text,
                            str,
                        )
                        else ""
                    )

                embeddings = self.embed_texts(
                    valid_items
                )

                results = []

                for item, embedding in zip(
                    text,
                    embeddings,
                ):

                    result = dict(item)

                    result["embedding"] = embedding

                    results.append(
                        result
                    )

                return results

            # Generic list[str] support.
            if all(
                isinstance(item, str)
                for item in text
            ):
                return self.embed_texts(
                    text
                )

        raise TypeError(
            "generate() expects a string, "
            "list[str], or list[dict]."
        )

    # ==================================================================
    # MODEL INFORMATION
    # ==================================================================

    def _resolve_dimension(
        self,
    ) -> int:
        """
        Resolve the dimension from an already-loaded local model.
        """

        if self.model is None:
            return self.dimension

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

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def _validate_embedding(
        self,
        embedding: Any,
    ) -> np.ndarray:
        """
        Validate a single embedding vector.
        """

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
            vector = vector.reshape(-1)

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
            np.isfinite(vector)
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
        """
        Validate a batch of embedding vectors.
        """

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
            np.isfinite(embeddings)
        ):

            raise ValueError(
                "Batch embeddings contain "
                "non-finite values."
            )

        return embeddings.astype(
            np.float32,
            copy=False,
        )

    # ==================================================================
    # PROPERTIES
    # ==================================================================

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

    # ==================================================================
    # UTILITY
    # ==================================================================

    def is_compatible_with(
        self,
        dimension: int,
    ) -> bool:
        return self.dimension == dimension


__all__ = [
    "EmbeddingGenerator",
]