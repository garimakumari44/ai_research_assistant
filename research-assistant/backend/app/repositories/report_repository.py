from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.report import ResearchReport


class ReportRepository:
    """
    Database access layer for research reports.

    This layer is responsible only for persistence.
    Authentication, RAG orchestration, LLM calls, and business
    decisions belong to the service layer.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        *,
        user_id: int,
        title: str,
        research_question: str | None = None,
        status: str = "draft",
        summary: str | None = None,
        content: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchReport:
        """
        Create a new research report.

        The caller is responsible for committing the transaction.
        """

        report = ResearchReport(
            user_id=user_id,
            title=title,
            research_question=research_question,
            status=status,
            summary=summary,
            content=content or {},
            evidence=evidence or [],
            report_metadata=metadata or {},
        )

        self.db.add(report)

        await self.db.flush()
        await self.db.refresh(report)

        return report

    # ============================================================
    # GET
    # ============================================================

    async def get_by_id(
        self,
        *,
        report_id: int,
        user_id: int,
    ) -> ResearchReport | None:
        """
        Fetch one report belonging to the authenticated user.
        """

        result = await self.db.execute(
            select(ResearchReport).where(
                ResearchReport.id == report_id,
                ResearchReport.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    # ============================================================
    # LIST
    # ============================================================

    async def list(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[ResearchReport], int]:
        """
        Return paginated reports for a user.

        Returns:
            (
                reports,
                total_count,
            )
        """

        offset = (page - 1) * page_size

        conditions = [
            ResearchReport.user_id == user_id,
        ]

        if status is not None:
            conditions.append(
                ResearchReport.status == status
            )

        # --------------------------------------------------------
        # COUNT
        # --------------------------------------------------------

        count_result = await self.db.execute(
            select(
                func.count(ResearchReport.id)
            ).where(
                *conditions
            )
        )

        total = int(
            count_result.scalar_one() or 0
        )

        # --------------------------------------------------------
        # DATA
        # --------------------------------------------------------

        result = await self.db.execute(
            select(ResearchReport)
            .where(*conditions)
            .order_by(
                ResearchReport.updated_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        reports = list(
            result.scalars().all()
        )

        return reports, total

    # ============================================================
    # UPDATE
    # ============================================================

    async def update(
        self,
        report: ResearchReport,
        *,
        title: str | None = None,
        research_question: str | None = None,
        status: str | None = None,
        summary: str | None = None,
        content: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        completed_at: datetime | None = None,
    ) -> ResearchReport:
        """
        Update an existing report.

        Only values explicitly supplied by the service are changed.
        The transaction is flushed here but committed by the service.
        """

        if title is not None:
            report.title = title

        if research_question is not None:
            report.research_question = research_question

        if status is not None:
            report.status = status

        if summary is not None:
            report.summary = summary

        if content is not None:
            report.content = content

        if evidence is not None:
            report.evidence = evidence

        if metadata is not None:
            report.report_metadata = metadata

        if completed_at is not None:
            report.completed_at = completed_at

        await self.db.flush()
        await self.db.refresh(report)

        return report

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        *,
        report_id: int,
        user_id: int,
    ) -> bool:
        """
        Delete a report belonging to the authenticated user.

        Returns:
            True  -> a report was deleted
            False -> no matching report existed
        """

        result = await self.db.execute(
            delete(ResearchReport).where(
                ResearchReport.id == report_id,
                ResearchReport.user_id == user_id,
            )
        )

        deleted = (result.rowcount or 0) > 0

        await self.db.flush()

        return bool(deleted)