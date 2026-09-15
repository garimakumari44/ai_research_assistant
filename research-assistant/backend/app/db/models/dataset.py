from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    source_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    paper_links: Mapped[List["PaperDataset"]] = relationship(
        "PaperDataset",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )