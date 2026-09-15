from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ======================================================================
# PAPER AUTHOR RESPONSE
# ======================================================================


class PaperAuthorResponse(BaseModel):
    name: str

    author_id: int | str | None = None

    orcid: str | None = None

    email: str | None = None

    affiliation: str | None = None

    position: int | None = None


# ======================================================================
# PAPER BASE
# ======================================================================


class PaperBase(BaseModel):

    title: str

    abstract: str | None = None

    publication_date: date | None = None

    venue: str | None = None

    journal: str | None = None

    conference: str | None = None

    doi: str | None = None

    url: str | None = None

    pdf_url: str | None = None

    language: str | None = None

    keywords: list[str] = Field(
        default_factory=list
    )

    categories: list[str] = Field(
        default_factory=list
    )

    external_ids: dict[str, Any] = Field(
        default_factory=dict
    )

    citation_count: int = Field(
        default=0,
        ge=0,
    )

    reference_count: int = Field(
        default=0,
        ge=0,
    )

    source: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ======================================================================
# PAPER CREATE
# ======================================================================


class PaperCreate(PaperBase):

    authors: list[Any] = Field(
        default_factory=list
    )


# ======================================================================
# PAPER UPDATE
# ======================================================================


class PaperUpdate(BaseModel):

    title: str | None = None

    abstract: str | None = None

    authors: list[Any] | None = None

    publication_date: date | None = None

    venue: str | None = None

    journal: str | None = None

    conference: str | None = None

    doi: str | None = None

    url: str | None = None

    pdf_url: str | None = None

    language: str | None = None

    keywords: list[str] | None = None

    categories: list[str] | None = None

    external_ids: dict[str, Any] | None = None

    citation_count: int | None = Field(
        default=None,
        ge=0,
    )

    reference_count: int | None = Field(
        default=None,
        ge=0,
    )

    source: str | None = None

    metadata: dict[str, Any] | None = None


# ======================================================================
# PAPER INGEST REQUEST
# ======================================================================


class PaperIngestRequest(BaseModel):

    provider: str = Field(
        min_length=1,
        max_length=100,
    )

    external_id: str = Field(
        min_length=1,
        max_length=512,
    )

    @field_validator(
        "provider",
        "external_id",
    )
    @classmethod
    def strip_values(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be empty"
            )

        return value


# ======================================================================
# PAPER RESPONSE
# ======================================================================


class PaperResponse(PaperBase):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int | str

    authors: list[PaperAuthorResponse] = Field(
        default_factory=list
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None

    canonical_key: str | None = None


# ======================================================================
# PAPER SUMMARY
# ======================================================================


class PaperSummary(BaseModel):

    id: int | str

    title: str

    abstract: str | None = None

    publication_date: date | None = None

    venue: str | None = None

    doi: str | None = None

    url: str | None = None

    citation_count: int = Field(
        default=0,
        ge=0,
    )


# ======================================================================
# PAPER LIST RESPONSE
# ======================================================================


class PaperListResponse(BaseModel):

    items: list[PaperResponse] = Field(
        default_factory=list
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    pages: int = Field(
        default=0,
        ge=0,
    )