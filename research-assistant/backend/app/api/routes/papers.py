from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logging
from app.db.session import get_db

from app.ingestion.providers.arxiv import ArxivProvider
from app.ingestion.providers.openalex import OpenAlexProvider
from app.ingestion.providers.manager import ProviderManager

from app.papers.schemas.paper import (
    PaperCreate,
    PaperIngestRequest,
    PaperListResponse,
    PaperResponse,
)
from app.papers.schemas.search import PaperSearchResponse

from app.papers.service import (
    PaperAlreadyExistsError,
    PaperNotFoundError,
    PaperService,
)

from app.repositories.paper_repository import PaperRepository


router = APIRouter(
    prefix="/papers",
    tags=["Papers"],
)


# ============================================================================
# DEPENDENCY
# ============================================================================


def get_paper_service(
    db: AsyncSession = Depends(get_db),
) -> PaperService:
    """
    Create a request-scoped PaperService.

    The repository receives the current AsyncSession.

    ProviderManager contains the metadata providers used by
    the paper ingestion pipeline.

    Provider priority:
        1. OpenAlex
        2. arXiv

    OpenAlex is currently the primary discovery provider because
    it is responding reliably to search requests. arXiv remains
    available as a secondary provider.
    """

    repository = PaperRepository(
        session=db,
    )

    provider_manager = ProviderManager(
        providers=[
            OpenAlexProvider(),
            ArxivProvider(),
        ],
    )

    return PaperService(
        repository=repository,
        provider_manager=provider_manager,
    )


# ============================================================================
# GET /papers
# ============================================================================


@router.get(
    "",
    response_model=PaperListResponse,
    summary="List papers",
)
async def list_papers(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    query: str | None = Query(
        default=None,
        max_length=1000,
    ),
    year: int | None = Query(
        default=None,
        ge=1,
    ),
    author: str | None = Query(
        default=None,
        max_length=500,
    ),
    doi: str | None = Query(
        default=None,
        max_length=500,
    ),
    source: str | None = Query(
        default=None,
        max_length=100,
    ),
    provider: str | None = Query(
        default=None,
        max_length=100,
    ),
    provider_paper_id: str | None = Query(
        default=None,
        max_length=512,
    ),
    venue: str | None = Query(
        default=None,
        max_length=500,
    ),
    category: str | None = Query(
        default=None,
        max_length=255,
    ),
    published_from: date | None = Query(
        default=None,
    ),
    published_to: date | None = Query(
        default=None,
    ),
    sort_by: str = Query(
        default="publication_date",
    ),
    sort_order: str = Query(
        default="desc",
    ),
    service: PaperService = Depends(
        get_paper_service,
    ),
) -> PaperListResponse:

    if (
        published_from is not None
        and published_to is not None
        and published_from > published_to
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="published_from cannot be after published_to",
        )

    try:
        return await service.list_papers(
            page=page,
            page_size=page_size,
            query=query,
            year=year,
            venue=venue,
            author=author,
            doi=doi,
            source=source,
            provider=provider,
            provider_paper_id=provider_paper_id,
            category=category,
            published_from=published_from,
            published_to=published_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logging.exception(
            "Failed to list papers",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve papers",
        )


# ============================================================================
# POST /papers
# ============================================================================


@router.post(
    "",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create paper",
)
async def create_paper(
    request: PaperCreate,
    service: PaperService = Depends(
        get_paper_service,
    ),
) -> PaperResponse:

    try:
        paper = await service.create(
            request,
        )

        return PaperService._to_response(
            paper,
        )

    except PaperAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logging.exception(
            "Failed to create paper",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create paper",
        )


# ============================================================================
# GET /papers/search
#
# IMPORTANT:
# This route must remain before /{paper_id}.
#
# q is intentionally optional because the frontend uses this endpoint
# to load the initial paper catalog before the user enters a search term.
# ============================================================================


@router.get(
    "/search",
    response_model=PaperSearchResponse,
    summary="Search papers",
)
async def search_papers(
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=1000,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    year: int | None = Query(
        default=None,
        ge=1,
    ),
    author: str | None = Query(
        default=None,
        max_length=500,
    ),
    doi: str | None = Query(
        default=None,
        max_length=500,
    ),
    source: str | None = Query(
        default=None,
        max_length=100,
    ),
    provider: str | None = Query(
        default=None,
        max_length=100,
    ),
    provider_paper_id: str | None = Query(
        default=None,
        max_length=512,
    ),
    venue: str | None = Query(
        default=None,
        max_length=500,
    ),
    category: str | None = Query(
        default=None,
        max_length=255,
    ),
    published_from: date | None = Query(
        default=None,
    ),
    published_to: date | None = Query(
        default=None,
    ),
    sort_by: str = Query(
        default="publication_date",
    ),
    sort_order: str = Query(
        default="desc",
    ),
    service: PaperService = Depends(
        get_paper_service,
    ),
) -> PaperSearchResponse:

    if (
        published_from is not None
        and published_to is not None
        and published_from > published_to
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="published_from cannot be after published_to",
        )

    try:
        return await service.search_papers(
            query=q,
            page=page,
            page_size=page_size,
            year=year,
            venue=venue,
            author=author,
            doi=doi,
            source=source,
            provider=provider,
            provider_paper_id=provider_paper_id,
            category=category,
            published_from=published_from,
            published_to=published_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logging.exception(
            "Failed to search papers",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search papers",
        )


# ============================================================================
# POST /papers/ingest
#
# IMPORTANT:
# This route must remain before /{paper_id}.
# ============================================================================


@router.post(
    "/ingest",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest paper",
)
async def ingest_paper(
    request: PaperIngestRequest,
    service: PaperService = Depends(
        get_paper_service,
    ),
) -> PaperResponse:

    provider = request.provider.strip().lower()
    external_id = request.external_id.strip()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider is required",
        )

    if not external_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="External ID is required",
        )

    try:
        logging.info(
            "Starting paper ingestion",
            extra={
                "provider": provider,
                "external_id": external_id,
            },
        )

        paper = await service.ingest_paper(
            provider=provider,
            external_id=external_id,
        )

        logging.info(
            "Paper ingestion completed",
            extra={
                "provider": provider,
                "external_id": external_id,
            },
        )

        return PaperService._to_response(
            paper,
        )

    except PaperAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except PaperNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logging.exception(
            "Paper ingestion failed",
            extra={
                "provider": provider,
                "external_id": external_id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Paper ingestion failed",
        )


# ============================================================================
# GET /papers/{paper_id}
# ============================================================================


@router.get(
    "/{paper_id}",
    response_model=PaperResponse,
    summary="Get paper",
)
async def get_paper(
    paper_id: int,
    service: PaperService = Depends(
        get_paper_service,
    ),
) -> PaperResponse:

    try:
        paper = await service.get_paper(
            paper_id,
        )

    except PaperNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logging.exception(
            "Failed to retrieve paper",
            extra={
                "paper_id": str(paper_id),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve paper",
        )

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {paper_id} not found",
        )

    return PaperService._to_response(
        paper,
    )


# ============================================================================
# DELETE /papers/{paper_id}
# ============================================================================


@router.delete(
    "/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete paper",
)
async def delete_paper(
    paper_id: int,
    service: PaperService = Depends(
        get_paper_service,
    ),
) -> None:

    try:
        deleted = await service.delete_paper(
            paper_id,
        )

    except PaperNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logging.exception(
            "Failed to delete paper",
            extra={
                "paper_id": str(paper_id),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete paper",
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {paper_id} not found",
        )

    return None