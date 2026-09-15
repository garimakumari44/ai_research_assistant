from __future__ import annotations

from typing import List

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Method(Base):
    __tablename__ = "methods"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    paper_links: Mapped[List["PaperMethod"]] = relationship(
        "PaperMethod",
        back_populates="method",
        cascade="all, delete-orphan",
    )