
from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.reports import (
    ReportCreate,
    ReportListResponse,
    ReportResponse,
    ReportStatus,
    ReportUpdate,
)
from app.services.report_service import ReportService
from app.research.pipeline import ResearchPipeline


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_research_pipeline(
    request: Request,
) -> ResearchPipeline:
    """
    Return the application-wide configured ResearchPipeline.

    Reports must use the same shared retrieval/index infrastructure
    as the main Research endpoint.
    """

    index_registry = getattr(
        request.app.state,
        "index_registry",
        None,
    )

    if index_registry is None:
        raise RuntimeError(
            "Shared IndexRegistry is not initialized."
        )

    # Import here so the route remains compatible with the existing
    # application dependency setup.
    from app.retrieval.service import RetrievalService
    from app.llm.pipeline import get_llm_pipeline

    retrieval_service = RetrievalService(
        registry=index_registry,
    )

    llm_pipeline = get_llm_pipeline()

    return ResearchPipeline(
        retrieval_service=retrieval_service,
        llm_pipeline=llm_pipeline,
    )


def get_report_service(
    db: AsyncSession = Depends(get_db),
    research_pipeline: ResearchPipeline = Depends(
        get_research_pipeline,
    ),
) -> ReportService:
    """
    Create a ReportService with the same configured
    ResearchPipeline used by the Research feature.
    """

    return ReportService(
        db,
        research_pipeline=research_pipeline,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    payload: ReportCreate,
    current_user: CurrentUser,
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """
    Create a new research report shell.
    """

    return await service.create_report(
        user_id=current_user.id,
        data=payload,
    )


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    payload: ReportCreate,
    current_user: CurrentUser,
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """
    Generate an evidence-grounded research synthesis report.
    """

    return await service.generate_report(
        user_id=current_user.id,
        data=payload,
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ReportListResponse,
)
async def list_reports(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    report_status: ReportStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: CurrentUser = None,
    service: ReportService = Depends(get_report_service),
) -> ReportListResponse:
    """
    List the current user's research reports.
    """

    return await service.list_reports(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=report_status,
    )


# ---------------------------------------------------------------------------
# Get one
# ---------------------------------------------------------------------------


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
)
async def get_report(
    report_id: int,
    current_user: CurrentUser,
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """
    Get one research report.
    """

    report = await service.get_report(
        user_id=current_user.id,
        report_id=report_id,
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research report not found",
        )

    return report


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.patch(
    "/{report_id}",
    response_model=ReportResponse,
)
async def update_report(
    report_id: int,
    payload: ReportUpdate,
    current_user: CurrentUser,
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """
    Update a research report.
    """

    report = await service.update_report(
        user_id=current_user.id,
        report_id=report_id,
        data=payload,
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research report not found",
        )

    return report


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_report(
    report_id: int,
    current_user: CurrentUser,
    service: ReportService = Depends(get_report_service),
) -> None:
    """
    Delete a research report.
    """

    deleted = await service.delete_report(
        user_id=current_user.id,
        report_id=report_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research report not found",
        )

    return None

