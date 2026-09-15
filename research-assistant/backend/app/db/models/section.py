from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.chunk import Chunk
    from app.db.models.document import Document


class Section(Base):
    """
    A logical section of a research document.

    Sections preserve the document's structural hierarchy and provide
    context for downstream chunking, retrieval, and citation.
    """

    __tablename__ = "document_sections"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "section_index",
            name="uq_document_sections_document_index",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    section_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    section_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    page_start: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    page_end: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="sections",
    )

    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="section",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )