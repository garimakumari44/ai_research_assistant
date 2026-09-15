from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document


class DocumentRepository:
    """
    Repository responsible for database operations on Document records.

    This repository only handles persistence.

    Document downloading, extraction, parsing, chunking, embedding,
    and indexing belong to the ingestion/indexing layers.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(
        self,
        values: dict[str, Any],
    ) -> Document:
        """
        Create a Document from ORM-compatible values.
        """

        document = Document(**values)

        self.db.add(document)

        await self.db.flush()
        await self.db.refresh(document)

        return document

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:
        """
        Fetch a document by UUID.
        """

        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_paper_id(
        self,
        paper_id: int,
    ) -> Document | None:
        """
        Fetch the canonical document associated with a paper.

        The current schema technically allows multiple documents for
        the same paper. Paper ingestion treats the earliest-created
        document as the canonical document.
        """

        result = await self.db.execute(
            select(Document)
            .where(
                Document.paper_id == paper_id
            )
            .order_by(
                Document.created_at.asc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def list_by_paper_id(
        self,
        paper_id: int,
    ) -> list[Document]:
        """
        Return all documents associated with a paper.
        """

        result = await self.db.execute(
            select(Document)
            .where(
                Document.paper_id == paper_id
            )
            .order_by(
                Document.created_at.asc()
            )
        )

        return list(result.scalars().all())

    async def list_documents(
        self,
        paper_id: int | None = None,
    ) -> Sequence[Document]:
        """
        Return documents ordered by newest first.

        When paper_id is provided, only documents belonging to that
        paper are returned.

        Examples:
            list_documents()
                -> all documents

            list_documents(paper_id=7)
                -> documents belonging to paper 7
        """

        query = (
            select(Document)
            .order_by(
                Document.created_at.desc()
            )
        )

        if paper_id is not None:
            query = query.where(
                Document.paper_id == paper_id
            )

        result = await self.db.execute(query)

        return result.scalars().all()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(
        self,
        document: Document,
    ) -> Document:
        """
        Persist changes to an existing Document.
        """

        self.db.add(document)

        await self.db.flush()
        await self.db.refresh(document)

        return document

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(
        self,
        document_id: UUID,
    ) -> bool:
        """
        Delete a document by UUID.

        Returns:
            True if a document was deleted.
            False if the document did not exist.
        """

        result = await self.db.execute(
            delete(Document).where(
                Document.id == document_id
            )
        )

        deleted = bool(
            result.rowcount
        )

        await self.db.flush()

        return deleted

    # ------------------------------------------------------------------
    # Backwards-compatible aliases
    # ------------------------------------------------------------------

    async def get_document(
        self,
        document_id: UUID,
    ) -> Document | None:
        """
        Backwards-compatible alias for get_by_id().
        """

        return await self.get_by_id(
            document_id
        )

    async def delete_document(
        self,
        document_id: UUID,
    ) -> bool:
        """
        Backwards-compatible alias for delete().
        """

        return await self.delete(
            document_id
        )