from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.adaptive_rag.adapters.retrieval import RetrievalAdapter
from app.adaptive_rag.controller import AdaptiveRAGController
from app.api.routes.retrieval import get_retrieval_service
from app.retrieval.service import RetrievalService

from app.explore.schemas import ExploreRequest, ExploreResponse
from app.explore.service import ExploreService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/explore",
    tags=["Explore"],
)


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_adaptive_rag_controller(
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service
    ),
) -> AdaptiveRAGController:
    """
    Build AdaptiveRAGController using the application's shared
    RetrievalService.

    The RetrievalService itself is already connected to the shared
    IndexRegistry.
    """

    return AdaptiveRAGController(
        retrieval_service=RetrievalAdapter(
            retrieval_service
        )
    )


def get_explore_service(
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service
    ),
    adaptive_rag_controller: AdaptiveRAGController = Depends(
        get_adaptive_rag_controller
    ),
) -> ExploreService:
    """
    Build ExploreService from the shared retrieval and Adaptive RAG
    components.

    FastAPI caches dependencies within a request, so the same
    RetrievalService dependency is reused by both branches.
    """

    return ExploreService(
        retrieval_service=retrieval_service,
        adaptive_rag_controller=adaptive_rag_controller,
    )


# ============================================================================
# EXPLORE
# ============================================================================


@router.post(
    "",
    response_model=ExploreResponse,
    status_code=status.HTTP_200_OK,
    summary="Explore the research knowledge base",
    description=(
        "Execute a research exploration query through direct retrieval "
        "or the Adaptive RAG pipeline."
    ),
)
async def explore(
    request: ExploreRequest,
    service: ExploreService = Depends(
        get_explore_service
    ),
) -> ExploreResponse:
    """
    Main Explore API endpoint.

    POST /api/v1/explore

    Execution:

        adaptive=True
            Explore
              ↓
            Adaptive RAG
              ↓
            RetrievalAdapter
              ↓
            RetrievalService
              ↓
            RetrievalPipeline
              ↓
            Shared IndexRegistry

        adaptive=False
            Explore
              ↓
            RetrievalService
              ↓
            RetrievalPipeline
              ↓
            Shared IndexRegistry
    """

    logger.info(
        "POST /explore: query=%r adaptive=%s",
        request.query,
        request.adaptive,
    )

    try:
        result = await service.explore(request)

        response = service.to_response(result)

        logger.info(
            "POST /explore completed: query=%r success=%s",
            request.query,
            response.success,
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Explore validation error: query=%r error=%s",
            request.query,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except LookupError as exc:
        logger.warning(
            "Explore lookup error: query=%r error=%s",
            request.query,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.error(
            "Explore runtime error: query=%r error=%s",
            request.query,
            exc,
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Explore execution failed: query=%r",
            request.query,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Explore execution failed.",
        ) from exc