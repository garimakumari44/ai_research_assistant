from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.cleanup.cleanup_failed_jobs",
)
def cleanup_failed_jobs(
    self,
    *,
    older_than_hours: int = 24,
) -> dict[str, Any]:
    """
    Clean up old failed processing records/jobs.

    The exact persistence model is intentionally kept out of this
    worker until the job model is finalized.
    """

    if older_than_hours <= 0:
        raise ValueError(
            "older_than_hours must be greater than zero"
        )

    logger.info(
        "Starting failed-job cleanup",
        extra={
            "older_than_hours": older_than_hours,
            "task_id": self.request.id,
        },
    )

    result = _run(
        _cleanup_failed_jobs(
            older_than_hours=older_than_hours,
        )
    )

    return {
        "status": "completed",
        "result": result,
    }


async def _cleanup_failed_jobs(
    *,
    older_than_hours: int,
) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=older_than_hours
    )

    logger.info(
        "Cleaning failed jobs older than cutoff",
        extra={"cutoff": cutoff.isoformat()},
    )

    # Add database cleanup once the worker/job persistence model exists.

    return {
        "deleted": 0,
        "cutoff": cutoff.isoformat(),
    }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.cleanup.cleanup_orphaned_chunks",
)
def cleanup_orphaned_chunks(
    self,
) -> dict[str, Any]:
    """
    Remove chunks whose parent document no longer exists.
    """

    logger.info(
        "Starting orphaned chunk cleanup",
        extra={"task_id": self.request.id},
    )

    result = _run(
        _cleanup_orphaned_chunks()
    )

    return {
        "status": "completed",
        "result": result,
    }


async def _cleanup_orphaned_chunks() -> dict[str, Any]:
    """
    Delete chunks that reference missing documents.

    Uses a database-level NOT EXISTS query so the cleanup remains
    efficient for large knowledge bases.
    """

    from sqlalchemy import delete, exists, select

    from app.db.models.chunk import Chunk
    from app.db.models.document import Document
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        orphan_condition = ~exists(
            select(Document.id).where(
                Document.id == Chunk.document_id
            )
        )

        result = await session.execute(
            delete(Chunk).where(orphan_condition)
        )

        await session.commit()

        deleted = result.rowcount or 0

    logger.info(
        "Orphaned chunk cleanup completed",
        extra={"deleted": deleted},
    )

    return {
        "deleted": deleted,
    }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.cleanup.cleanup_expired_data",
)
def cleanup_expired_data(
    self,
    *,
    older_than_days: int = 30,
) -> dict[str, Any]:
    """
    General maintenance task for expired temporary data.
    """

    if older_than_days <= 0:
        raise ValueError(
            "older_than_days must be greater than zero"
        )

    logger.info(
        "Starting expired-data cleanup",
        extra={
            "older_than_days": older_than_days,
            "task_id": self.request.id,
        },
    )

    result = _run(
        _cleanup_expired_data(
            older_than_days=older_than_days,
        )
    )

    return {
        "status": "completed",
        "result": result,
    }


async def _cleanup_expired_data(
    *,
    older_than_days: int,
) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=older_than_days
    )

    # Add cleanup of temporary ingestion artifacts, stale processing
    # records, and other TTL-based entities here.

    return {
        "deleted": 0,
        "cutoff": cutoff.isoformat(),
    }