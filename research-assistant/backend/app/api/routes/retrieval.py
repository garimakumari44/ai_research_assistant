from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from app.knowledge.indexing.registry import (
    IndexRegistry,
)

from app.retrieval.models import (
    RetrievalQuery,
)

from app.retrieval.service import (
    RetrievalService,
)

from app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
)


router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
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
    """

    registry = getattr(
        request.app.state,
        "index_registry",
        None,
    )

    if registry is None:

        raise RuntimeError(
            "Application IndexRegistry has not been initialized."
        )

    return registry


def get_retrieval_service(
    registry: IndexRegistry = Depends(
        get_index_registry
    ),
) -> RetrievalService:
    """
    Build RetrievalService using the shared IndexRegistry.
    """

    return RetrievalService(
        registry=registry,
    )


# ============================================================================
# SEARCH
# ============================================================================


@router.post(
    "/search",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Search the research knowledge base",
    description=(
        "Execute the research retrieval pipeline over "
        "the available knowledge base."
    ),
)
async def search_knowledge(
    payload: RetrievalRequest,
    service: RetrievalService = Depends(
        get_retrieval_service
    ),
) -> RetrievalResponse:
    """
    Execute the retrieval pipeline.

    API schema
        ↓
    RetrievalQuery
        ↓
    RetrievalService
        ↓
    API response
    """

    try:

        # ------------------------------------------------------------------
        # API schema → internal retrieval model
        # ------------------------------------------------------------------

        filters: dict[str, object] = {}

        if payload.paper_id is not None:

            filters[
                "paper_id"
            ] = str(
                payload.paper_id
            )

        if payload.document_id is not None:

            filters[
                "document_id"
            ] = str(
                payload.document_id
            )

        query = RetrievalQuery(
            query=payload.query,
            top_k=payload.top_k,
            vector_weight=payload.vector_weight,
            keyword_weight=payload.keyword_weight,
            filters=filters,
        )

        # ------------------------------------------------------------------
        # Execute retrieval
        # ------------------------------------------------------------------

        result = await service.search(
            query
        )

        # ------------------------------------------------------------------
        # Internal response → API response
        # ------------------------------------------------------------------

        return service.to_api_response(
            result
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(
                exc
            ),
        ) from exc

    except LookupError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exc
            ),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(
                exc
            ),
        ) from exc


__all__ = [
    "router",
]