from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from uuid import UUID


@dataclass(slots=True)
class EmbeddingConfig:
    """
    Configuration for the embedding subsystem.

    This configuration is intentionally provider-neutral.
    """

    model: str

    dimensions: int | None = None

    batch_size: int = 32

    normalize: bool = True

    max_input_tokens: int | None = None

    timeout_seconds: float = 60.0

    max_retries: int = 3

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("Embedding model cannot be empty.")

        if self.dimensions is not None and self.dimensions <= 0:
            raise ValueError(
                "Embedding dimensions must be greater than zero."
            )

        if self.batch_size <= 0:
            raise ValueError(
                "Embedding batch_size must be greater than zero."
            )

        if self.max_input_tokens is not None:
            if self.max_input_tokens <= 0:
                raise ValueError(
                    "max_input_tokens must be greater than zero."
                )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        if self.max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )


@dataclass(slots=True)
class EmbeddingResult:
    """
    Canonical representation of one embedding.

    This object is independent of any specific provider.
    """

    vector: list[float]

    model: str

    dimensions: int

    index: int = 0

    text: str | None = None

    document_id: UUID | str | None = None

    chunk_id: UUID | str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vector:
            raise ValueError(
                "Embedding vector cannot be empty."
            )

        if self.dimensions != len(self.vector):
            raise ValueError(
                "Embedding dimensions do not match vector length."
            )

        if self.index < 0:
            raise ValueError(
                "Embedding index cannot be negative."
            )

    @property
    def dimension(self) -> int:
        """
        Alias for dimensions.
        """

        return self.dimensions


class BaseEmbeddingProvider(ABC):
    """
    Abstract interface implemented by every embedding provider.

    Examples:

    - OpenAI embeddings
    - SentenceTransformers
    - HuggingFace inference
    - Cohere
    - custom local embedding model
    """

    provider_name: str = "base"

    def __init__(
        self,
        config: EmbeddingConfig,
    ) -> None:
        self.config = config

    @abstractmethod
    async def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for a single text.
        """

    @abstractmethod
    async def embed_batch(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """

    async def health_check(self) -> bool:
        """
        Basic provider health check.

        Providers can override this if they have a real remote
        health endpoint.
        """

        try:
            vector = await self.embed("health check")

            return bool(vector)

        except Exception:
            return False

    def validate_vector(
        self,
        vector: Sequence[float],
    ) -> list[float]:
        """
        Validate and normalize a provider response.

        This catches provider/model mismatches early.
        """

        result = [float(value) for value in vector]

        if not result:
            raise ValueError(
                f"{self.provider_name} returned an empty embedding."
            )

        if (
            self.config.dimensions is not None
            and len(result) != self.config.dimensions
        ):
            raise ValueError(
                f"{self.provider_name} returned an embedding with "
                f"{len(result)} dimensions, expected "
                f"{self.config.dimensions}."
            )

        return result

    def prepare_text(self, text: str) -> str:
        """
        Normalize input before sending it to the provider.
        """

        if text is None:
            raise ValueError(
                "Embedding input cannot be None."
            )

        normalized = " ".join(text.split())

        if not normalized:
            raise ValueError(
                "Embedding input cannot be empty."
            )

        return normalized

    @property
    def model(self) -> str:
        return self.config.model

    @property
    def dimensions(self) -> int | None:
        return self.config.dimensions