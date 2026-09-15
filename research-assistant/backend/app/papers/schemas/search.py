
from __future__ import annotations

from datetime import date

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


# ============================================================================
# PAPER SEARCH REQUEST
# ============================================================================


class PaperSearchRequest(BaseModel):
    """
    Search and filtering contract for papers.

    This schema is shared by:
        - API layer
        - PaperService
        - PaperRepository

    The repository uses this object for database filtering.
    External provider discovery is handled by the service/provider layer.
    """

    # ------------------------------------------------------------------------
    # TEXT
    # ------------------------------------------------------------------------

    query: str | None = Field(
        default=None,
        max_length=1000,
    )

    # ------------------------------------------------------------------------
    # AUTHOR
    # ------------------------------------------------------------------------

    author: str | None = Field(
        default=None,
        max_length=500,
    )

    # ------------------------------------------------------------------------
    # IDENTITY
    # ------------------------------------------------------------------------

    doi: str | None = Field(
        default=None,
        max_length=500,
    )

    # ------------------------------------------------------------------------
    # PROVIDER
    # ------------------------------------------------------------------------

    source: str | None = Field(
        default=None,
        max_length=100,
    )

    provider: str | None = Field(
        default=None,
        max_length=100,
    )

    provider_paper_id: str | None = Field(
        default=None,
        max_length=512,
    )

    # ------------------------------------------------------------------------
    # VENUE
    # ------------------------------------------------------------------------

    venue: str | None = Field(
        default=None,
        max_length=500,
    )

    # ------------------------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------------------------

    category: str | None = Field(
        default=None,
        max_length=255,
    )

    # ------------------------------------------------------------------------
    # YEAR
    # ------------------------------------------------------------------------

    year: int | None = Field(
        default=None,
        ge=1000,
        le=9999,
    )

    # ------------------------------------------------------------------------
    # PUBLICATION DATE RANGE
    # ------------------------------------------------------------------------

    published_from: date | None = None

    published_to: date | None = None

    # ------------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------------

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    # ------------------------------------------------------------------------
    # SORTING
    # ------------------------------------------------------------------------

    sort_by: str = Field(
        default="publication_date",
    )

    sort_order: str = Field(
        default="desc",
    )

    # ========================================================================
    # STRING NORMALIZATION
    # ========================================================================

    @field_validator(
        "query",
        "author",
        "doi",
        "source",
        "provider",
        "provider_paper_id",
        "venue",
        "category",
    )
    @classmethod
    def strip_strings(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize optional string fields.

        Empty strings become None.
        """
        if value is None:
            return None

        value = value.strip()

        return value or None

    # ========================================================================
    # SORT BY
    # ========================================================================

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(
        cls,
        value: str,
    ) -> str:
        """
        Validate and normalize the requested sort field.
        """
        value = value.strip().lower()

        allowed = {
            "publication_date",
            "title",
            "citation_count",
            "created_at",
            "updated_at",
            "year",
        }

        if value not in allowed:
            raise ValueError(
                "sort_by must be one of: "
                "publication_date, title, citation_count, "
                "created_at, updated_at, year"
            )

        return value

    # ========================================================================
    # SORT ORDER
    # ========================================================================

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(
        cls,
        value: str,
    ) -> str:
        """
        Validate and normalize ascending/descending ordering.
        """
        value = value.strip().lower()

        if value not in {
            "asc",
            "desc",
        }:
            raise ValueError(
                "sort_order must be either 'asc' or 'desc'"
            )

        return value

    # ========================================================================
    # DATE RANGE
    # ========================================================================

    @model_validator(mode="after")
    def validate_date_range(self) -> PaperSearchRequest:
        """
        Ensure the publication date range is valid.
        """
        if (
            self.published_from is not None
            and self.published_to is not None
            and self.published_to < self.published_from
        ):
            raise ValueError(
                "published_to cannot be earlier than "
                "published_from"
            )

        return self

    # ========================================================================
    # OFFSET
    # ========================================================================

    @property
    def offset(self) -> int:
        """
        Convert page/page_size into a zero-based database/provider offset.
        """
        return (
            (self.page - 1)
            * self.page_size
        )


# ============================================================================
# SEARCH RESULT
# ============================================================================


class PaperSearchResult(BaseModel):
    """
    Lightweight paper representation returned by search.

    `id` may represent:
        - canonical database ID for locally stored papers
        - provider-specific identifier for external results

    The service is responsible for deciding which identifier to expose.
    """

    # ------------------------------------------------------------------------
    # IDENTITY
    # ------------------------------------------------------------------------

    id: int | str | None = None

    # ------------------------------------------------------------------------
    # CORE METADATA
    # ------------------------------------------------------------------------

    title: str

    abstract: str | None = None

    # ------------------------------------------------------------------------
    # AUTHORS
    # ------------------------------------------------------------------------

    authors: list[str] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------------
    # PUBLICATION
    # ------------------------------------------------------------------------

    publication_date: date | None = None

    venue: str | None = None

    # ------------------------------------------------------------------------
    # IDENTIFIERS
    # ------------------------------------------------------------------------

    doi: str | None = None

    # ------------------------------------------------------------------------
    # URLS
    # ------------------------------------------------------------------------

    url: str | None = None

    pdf_url: str | None = None

    # ------------------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------------------

    citation_count: int = Field(
        default=0,
        ge=0,
    )

    # ------------------------------------------------------------------------
    # SOURCE
    # ------------------------------------------------------------------------

    source: str | None = None

    # ------------------------------------------------------------------------
    # RELEVANCE
    # ------------------------------------------------------------------------

    relevance_score: float | None = None


# ============================================================================
# SEARCH RESPONSE
# ============================================================================


class PaperSearchResponse(BaseModel):
    """
    Paginated paper search response.
    """

    # ------------------------------------------------------------------------
    # RESULTS
    # ------------------------------------------------------------------------

    papers: list[PaperSearchResult] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------------

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

    total_pages: int = Field(
        default=0,
        ge=0,
    )

