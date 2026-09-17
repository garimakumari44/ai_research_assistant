"""
Adaptive RAG API routes.

The API layer is intentionally thin.

Request flow:

Client
    ↓
FastAPI route
    ↓
Shared IndexRegistry
    ↓
RetrievalService
    ↓
AdaptiveRAGController
    ↓
Planner
    ↓
RAG strategy
    ↓
RetrievalAdapter
    ↓
RetrievalService
    ↓
RetrievalPipeline
    ↓
IndexRegistry
    ↓
Evaluator
    ↓
Response
"""

from __future__ import annotations

import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from app.adaptive_rag.controller import (
    AdaptiveRAGController,
)

from app.knowledge.indexing.registry import (
    IndexRegistry,
)

from app.retrieval.service import (
    RetrievalService,
)

from app.schemas.adaptive_rag import (
    AdaptiveRAGRequest,
    AdaptiveRAGResponse,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/adaptive-rag",
    tags=["Adaptive RAG"],
)


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_index_registry(
    request: Request,
) -> IndexRegistry:
    """
    Return the application's shared IndexRegistry.

    The registry is initialized once during the FastAPI
    application lifespan and stored on app.state.

    IMPORTANT:
    Do not create a new IndexRegistry here.

    Indexing, retrieval, research, and Adaptive RAG must
    operate against the same application-level registry.
    """

    registry = getattr(
        request.app.state,
        "index_registry",
        None,
    )

    if registry is None:
        logger.error(
            "Adaptive RAG requested but app.state.index_registry "
            "is not initialized."
        )

        raise RuntimeError(
            "Shared retrieval IndexRegistry is not initialized."
        )

    return registry


def get_retrieval_service(
    registry: IndexRegistry = Depends(
        get_index_registry,
    ),
) -> RetrievalService:
    """
    Build the canonical RetrievalService using the
    application's shared IndexRegistry.

    This mirrors the dependency used by the normal
    retrieval API and research pipeline.
    """

    return RetrievalService(
        registry=registry,
    )


def get_adaptive_rag_controller(
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service,
    ),
) -> AdaptiveRAGController:
    """
    Build an AdaptiveRAGController with the canonical
    application RetrievalService injected.

    The controller must never be created without retrieval
    dependencies because every retrieval-backed strategy
    depends on RetrievalService.
    """

    return AdaptiveRAGController(
        retrieval_service=retrieval_service,
    )


# ============================================================================
# ADAPTIVE RAG QUERY
# ============================================================================


@router.post(
    "/query",
    response_model=AdaptiveRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an Adaptive RAG query",
    description=(
        "Execute an adaptive retrieval-augmented generation query "
        "using the application's shared retrieval indexes."
    ),
)
async def adaptive_rag_query(
    request: AdaptiveRAGRequest,
    controller: AdaptiveRAGController = Depends(
        get_adaptive_rag_controller,
    ),
) -> AdaptiveRAGResponse:
    """
    Execute an Adaptive RAG query.

    API schema
        ↓
    AdaptiveRAGRequest
        ↓
    AdaptiveRAGController
        ↓
    Planner
        ↓
    Strategy
        ↓
    RetrievalService
        ↓
    RetrievalPipeline
        ↓
    Shared IndexRegistry
        ↓
    AdaptiveRAGResponse
    """

    try:
        result = await controller.run(
            request,
        )

        if isinstance(
            result,
            AdaptiveRAGResponse,
        ):
            return result

        return AdaptiveRAGResponse.model_validate(
            result,
        )

    except ValueError as exc:
        logger.warning(
            "Adaptive RAG validation error: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Adaptive RAG execution failed.",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Adaptive RAG execution failed.",
        )