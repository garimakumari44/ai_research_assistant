
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUserId
from app.db.models.collection import Collection
from app.db.models.collection_item import CollectionItem
from app.db.models.document import Document
from app.db.models.research_execution import ResearchExecution
from app.db.models.research_project import ResearchProject
from app.db.models.research_result import ResearchResult
from app.db.session import get_db
from app.llm.pipeline import get_llm_pipeline
from app.research.models import ResearchQuery, ResearchReport
from app.research.pipeline import ResearchPipeline
from app.retrieval.service import RetrievalService


logger = logging.getLogger(__name__)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/research",
    tags=["Research"],
)


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_research_pipeline(
    request: Request,
) -> ResearchPipeline:
    """
    Create a request-scoped ResearchPipeline using the application's
    shared retrieval indexes and canonical LLM pipeline.

    The IndexRegistry is created and restored during application startup
    and stored on app.state.index_registry.

    IMPORTANT:
        Do not create a new IndexRegistry here.

    Creating a new registry would bypass the application's restored
    indexes and result in an empty retrieval system.
    """

    index_registry = getattr(
        request.app.state,
        "index_registry",
        None,
    )

    if index_registry is None:
        logger.error(
            "Research pipeline requested but the shared "
            "IndexRegistry is not initialized."
        )

        raise RuntimeError(
            "Shared retrieval IndexRegistry is not initialized."
        )

    retrieval_service = RetrievalService(
        registry=index_registry,
    )

    llm_pipeline = get_llm_pipeline()

    pipeline = ResearchPipeline(
        retrieval_service=retrieval_service,
        llm_pipeline=llm_pipeline,
    )

    logger.debug(
        "ResearchPipeline created: registry=%s provider=%s",
        type(index_registry).__name__,
        getattr(
            llm_pipeline,
            "provider_name",
            "unknown",
        ),
    )

    return pipeline


# ============================================================================
# HELPERS
# ============================================================================


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def extract_research_question(
    request: ResearchQuery,
) -> str:
    """
    Extract the user's research question from ResearchQuery.

    The ResearchQuery model has changed during development, so this
    helper deliberately supports the canonical field as well as older
    field names.

    Preferred field:
        research_question

    Supported legacy fields:
        query
        question
        prompt

    Raises:
        ValueError:
            If no usable research question exists.
    """

    # Preferred/current field.
    candidates: tuple[str, ...] = (
        "research_question",
        "query",
        "question",
        "prompt",
    )

    for field_name in candidates:
        value = getattr(request, field_name, None)

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

    raise ValueError(
        "A research question is required."
    )


def build_project_slug(
    query: str,
) -> str:
    """
    Generate a deterministic URL-safe project slug.

    Examples:
        Compare LoRA and QLoRA
            -> compare-lora-and-qlora

        What is RAG?
            -> what-is-rag
    """

    normalized = query.lower().strip()

    slug = re.sub(
        r"\s+",
        "-",
        normalized,
    )

    slug = re.sub(
        r"[^a-z0-9-]",
        "",
        slug,
    )

    slug = re.sub(
        r"-+",
        "-",
        slug,
    )

    slug = slug.strip("-")

    return slug[:240] or "research-project"


async def build_unique_project_slug(
    db: AsyncSession,
    query: str,
) -> str:
    """
    Build a unique project slug.

    The first occurrence keeps the base slug.

    If the base slug already exists, a numeric suffix is appended.
    """

    base_slug = build_project_slug(query)

    existing = await db.scalar(
        select(ResearchProject.id).where(
            ResearchProject.slug == base_slug,
        )
    )

    if existing is None:
        return base_slug

    suffix = 2

    while True:
        suffix_text = f"-{suffix}"

        candidate = (
            f"{base_slug[:240 - len(suffix_text)]}"
            f"{suffix_text}"
        )

        existing = await db.scalar(
            select(ResearchProject.id).where(
                ResearchProject.slug == candidate,
            )
        )

        if existing is None:
            return candidate

        suffix += 1


def report_to_result_data(
    report: ResearchReport,
) -> dict[str, Any]:
    """
    Convert a ResearchReport into JSON-compatible database data.
    """

    return report.model_dump(
        mode="json",
    )


def normalize_error_message(
    error: Exception,
    max_length: int = 5000,
) -> str:
    """
    Convert an exception into a safe database-friendly message.
    """

    message = str(error).strip()

    if not message:
        message = error.__class__.__name__

    return message[:max_length]


async def resolve_collection_document_ids(
    db: AsyncSession,
    *,
    collection_id: int,
    user_id: int,
) -> list[str]:
    """
    Resolve document IDs belonging to an authenticated user's collection.

    Relationship:

        Collection
            |
            v
        CollectionItem
            |
            v
          Paper
            |
            v
        Document

    The collection ownership check is performed before resolving
    documents so a user cannot use another user's collection ID.
    """

    # ------------------------------------------------------------------------
    # 1. Verify collection ownership
    # ------------------------------------------------------------------------

    collection = await db.scalar(
        select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
    )

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge-base collection not found.",
        )

    # ------------------------------------------------------------------------
    # 2. Resolve documents through collection items -> papers
    # ------------------------------------------------------------------------

    result = await db.scalars(
        select(Document.id)
        .join(
            CollectionItem,
            CollectionItem.paper_id == Document.paper_id,
        )
        .where(
            CollectionItem.collection_id == collection_id,
        )
        .distinct()
    )

    document_ids = [
        str(document_id)
        for document_id in result.all()
        if document_id is not None
    ]

    # ------------------------------------------------------------------------
    # 3. Reject empty knowledge-base scopes
    # ------------------------------------------------------------------------

    if not document_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected knowledge-base collection "
                "does not contain any documents."
            ),
        )

    logger.info(
        "Resolved collection documents: "
        "collection_id=%s user_id=%s document_count=%s",
        collection_id,
        user_id,
        len(document_ids),
    )

    return document_ids


# ============================================================================
# POST /api/v1/research
# ============================================================================


@router.post(
    "",
    response_model=ResearchReport,
    status_code=status.HTTP_200_OK,
    summary="Run research",
)
async def run_research(
    request: ResearchQuery,
    current_user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
    pipeline: ResearchPipeline = Depends(get_research_pipeline),
) -> ResearchReport:
    """
    Execute the complete research workflow and persist the execution.

    Flow with collection_id:

        ResearchQuery
             |
             v
        Validate user
             |
             v
        Extract research question
             |
             v
        Validate collection ownership
             |
             v
        Collection -> Papers -> Documents
             |
             v
        allowed_document_ids
             |
             v
        ResearchPipeline
             |
             +-------------------------+
             |                         |
             v                         v
        Shared Retrieval           LLM Pipeline
        IndexRegistry              OpenRouter
             |                         |
             +------------+------------+
                          |
                          v
                    ResearchReport
                          |
                          v
                    ResearchResult

    Without collection_id, the existing global research behavior is retained.
    """

    # =========================================================================
    # 1. Validate authenticated user
    # =========================================================================

    try:
        user_id = int(current_user_id)

    except (TypeError, ValueError) as exc:
        logger.warning(
            "Invalid authenticated user ID: %r",
            current_user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user ID.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    if user_id <= 0:
        logger.warning(
            "Authenticated user ID must be positive: %s",
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user ID.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # =========================================================================
    # 2. Extract and validate research question
    # =========================================================================

    try:
        research_question = extract_research_question(
            request,
        )

    except ValueError as exc:
        logger.warning(
            "Research request contains no valid research question: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if len(research_question) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Research query must contain at least "
                "3 characters."
            ),
        )

    logger.info(
        "Research request received: "
        "user_id=%s collection_id=%s query=%r",
        user_id,
        getattr(request, "collection_id", None),
        research_question,
    )

    # =========================================================================
    # 3. Resolve optional knowledge-base scope
    # =========================================================================

    allowed_document_ids: list[str] | None = None

    collection_id = getattr(
        request,
        "collection_id",
        None,
    )

    if collection_id is not None:
        if collection_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid knowledge-base collection ID.",
            )

        allowed_document_ids = (
            await resolve_collection_document_ids(
                db,
                collection_id=collection_id,
                user_id=user_id,
            )
        )

        logger.info(
            "Collection-scoped research: "
            "collection_id=%s document_count=%s",
            collection_id,
            len(allowed_document_ids),
        )

    else:
        logger.info(
            "Research request has no collection scope."
        )

    # =========================================================================
    # 4. Create unique research project
    # =========================================================================

    slug = await build_unique_project_slug(
        db,
        research_question,
    )

    project = ResearchProject(
        user_id=user_id,
        slug=slug,
        title=research_question[:500],
        research_question=research_question,
        description=None,
        status="active",
    )

    db.add(project)

    await db.flush()

    logger.info(
        "Created research project: "
        "project_id=%s user_id=%s slug=%s",
        project.id,
        user_id,
        project.slug,
    )

    # =========================================================================
    # 5. Create research execution
    # =========================================================================

    execution = ResearchExecution(
        project_id=project.id,
        status="running",
        query=research_question,
        started_at=utc_now(),
    )

    db.add(execution)

    await db.flush()

    logger.info(
        "Created research execution: "
        "project_id=%s execution_id=%s",
        project.id,
        execution.id,
    )

    # =========================================================================
    # 6. Run research pipeline
    # =========================================================================

    try:
        logger.info(
            "Starting research pipeline: "
            "project_id=%s execution_id=%s "
            "depth=%s papers=%s github=%s docs=%s "
            "collection_id=%s scoped_documents=%s",
            project.id,
            execution.id,
            getattr(request, "depth", None),
            getattr(request, "include_papers", None),
            getattr(request, "include_github", None),
            getattr(request, "include_docs", None),
            collection_id,
            (
                len(allowed_document_ids)
                if allowed_document_ids is not None
                else None
            ),
        )

        report = await pipeline.run(
            request,
            allowed_document_ids=allowed_document_ids,
        )

        # =====================================================================
        # 7. Validate pipeline result
        # =====================================================================

        if not isinstance(
            report,
            ResearchReport,
        ):
            raise TypeError(
                "ResearchPipeline.run() must return "
                "a ResearchReport instance."
            )

        logger.info(
            "Research pipeline returned report: "
            "project_id=%s execution_id=%s "
            "status=%s sources=%s evidence=%s citations=%s",
            project.id,
            execution.id,
            report.status,
            len(report.sources),
            len(report.evidence),
            len(report.citations),
        )

        # =====================================================================
        # 8. Persist research result
        # =====================================================================

        result = ResearchResult(
            project_id=project.id,
            execution_id=execution.id,
            result_type="report",
            title=report.title,
            content=report.summary,
            data=report_to_result_data(report),
        )

        db.add(result)

        # =====================================================================
        # 9. Complete execution
        # =====================================================================

        execution.status = "completed"
        execution.completed_at = utc_now()
        execution.error_message = None

        await db.flush()

        logger.info(
            "Research execution completed: "
            "project_id=%s execution_id=%s "
            "report_status=%s source_count=%s",
            project.id,
            execution.id,
            report.status,
            len(report.sources),
        )

        return report

    # =========================================================================
    # Expected validation errors
    # =========================================================================

    except ValueError as exc:
        error_message = normalize_error_message(
            exc,
        )

        logger.warning(
            "Research validation failed: "
            "project_id=%s execution_id=%s error=%s",
            project.id,
            execution.id,
            error_message,
        )

        execution.status = "failed"
        execution.completed_at = utc_now()
        execution.error_message = error_message

        await db.flush()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        ) from exc

    # =========================================================================
    # Pipeline contract errors
    # =========================================================================

    except TypeError as exc:
        error_message = normalize_error_message(
            exc,
        )

        logger.exception(
            "Research pipeline contract error: "
            "project_id=%s execution_id=%s error=%s",
            project.id,
            execution.id,
            error_message,
        )

        execution.status = "failed"
        execution.completed_at = utc_now()
        execution.error_message = error_message

        await db.flush()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Research pipeline returned an invalid result.",
        ) from exc

    # =========================================================================
    # Unexpected errors
    # =========================================================================

    except Exception as exc:
        error_message = normalize_error_message(
            exc,
        )

        logger.exception(
            "Research execution failed: "
            "project_id=%s execution_id=%s error=%s",
            project.id,
            execution.id,
            error_message,
        )

        execution.status = "failed"
        execution.completed_at = utc_now()
        execution.error_message = error_message

        await db.flush()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Research execution failed.",
        ) from exc
