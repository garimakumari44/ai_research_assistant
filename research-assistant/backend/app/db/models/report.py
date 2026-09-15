from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchReport(Base):
    """
    Persistent research synthesis report.

    This is the SQLAlchemy database model.

    A report belongs to a user. Research-specific context such as:
    - research project
    - research session
    - selected papers
    - retrieval configuration
    - synthesis configuration
    - generation configuration

    is stored in the JSONB `metadata` database column through the
    Python attribute `report_metadata`.

    NOTE:
    `metadata` cannot be used as a Python ORM attribute because it is
    reserved by SQLAlchemy's Declarative API.
    """

    __tablename__ = "research_reports"

    # ==========================================================
    # PRIMARY KEY
    # ==========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # OWNERSHIP
    # ==========================================================

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # REPORT INFORMATION
    # ==========================================================

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    research_question: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==========================================================
    # REPORT LIFECYCLE
    # ==========================================================

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )

    # Expected values:
    #
    # draft
    # generating
    # completed
    # failed

    # ==========================================================
    # SYNTHESIS SUMMARY
    # ==========================================================

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==========================================================
    # STRUCTURED REPORT CONTENT
    # ==========================================================

    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Example:
    #
    # {
    #     "executive_summary": "...",
    #     "key_findings": [],
    #     "methodology": "...",
    #     "evidence_synthesis": "...",
    #     "contradictions": [],
    #     "research_gaps": [],
    #     "emerging_trends": [],
    #     "future_directions": [],
    #     "conclusion": "...",
    #     "references": []
    # }

    # ==========================================================
    # TRACEABLE EVIDENCE
    # ==========================================================

    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    # ==========================================================
    # RESEARCH / GENERATION METADATA
    # ==========================================================

    # IMPORTANT:
    #
    # Database column:
    #     metadata
    #
    # Python ORM attribute:
    #     report_metadata
    #
    # This avoids SQLAlchemy's reserved `metadata` attribute.

    report_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Example:
    #
    # {
    #     "research_project_id": 12,
    #     "research_session_id": 8,
    #     "paper_ids": [1, 2, 3],
    #     "retrieval_strategy": "adaptive",
    #     "generation_model": "...",
    #     "temperature": 0.2
    # }

    # ==========================================================
    # TIMESTAMPS
    # ==========================================================

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

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # RELATIONSHIPS
    # ==========================================================

    user = relationship(
        "User",
        back_populates="research_reports",
    )

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self) -> str:
        return (
            f"<ResearchReport "
            f"id={self.id} "
            f"title={self.title!r} "
            f"status={self.status!r}>"
        )