from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================
# STATUS
# ============================================================


class ReportStatus(str, Enum):
    """
    Lifecycle state of a research report.
    """

    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


# ============================================================
# EVIDENCE
# ============================================================


class ReportEvidence(BaseModel):
    """
    Traceable evidence used by a research report.

    `chunk_id` is intentionally a string because document chunks
    in the research system may use UUID identifiers.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    paper_id: int | None = None

    chunk_id: str | None = None

    citation_key: str | None = None

    title: str | None = None

    authors: list[str] = Field(
        default_factory=list
    )

    year: int | None = None

    source: str | None = None

    quote: str | None = None

    evidence: str | None = None

    relevance_score: float | None = None


# ============================================================
# CONTENT
# ============================================================


class ReportContent(BaseModel):
    """
    Structured body of a generated research report.

    All fields are JSON serializable so the object can be stored
    directly in PostgreSQL JSON/JSONB.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    executive_summary: str | None = None

    key_findings: list[str] = Field(
        default_factory=list
    )

    methodology: str | None = None

    evidence_synthesis: str | None = None

    supporting_evidence: list[dict[str, Any]] = Field(
        default_factory=list
    )

    contradictions: list[str] = Field(
        default_factory=list
    )

    research_gaps: list[str] = Field(
        default_factory=list
    )

    emerging_trends: list[str] = Field(
        default_factory=list
    )

    future_directions: list[str] = Field(
        default_factory=list
    )

    conclusion: str | None = None

    references: list[dict[str, Any]] = Field(
        default_factory=list
    )


# ============================================================
# CREATE
# ============================================================


class ReportCreate(BaseModel):
    """
    Request used for creating or generating a research report.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    research_question: str | None = None

    paper_ids: list[int] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# UPDATE
# ============================================================


class ReportUpdate(BaseModel):
    """
    Partial report update.
    """

    title: str | None = None

    research_question: str | None = None

    status: ReportStatus | None = None

    summary: str | None = None

    content: ReportContent | None = None

    evidence: list[ReportEvidence] | None = None

    metadata: dict[str, Any] | None = None


# ============================================================
# RESPONSE
# ============================================================


class ReportResponse(BaseModel):
    """
    API representation of a research report.

    The database model uses `report_metadata`, while the public
    API exposes that field as `metadata`.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int

    user_id: int

    title: str

    research_question: str | None

    status: ReportStatus

    summary: str | None

    content: dict[str, Any]

    evidence: list[dict[str, Any]]

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="report_metadata",
        serialization_alias="metadata",
    )

    created_at: datetime

    updated_at: datetime

    completed_at: datetime | None


# ============================================================
# LIST ITEM
# ============================================================


class ReportListItem(BaseModel):
    """
    Lightweight report representation for report history.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    title: str

    research_question: str | None

    status: ReportStatus

    summary: str | None

    created_at: datetime

    updated_at: datetime

    completed_at: datetime | None


# ============================================================
# LIST RESPONSE
# ============================================================


class ReportListResponse(BaseModel):
    """
    Paginated report history response.
    """

    items: list[ReportListItem]

    total: int

    page: int

    page_size: int

    pages: int