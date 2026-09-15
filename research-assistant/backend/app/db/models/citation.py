from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Citation(Base):
    __tablename__ = "citations"

    __table_args__ = (
        UniqueConstraint(
            "citing_paper_id",
            "cited_paper_id",
            name="uq_citation_pair",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    citing_paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cited_paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    citation_context: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    citing_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[citing_paper_id],
        back_populates="citations_made",
    )

    cited_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[cited_paper_id],
        back_populates="citations_received",
    )