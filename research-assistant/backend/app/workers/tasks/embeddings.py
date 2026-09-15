from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    """Run an async coroutine inside the synchronous Celery worker."""
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.embeddings.generate_document_embeddings",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def generate_document_embeddings(
    self,
    document_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """
    Generate embeddings for all chunks belonging to a document.
    """

    logger.info(
        "Starting embedding generation",
        extra={
            "document_id": document_id,
            "force": force,
            "task_id": self.request.id,
        },
    )

    try:
        UUID(document_id)
    except ValueError as exc:
        raise ValueError(
            f"Invalid document_id: {document_id}"
        ) from exc

    result = _run(
        _generate_document_embeddings(
            document_id=document_id,
            force=force,
        )
    )

    logger.info(
        "Embedding generation completed",
        extra={
            "document_id": document_id,
            "task_id": self.request.id,
        },
    )

    return {
        "status": "completed",
        "document_id": document_id,
        "result": result,
    }


async def _generate_document_embeddings(
    *,
    document_id: str,
    force: bool,
) -> dict[str, Any]:
    """
    Generate embeddings using the Phase 3 embedding service.
    """

    from sqlalchemy import select

    from app.db.models.chunk import Chunk
    from app.db.session import async_session_factory
    from app.knowledge.embeddings.service import EmbeddingService

    document_uuid = UUID(document_id)

    embedding_service = EmbeddingService()

    async with async_session_factory() as session:
        result = await session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_uuid)
            .order_by(Chunk.chunk_index)
        )

        chunks = list(result.scalars().all())

        if not chunks:
            logger.warning(
                "No chunks found for embedding",
                extra={"document_id": document_id},
            )

            return {
                "chunks_found": 0,
                "embeddings_created": 0,
            }

        processed = 0

        for chunk in chunks:
            if not force and getattr(chunk, "embedding", None) is not None:
                continue

            text = getattr(chunk, "content", None)

            if not text:
                text = getattr(chunk, "text", None)

            if not text:
                logger.warning(
                    "Skipping empty chunk",
                    extra={
                        "document_id": document_id,
                        "chunk_id": str(chunk.id),
                    },
                )
                continue

            embedding = await embedding_service.embed(text)

            chunk.embedding = embedding
            processed += 1

        await session.commit()

    return {
        "chunks_found": len(chunks),
        "embeddings_created": processed,
    }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.embeddings.generate_chunk_embedding",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def generate_chunk_embedding(
    self,
    chunk_id: str,
) -> dict[str, Any]:
    """
    Generate an embedding for one chunk.
    """

    try:
        UUID(chunk_id)
    except ValueError as exc:
        raise ValueError(
            f"Invalid chunk_id: {chunk_id}"
        ) from exc

    result = _run(
        _generate_chunk_embedding(
            chunk_id=chunk_id,
        )
    )

    return {
        "status": "completed",
        "chunk_id": chunk_id,
        "result": result,
    }


async def _generate_chunk_embedding(
    *,
    chunk_id: str,
) -> dict[str, Any]:
    from sqlalchemy import select

    from app.db.models.chunk import Chunk
    from app.db.session import async_session_factory
    from app.knowledge.embeddings.service import EmbeddingService

    chunk_uuid = UUID(chunk_id)

    async with async_session_factory() as session:
        result = await session.execute(
            select(Chunk).where(
                Chunk.id == chunk_uuid
            )
        )

        chunk = result.scalar_one_or_none()

        if chunk is None:
            raise ValueError(
                f"Chunk not found: {chunk_id}"
            )

        text = getattr(chunk, "content", None)

        if not text:
            text = getattr(chunk, "text", None)

        if not text:
            raise ValueError(
                f"Chunk has no text: {chunk_id}"
            )

        embedding_service = EmbeddingService()

        embedding = await embedding_service.embed(text)

        chunk.embedding = embedding

        await session.commit()

    return {
        "chunk_id": chunk_id,
        "embedded": True,
    }