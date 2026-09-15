from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.section import Section


class SectionRepository:
    """
    Repository for document sections.

    The database model uses `section_index` as the ordering field and
    `metadata_` as the Python attribute for the `metadata` JSONB column.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        values: dict[str, Any],
    ) -> Section:
        section = Section(**values)

        self.db.add(section)
        await self.db.flush()

        return section

    async def create_for_document(
        self,
        *,
        document_id: UUID,
        section_index: int,
        title: str | None,
        section_type: str = "section",
        level: int = 1,
        content: str,
        page_start: int | None = None,
        page_end: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Section:
        section = Section(
            document_id=document_id,
            section_index=section_index,
            title=title,
            section_type=section_type,
            level=level,
            content=content,
            page_start=page_start,
            page_end=page_end,
            metadata_=metadata or {},
        )

        self.db.add(section)
        await self.db.flush()

        return section

    async def get_by_id(
        self,
        section_id: UUID,
    ) -> Section | None:
        result = await self.db.execute(
            select(Section).where(Section.id == section_id)
        )

        return result.scalar_one_or_none()

    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[Section]:
        result = await self.db.execute(
            select(Section)
            .where(Section.document_id == document_id)
            .order_by(Section.section_index.asc())
        )

        return list(result.scalars().all())

    async def count_by_document_id(
        self,
        document_id: UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Section.id)).where(
                Section.document_id == document_id
            )
        )

        return int(result.scalar_one())

    async def delete_by_document_id(
        self,
        document_id: UUID,
    ) -> int:
        result = await self.db.execute(
            delete(Section).where(
                Section.document_id == document_id
            )
        )

        await self.db.flush()

        return int(result.rowcount or 0)

    async def delete(
        self,
        section_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            delete(Section).where(Section.id == section_id)
        )

        await self.db.flush()

        return bool(result.rowcount)