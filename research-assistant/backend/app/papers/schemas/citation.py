from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CitationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_paper_id: str = Field(
        ...,
        min_length=1,
    )

    target_paper_id: str = Field(
        ...,
        min_length=1,
    )

    citation_type: str = Field(
        default="references",
        min_length=1,
        max_length=100,
    )


class CitationCreate(CitationBase):
    pass


class CitationResponse(CitationBase):
    id: str | None = None

    created_at: datetime | None = None