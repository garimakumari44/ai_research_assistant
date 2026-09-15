from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================================================
# Collection Paper Summary
# ============================================================================


class CollectionPaperAuthorResponse(BaseModel):
    """
    Minimal author representation used by the Collections UI.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    full_name: str


class CollectionPaperVenueResponse(BaseModel):
    """
    Minimal venue representation used by the Collections UI.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str


class CollectionPaperTopicResponse(BaseModel):
    """
    Minimal topic representation used by the Collections UI.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str


class CollectionPaperSummary(BaseModel):
    """
    Lightweight paper representation embedded in a collection item.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    title: str
    year: int | None = None

    citation_count: int = 0
    reference_count: int = 0

    venue: CollectionPaperVenueResponse | None = None

    authors: list[CollectionPaperAuthorResponse] = Field(
        default_factory=list,
    )

    topics: list[CollectionPaperTopicResponse] = Field(
        default_factory=list,
    )

    @model_validator(mode="before")
    @classmethod
    def flatten_paper_relationships(
        cls,
        value: Any,
    ) -> Any:
        """
        Convert SQLAlchemy Paper relationships into the API shape.

        SQLAlchemy structure:

            paper.author_links
                -> paper_author
                    -> author

            paper.topic_links
                -> paper_topic
                    -> topic

        API structure:

            authors: Author[]
            topics: Topic[]
        """

        if value is None:
            return value

        if isinstance(value, dict):
            return value

        data: dict[str, Any] = {
            "id": value.id,
            "title": value.title,
            "year": value.year,
            "citation_count": value.citation_count,
            "reference_count": value.reference_count,
            "venue": value.venue,
            "authors": [],
            "topics": [],
        }

        author_links = getattr(
            value,
            "author_links",
            None,
        )

        if author_links:
            data["authors"] = [
                link.author
                for link in author_links
                if getattr(link, "author", None) is not None
            ]

        topic_links = getattr(
            value,
            "topic_links",
            None,
        )

        if topic_links:
            data["topics"] = [
                link.topic
                for link in topic_links
                if getattr(link, "topic", None) is not None
            ]

        return data


# ============================================================================
# Collection Items
# ============================================================================


class CollectionItemCreate(BaseModel):
    paper_id: int = Field(
        ...,
        gt=0,
    )


class CollectionItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    collection_id: int
    paper_id: int
    created_at: datetime

    paper: CollectionPaperSummary | None = None


class CollectionItemListResponse(BaseModel):
    items: list[CollectionItemResponse]
    page: int
    page_size: int
    total: int
    pages: int = 0


# ============================================================================
# Collections
# ============================================================================


class CollectionCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    archived: bool = False


class CollectionUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    archived: bool | None = None


class CollectionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int
    name: str
    description: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime

    paper_count: int = 0

    # IMPORTANT:
    # The detail endpoint now returns the actual collection items.
    items: list[CollectionItemResponse] = Field(
        default_factory=list,
    )


class CollectionListResponse(BaseModel):
    items: list[CollectionResponse]
    page: int
    page_size: int
    total: int
    pages: int = 0