
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Research Query
# ============================================================================


class ResearchQuery(BaseModel):
    """
    User research request.

    Examples:
        "Compare LoRA and QLoRA fine tuning methods"
        "What are the latest approaches to RAG evaluation?"
        "Explain transformer architecture and its limitations"

    Canonical request field:
        question

    IMPORTANT:
        `question` is the public API field sent by the frontend.

        Internal research pipeline objects may continue to use `query`
        where appropriate. The API request itself must use `question`.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    question: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Research question from the user",
    )

    depth: Literal[
        "basic",
        "medium",
        "deep",
    ] = Field(
        default="medium",
        description="Research depth",
    )

    include_papers: bool = Field(
        default=True,
        description="Search academic papers",
    )

    include_github: bool = Field(
        default=True,
        description="Search GitHub implementations",
    )

    include_docs: bool = Field(
        default=True,
        description="Search official documentation",
    )

    collection_id: Optional[int] = Field(
        default=None,
        description=(
            "Knowledge-base collection to restrict research "
            "retrieval to"
        ),
    )


# ============================================================================
# Research Source
# ============================================================================


class ResearchSource(BaseModel):
    """
    Represents any information source.

    Examples:
        - arXiv paper
        - GitHub repository
        - Documentation page
        - Web page
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: str = Field(
        ...,
        description="Unique source identifier",
    )

    title: str = Field(
        ...,
        description="Source title",
    )

    source_type: Literal[
        "paper",
        "github",
        "documentation",
        "web",
        "other",
    ] = Field(
        default="other",
        description="Type of source",
    )

    url: Optional[str] = Field(
        default=None,
        description="Source URL",
    )

    authors: List[str] = Field(
        default_factory=list,
        description="Authors if available",
    )

    content: str = Field(
        default="",
        description="Extracted source content",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source metadata",
    )


# ============================================================================
# Retrieved Document
# ============================================================================


class RetrievedDocument(BaseModel):
    """
    Document returned from the retrieval pipeline.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: str = Field(
        ...,
        description="Unique retrieved document ID",
    )

    source: ResearchSource = Field(
        ...,
        description="Source associated with the document",
    )

    text: str = Field(
        ...,
        description="Retrieved text chunk",
    )

    score: float = Field(
        default=0.0,
        description="Retrieval relevance score",
    )

    chunk_id: Optional[str] = Field(
        default=None,
        description="Chunk identifier",
    )


# ============================================================================
# Evidence
# ============================================================================


class Evidence(BaseModel):
    """
    A piece of supporting research evidence.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: str = Field(
        ...,
        description="Unique evidence identifier",
    )

    claim: str = Field(
        ...,
        description="Claim supported by the evidence",
    )

    supporting_text: str = Field(
        ...,
        description="Original supporting evidence",
    )

    source_id: str = Field(
        ...,
        description="Source supporting this evidence",
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evidence confidence score",
    )

    relevance_score: float = Field(
        default=0.0,
        description="Evidence relevance score",
    )


# ============================================================================
# Citation
# ============================================================================


class Citation(BaseModel):
    """
    Generated citation reference.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: str = Field(
        ...,
        description="Unique citation identifier",
    )

    source_id: str = Field(
        ...,
        description="Source identifier",
    )

    title: str = Field(
        ...,
        description="Cited source title",
    )

    authors: List[str] = Field(
        default_factory=list,
        description="Authors if available",
    )

    year: Optional[int] = Field(
        default=None,
        ge=0,
        description="Publication year",
    )

    citation_text: str = Field(
        ...,
        description="Human-readable citation",
    )

    url: Optional[str] = Field(
        default=None,
        description="Source URL",
    )


# ============================================================================
# Comparison Result
# ============================================================================


class ComparisonResult(BaseModel):
    """
    Structured comparison result.

    Example:
        LoRA vs QLoRA
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    topic: str = Field(
        ...,
        description="Topic being compared",
    )

    criteria: List[str] = Field(
        default_factory=list,
        description="Comparison criteria",
    )

    comparison_table: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Comparison rows",
    )


# ============================================================================
# Research Section
# ============================================================================


class ResearchSection(BaseModel):
    """
    Individual research report section.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    title: str = Field(
        ...,
        description="Section title",
    )

    content: str = Field(
        ...,
        description="Section content",
    )

    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence IDs supporting this section",
    )


# ============================================================================
# Research Report
# ============================================================================


class ResearchReport(BaseModel):
    """
    Final generated research output.

    Returned directly by:

        POST /api/v1/research
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    title: str = Field(
        ...,
        description="Research report title",
    )

    summary: str = Field(
        ...,
        description="Executive summary",
    )

    sections: List[ResearchSection] = Field(
        default_factory=list,
        description="Research report sections",
    )

    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations used in the report",
    )

    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Supporting evidence",
    )

    sources: List[ResearchSource] = Field(
        default_factory=list,
        description="Research sources",
    )

    comparison: Optional[ComparisonResult] = Field(
        default=None,
        description="Structured comparison when applicable",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pipeline and execution metadata",
    )

    status: Literal[
        "completed",
        "partial",
        "failed",
    ] = Field(
        default="completed",
        description="Report generation status",
    )

