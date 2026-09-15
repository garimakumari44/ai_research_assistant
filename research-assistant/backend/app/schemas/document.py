from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """
    Base schema shared by document request/response models.
    """

    filename: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    content_type: str | None = Field(
        default=None,
        max_length=255,
    )


class DocumentCreate(DocumentBase):
    """
    Schema used when creating a document.
    """

    pass


class DocumentUpdate(BaseModel):
    """
    Schema used when updating document metadata.
    """

    filename: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    content_type: str | None = Field(
        default=None,
        max_length=255,
    )


class DocumentResponse(DocumentBase):
    """
    Schema returned by the API for a document.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None


class DocumentListResponse(BaseModel):
    """
    Response schema for a list of documents.
    """

    items: list[DocumentResponse]
    total: int