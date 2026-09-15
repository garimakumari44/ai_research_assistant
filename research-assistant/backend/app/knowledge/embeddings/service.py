from __future__ import annotations

from typing import Any, Mapping, Sequence
from uuid import UUID

from app.knowledge.chunking.base import Chunk
from app.knowledge.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingResult,
)
from app.knowledge.embeddings.provider import (
    EmbeddingProvider,
)


class EmbeddingService:
    """
    Application-level embedding service.

    This service sits between the RAG pipeline and concrete
    embedding providers.

    It should not know anything about PostgreSQL, pgvector,
    Qdrant, Pinecone, or other vector stores.
    """

    def __init__(
        self,
        provider: BaseEmbeddingProvider,
    ) -> None:
        self.provider = provider

    @classmethod
    def from_registry(
        cls,
        registry: EmbeddingProvider,
        provider_name: str,
        config: EmbeddingConfig,
    ) -> "EmbeddingService":
        """
        Construct an EmbeddingService using the provider registry.
        """

        provider = registry.create(
            provider_name,
            config,
        )

        return cls(provider)

    @property
    def provider_name(self) -> str:
        return self.provider.provider_name

    @property
    def model(self) -> str:
        return self.provider.model

    @property
    def dimensions(self) -> int | None:
        return self.provider.dimensions

    async def embed(
        self,
        text: str,
        *,
        document_id: UUID | str | None = None,
        chunk_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
        index: int = 0,
    ) -> EmbeddingResult:
        """
        Generate an embedding for one piece of text.
        """

        prepared = self.provider.prepare_text(text)

        vector = await self.provider.embed(
            prepared
        )

        vector = self.provider.validate_vector(
            vector
        )

        dimensions = len(vector)

        return EmbeddingResult(
            vector=vector,
            model=self.model,
            dimensions=dimensions,
            index=index,
            text=prepared,
            document_id=document_id,
            chunk_id=chunk_id,
            metadata=dict(metadata or {}),
        )

    async def embed_batch(
        self,
        texts: Sequence[str],
        *,
        document_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
        start_index: int = 0,
    ) -> list[EmbeddingResult]:
        """
        Generate embeddings for a batch of texts.

        The service splits large requests according to the
        configured batch size.
        """

        if not texts:
            return []

        prepared_texts = [
            self.provider.prepare_text(text)
            for text in texts
        ]

        batch_size = self.provider.config.batch_size

        results: list[EmbeddingResult] = []

        for batch_start in range(
            0,
            len(prepared_texts),
            batch_size,
        ):
            batch_texts = prepared_texts[
                batch_start: batch_start + batch_size
            ]

            vectors = await self.provider.embed_batch(
                batch_texts
            )

            if len(vectors) != len(batch_texts):
                raise ValueError(
                    "Embedding provider returned "
                    f"{len(vectors)} vectors for "
                    f"{len(batch_texts)} inputs."
                )

            for offset, (
                text,
                vector,
            ) in enumerate(
                zip(
                    batch_texts,
                    vectors,
                    strict=True,
                )
            ):
                validated = (
                    self.provider.validate_vector(
                        vector
                    )
                )

                results.append(
                    EmbeddingResult(
                        vector=validated,
                        model=self.model,
                        dimensions=len(validated),
                        index=(
                            start_index
                            + batch_start
                            + offset
                        ),
                        text=text,
                        document_id=document_id,
                        metadata=dict(
                            metadata or {}
                        ),
                    )
                )

        return results

    async def embed_chunks(
        self,
        chunks: Sequence[Chunk],
    ) -> list[EmbeddingResult]:
        """
        Generate embeddings directly from Phase 3 Chunk objects.

        This creates the bridge between:

            knowledge.chunking
                    ↓
            knowledge.embeddings
        """

        if not chunks:
            return []

        texts = [
            chunk.text
            for chunk in chunks
        ]

        document_id = chunks[0].document_id

        embeddings = await self.embed_batch(
            texts,
            document_id=document_id,
        )

        for embedding, chunk in zip(
            embeddings,
            chunks,
            strict=True,
        ):
            embedding.chunk_id = (
                chunk.metadata.get("chunk_id")
            )

            embedding.metadata.update(
                {
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    "section_id": (
                        str(chunk.section_id)
                        if chunk.section_id
                        else None
                    ),
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "token_count": chunk.token_count,
                }
            )

        return embeddings

    async def health_check(self) -> bool:
        """
        Check whether the configured provider is usable.
        """

        return await self.provider.health_check()

    def describe(self) -> dict[str, Any]:
        """
        Return provider configuration metadata.

        Useful for logging and diagnostics.
        """

        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "batch_size": (
                self.provider.config.batch_size
            ),
            "normalize": (
                self.provider.config.normalize
            ),
        }