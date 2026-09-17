"""
Assistant API routes.

HTTP interface for the application assistant.

Architecture:

    HTTP Request
        ↓
    Assistant API Route
        ↓
    app.assistant.service
        ↓
    Assistant orchestration
        ↓
    Adaptive RAG / Research / Retrieval / Generation / LLM

The API layer intentionally contains no business logic.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.assistant.models import AssistantRequest
from app.assistant.service import AssistantService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)


# ============================================================================
# SERVICE DEPENDENCY
# ============================================================================


def get_assistant_service() -> AssistantService:
    """
    Construct the assistant service.

    This dependency is intentionally small for now.

    Once the application has a centralized dependency/container layer,
    this function can be replaced with the application's singleton or
    request-scoped service provider without changing the route contract.
    """
    return AssistantService()


# ============================================================================
# CHAT
# ============================================================================


@router.post(
    "/chat",
    status_code=status.HTTP_200_OK,
    summary="Chat with the AI research assistant",
    description=(
        "Submit a user request to the AI research assistant. "
        "The assistant may use conversation context, retrieval, "
        "Adaptive RAG, research workflows, and LLM generation."
    ),
)
async def chat(
    payload: AssistantRequest,
    request: Request,
    assistant_service: AssistantService = Depends(get_assistant_service),
) -> Any:
    """
    Execute one assistant interaction.

    The route is deliberately thin. All assistant behavior belongs
    to the application assistant layer.
    """

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    try:
        logger.info(
            "Assistant request received | request_id=%s",
            request_id,
        )

        # Keep the API independent from the exact internal method name
        # until the AssistantService contract is finalized.
        result = await assistant_service.respond(payload)

        logger.info(
            "Assistant request completed | request_id=%s",
            request_id,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Assistant request failed | request_id=%s | error=%s",
            request_id,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assistant request failed.",
        ) from exc


# ============================================================================
# HEALTH
# ============================================================================


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check assistant availability",
)
async def assistant_health(
    assistant_service: AssistantService = Depends(get_assistant_service),
) -> dict[str, Any]:
    """
    Lightweight assistant health endpoint.

    This should verify application-level assistant readiness rather
    than performing an expensive LLM request.
    """

    try:
        health_method = getattr(
            assistant_service,
            "health",
            None,
        )

        if callable(health_method):
            result = health_method()

            if hasattr(result, "__await__"):
                result = await result

            if isinstance(result, dict):
                return result

        return {
            "status": "ok",
            "service": "assistant",
        }

    except Exception as exc:
        logger.exception(
            "Assistant health check failed | error=%s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistant service unavailable.",
        ) from exc
