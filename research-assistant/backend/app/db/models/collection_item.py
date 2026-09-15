from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.collection import Collection
    from app.db.models.paper import Paper


class CollectionItem(Base):
    """
    Represents the relationship between a collection and a paper.

    A paper can appear only once inside the same collection.
    """

    __tablename__ = "collection_items"

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "paper_id",
            name="uq_collection_item_collection_paper",
        ),
    )

    # ========================================================================
    # Primary key
    # ========================================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ========================================================================
    # Collection
    # ========================================================================

    collection_id: Mapped[int] = mapped_column(
        ForeignKey(
            "collections.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="items",
    )

    # ========================================================================
    # Paper
    # ========================================================================

    paper_id: Mapped[int] = mapped_column(
        ForeignKey(
            "papers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # IMPORTANT:
    # selectin loading prevents SQLAlchemy from trying to perform
    # asynchronous lazy-loading while FastAPI/Pydantic is serializing
    # the response.
    paper: Mapped["Paper"] = relationship(
        "Paper",
        lazy="selectin",
    )

    # ========================================================================
    # Timestamp
    # ========================================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )