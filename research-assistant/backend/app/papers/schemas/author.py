from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthorBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=500)

    author_id: str | None = Field(
        default=None,
        max_length=255,
    )

    orcid: str | None = Field(
        default=None,
        max_length=100,
    )

    email: str | None = Field(
        default=None,
        max_length=320,
    )

    affiliation: str | None = Field(
        default=None,
        max_length=1000,
    )

    position: int = Field(
        default=0,
        ge=0,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Author name cannot be empty")

        return value

    @field_validator("orcid")
    @classmethod
    def normalize_orcid(cls, value: str | None) -> str | None:
        if not value:
            return None

        value = value.strip()

        prefixes = (
            "https://orcid.org/",
            "http://orcid.org/",
        )

        for prefix in prefixes:
            if value.lower().startswith(prefix):
                value = value[len(prefix):]
                break

        return value or None


class AuthorCreate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    pass