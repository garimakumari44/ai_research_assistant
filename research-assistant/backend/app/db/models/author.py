from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    orcid: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    given_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    family_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    affiliation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    author_metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    paper_links: Mapped[List["PaperAuthor"]] = relationship(
        "PaperAuthor",
        back_populates="author",
        cascade="all, delete-orphan",
    )