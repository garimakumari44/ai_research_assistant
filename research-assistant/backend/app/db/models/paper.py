from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ============================================================================
# PAPER ↔ AUTHOR
# ============================================================================


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    paper_id: Mapped[int] = mapped_column(
        ForeignKey(
            "papers.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey(
            "authors.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    author_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="author_links",
    )

    author: Mapped["Author"] = relationship(
        "Author",
        back_populates="paper_links",
    )


# ============================================================================
# PAPER ↔ TOPIC
# ============================================================================


class PaperTopic(Base):
    __tablename__ = "paper_topics"

    paper_id: Mapped[int] = mapped_column(
        ForeignKey(
            "papers.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey(
            "topics.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="topic_links",
    )

    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="paper_links",
    )


# ============================================================================
# PAPER ↔ METHOD
# ============================================================================


class PaperMethod(Base):
    __tablename__ = "paper_methods"

    paper_id: Mapped[int] = mapped_column(
        ForeignKey(
            "papers.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    method_id: Mapped[int] = mapped_column(
        ForeignKey(
            "methods.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="method_links",
    )

    method: Mapped["Method"] = relationship(
        "Method",
        back_populates="paper_links",
    )


# ============================================================================
# PAPER ↔ DATASET
# ============================================================================


class PaperDataset(Base):
    __tablename__ = "paper_datasets"

    paper_id: Mapped[int] = mapped_column(
        ForeignKey(
            "papers.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="dataset_links",
    )

    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="paper_links",
    )


# ============================================================================
# PAPER
# ============================================================================


class Paper(Base):
    __tablename__ = "papers"

    __table_args__ = (
        UniqueConstraint(
            "doi",
            name="uq_papers_doi",
        ),
        UniqueConstraint(
            "provider",
            "provider_paper_id",
            name="uq_papers_provider_id",
        ),
    )

    # ========================================================================
    # IDENTITY
    # ========================================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    doi: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        index=True,
    )

    arxiv_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        index=True,
    )

    pmid: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        index=True,
    )

    # ========================================================================
    # PROVIDER
    # ========================================================================

    provider: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    provider_paper_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        index=True,
    )

    # ========================================================================
    # BIBLIOGRAPHIC DATA
    # ========================================================================

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    abstract: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    publication_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    language: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================================
    # VENUE
    # ========================================================================

    venue_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "venues.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================================
    # METRICS
    # ========================================================================

    citation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    reference_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # ========================================================================
    # LINKS
    # ========================================================================

    landing_page_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    pdf_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================================
    # METADATA
    # ========================================================================

    source_metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================================
    # TIMESTAMPS
    # ========================================================================

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

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    venue: Mapped[Optional["Venue"]] = relationship(
        "Venue",
        back_populates="papers",
    )

    author_links: Mapped[List["PaperAuthor"]] = relationship(
        "PaperAuthor",
        back_populates="paper",
        cascade="all, delete-orphan",
        order_by="PaperAuthor.author_order",
    )

    topic_links: Mapped[List["PaperTopic"]] = relationship(
        "PaperTopic",
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    method_links: Mapped[List["PaperMethod"]] = relationship(
        "PaperMethod",
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    dataset_links: Mapped[List["PaperDataset"]] = relationship(
        "PaperDataset",
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    citations_made: Mapped[List["Citation"]] = relationship(
        "Citation",
        foreign_keys="Citation.citing_paper_id",
        back_populates="citing_paper",
        cascade="all, delete-orphan",
    )

    citations_received: Mapped[List["Citation"]] = relationship(
        "Citation",
        foreign_keys="Citation.cited_paper_id",
        back_populates="cited_paper",
    )

    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="paper",
        cascade="all, delete-orphan",
    )