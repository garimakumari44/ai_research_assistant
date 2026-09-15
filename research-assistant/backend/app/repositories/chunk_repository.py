from __future__ import annotations

from typing import Any, Iterable
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chunk import Chunk


class ChunkRepository:
    """
    Repository for persisted document chunks.

    This repository translates application-level chunk data into the
    actual SQLAlchemy Chunk model.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        values: dict[str, Any],
    ) -> Chunk:
        chunk = Chunk(
            document_id=values["document_id"],
            section_id=values["section_id"],
            chunk_index=values["chunk_index"],
            content=values["content"],
            page_number=values.get("page_number"),
            token_count=values.get("token_count"),
            metadata_=values.get("metadata_", values.get("metadata", {})),
        )

        self.db.add(chunk)
        await self.db.flush()

        return chunk

    async def create_many(
        self,
        values_list: Iterable[dict[str, Any]],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []

        for values in values_list:
            chunk = Chunk(
                document_id=values["document_id"],
                section_id=values["section_id"],
                chunk_index=values["chunk_index"],
                content=values["content"],
                page_number=values.get("page_number"),
                token_count=values.get("token_count"),
                metadata_=values.get(
                    "metadata_",
                    values.get("metadata", {}),
                ),
            )

            self.db.add(chunk)
            chunks.append(chunk)

        if chunks:
            await self.db.flush()

        return chunks

    async def get_by_id(
        self,
        chunk_id: UUID,
    ) -> Chunk | None:
        result = await self.db.execute(
            select(Chunk).where(Chunk.id == chunk_id)
        )

        return result.scalar_one_or_none()

    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[Chunk]:
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(
                Chunk.section_id.asc(),
                Chunk.chunk_index.asc(),
            )
        )

        return list(result.scalars().all())

    async def list_by_section_id(
        self,
        section_id: UUID,
    ) -> list[Chunk]:
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.section_id == section_id)
            .order_by(Chunk.chunk_index.asc())
        )

        return list(result.scalars().all())

    async def count_by_document(
        self,
        document_id: UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Chunk.id)).where(
                Chunk.document_id == document_id
            )
        )

        return int(result.scalar_one())

    async def count_by_section(
        self,
        section_id: UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Chunk.id)).where(
                Chunk.section_id == section_id
            )
        )

        return int(result.scalar_one())

    async def delete_by_document_id(
        self,
        document_id: UUID,
    ) -> int:
        result = await self.db.execute(
            delete(Chunk).where(
                Chunk.document_id == document_id
            )
        )

        await self.db.flush()

        return int(result.rowcount or 0)

    async def delete_by_section_id(
        self,
        section_id: UUID,
    ) -> int:
        result = await self.db.execute(
            delete(Chunk).where(
                Chunk.section_id == section_id
            )
        )

        await self.db.flush()

        return int(result.rowcount or 0)

    async def delete(
        self,
        chunk_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            delete(Chunk).where(Chunk.id == chunk_id)
        )

        await self.db.flush()

        return bool(result.rowcount)