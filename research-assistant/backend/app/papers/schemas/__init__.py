# app/papers/schemas/__init__.py

from app.papers.schemas.author import (
    AuthorBase,
    AuthorCreate,
    AuthorResponse,
)

from app.papers.schemas.citation import (
    CitationBase,
    CitationCreate,
    CitationResponse,
)

from app.papers.schemas.paper import (
    PaperAuthorResponse,
    PaperBase,
    PaperCreate,
    PaperListResponse,
    PaperResponse,
    PaperSummary,
    PaperUpdate,
)

from app.papers.schemas.search import (
    PaperSearchRequest,
    PaperSearchResponse,
    PaperSearchResult,
)


__all__ = [
    # Author
    "AuthorBase",
    "AuthorCreate",
    "AuthorResponse",

    # Citation
    "CitationBase",
    "CitationCreate",
    "CitationResponse",

    # Paper
    "PaperAuthorResponse",
    "PaperBase",
    "PaperCreate",
    "PaperListResponse",
    "PaperResponse",
    "PaperSummary",
    "PaperUpdate",

    # Search
    "PaperSearchRequest",
    "PaperSearchResponse",
    "PaperSearchResult",
]