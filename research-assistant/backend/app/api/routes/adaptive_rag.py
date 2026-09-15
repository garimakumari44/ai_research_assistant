"""
Adaptive RAG API routes.

The API layer is intentionally thin.

Request flow:

Client
  ↓
FastAPI route
  ↓
AdaptiveRAGController
  ↓
Planner
  ↓
Router
  ↓
Strategy
  ↓
Evaluator
  ↓
Controller
  ↓
Response
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.adaptive_rag.controller import AdaptiveRAGController
from app.schemas.adaptive_rag import (
    AdaptiveRAGRequest,
    AdaptiveRAGResponse,
)


router = APIRouter(
    prefix="/adaptive-rag",
    tags=["Adaptive RAG"],
)


def get_adaptive_rag_controller() -> AdaptiveRAGController:
    """
    Dependency provider for AdaptiveRAGController.

    Replace this with your application-level dependency/container
    once the controller is wired into the composition root.
    """

    return AdaptiveRAGController()


@router.post(
    "/query",
    response_model=AdaptiveRAGResponse,
    status_code=status.HTTP_200_OK,
)
async def adaptive_rag_query(
    request: AdaptiveRAGRequest,
    controller: AdaptiveRAGController = Depends(
        get_adaptive_rag_controller
    ),
) -> AdaptiveRAGResponse:
    """
    Execute an Adaptive RAG query.
    """

    try:
        result = await controller.run(
            query=request.query,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            top_k=request.top_k,
            metadata=request.metadata,
        )

        if isinstance(result, AdaptiveRAGResponse):
            return result

        return AdaptiveRAGResponse.model_validate(result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Adaptive RAG execution failed.",
        ) from exc