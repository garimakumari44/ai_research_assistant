from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.db.models.document import Document
from app.db.session import AsyncSessionLocal
from app.documents.service import DocumentService
from app.ingestion.documents.downloader import DocumentDownloader
from app.ingestion.documents.extractor import DocumentExtractor
from app.ingestion.documents.parser import DocumentParser
from app.ingestion.documents.resolver import DocumentResolver
from app.ingestion.documents.storage import DocumentStorage
from app.knowledge.chunking.semantic import SemanticChunker
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.paper_repository import PaperRepository
from app.repositories.section_repository import SectionRepository
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    """
    Run an async coroutine from a synchronous Celery task.
    """
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.ingest_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def ingest_document(
    self,
    document_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """
    Process one existing Document.

    The Celery task itself remains synchronous while all database
    and ingestion work is executed inside an async coroutine.
    """
    try:
        document_uuid = UUID(str(document_id))
    except (TypeError, ValueError) as exc:
        logger.exception(
            "Invalid document UUID: %s",
            document_id,
        )
        raise ValueError(
            f"Invalid document UUID: {document_id!r}"
        ) from exc

    logger.info(
        "Starting document ingestion task: "
        "document_id=%s force=%s",
        document_uuid,
        force,
    )

    result = _run(
        _ingest_document(
            document_id=document_uuid,
            force=force,
        )
    )

    logger.info(
        "Document ingestion task completed: "
        "document_id=%s result=%s",
        document_uuid,
        result,
    )

    return result


async def _ingest_document(
    *,
    document_id: UUID,
    force: bool,
) -> dict[str, Any]:
    """
    Load a Document and delegate ingestion to DocumentService.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        document = result.scalar_one_or_none()

        if document is None:
            raise ValueError(
                f"Document {document_id} does not exist."
            )

        if document.paper_id is None:
            raise ValueError(
                f"Document {document_id} has no paper_id."
            )

        logger.info(
            "Loaded document for ingestion: "
            "document_id=%s paper_id=%s",
            document.id,
            document.paper_id,
        )

        paper_repository = PaperRepository(db)
        document_repository = DocumentRepository(db)
        section_repository = SectionRepository(db)
        chunk_repository = ChunkRepository(db)

        service = DocumentService(
            paper_repository=paper_repository,
            document_repository=document_repository,
            section_repository=section_repository,
            chunk_repository=chunk_repository,
            document_resolver=DocumentResolver(),
            document_downloader=DocumentDownloader(),
            document_storage=DocumentStorage(),
            document_extractor=DocumentExtractor(),
            document_parser=DocumentParser(),
            chunker=SemanticChunker(),
        )

        try:
            ingestion_result = await service.ingest_document(
                document_id=document_id,
                force=force,
            )

            await db.commit()

            logger.info(
                "Document ingestion committed successfully: "
                "document_id=%s result=%s",
                document_id,
                ingestion_result,
            )

            return ingestion_result

        except Exception:
            await db.rollback()

            logger.exception(
                "Document ingestion failed: "
                "document_id=%s",
                document_id,
            )

            raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.ingest_paper_documents",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def ingest_paper_documents(
    self,
    paper_id: int | str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """
    Queue ingestion for all documents belonging to a paper.
    """
    try:
        normalized_paper_id = int(paper_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid paper_id: {paper_id!r}"
        ) from exc

    logger.info(
        "Queueing document ingestion for paper: "
        "paper_id=%s force=%s",
        normalized_paper_id,
        force,
    )

    return _run(
        _queue_paper_documents(
            paper_id=normalized_paper_id,
            force=force,
        )
    )


async def _queue_paper_documents(
    *,
    paper_id: int,
    force: bool,
) -> dict[str, Any]:
    """
    Find all Documents belonging to a paper and enqueue one
    ingestion task for each document.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document)
            .where(
                Document.paper_id == paper_id
            )
            .order_by(
                Document.created_at.asc()
            )
        )

        documents = list(
            result.scalars().all()
        )

        if not documents:
            logger.warning(
                "No documents found for paper_id=%s",
                paper_id,
            )

            return {
                "status": "no_documents",
                "paper_id": paper_id,
                "queued": 0,
                "document_ids": [],
            }

        document_ids: list[str] = []

        for document in documents:
            document_id = str(document.id)

            ingest_document.delay(
                document_id,
                force=force,
            )

            document_ids.append(
                document_id
            )

            logger.info(
                "Queued document ingestion: "
                "paper_id=%s document_id=%s force=%s",
                paper_id,
                document_id,
                force,
            )

        return {
            "status": "queued",
            "paper_id": paper_id,
            "queued": len(document_ids),
            "document_ids": document_ids,
        }