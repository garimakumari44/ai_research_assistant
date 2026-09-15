from __future__ import annotations

import logging
from typing import Any, Optional

from app.assistant.assistant import (
    Assistant,
    get_assistant,
)
from app.assistant.models import (
    AssistantRequest,
    AssistantResponse,
)

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Application service for assistant operations.

    API routes should depend on this service rather than directly
    interacting with the LLM provider.
    """

    def __init__(
        self,
        *,
        assistant: Optional[Assistant] = None,
    ) -> None:
        self.assistant = (
            assistant
            or get_assistant()
        )

    async def respond(
        self,
        request: AssistantRequest,
    ) -> AssistantResponse:
        """
        Main application-level assistant entry point.
        """

        logger.info(
            "Processing assistant request "
            "conversation_id=%s mode=%s",
            request.conversation_id,
            request.mode,
        )

        return await self.assistant.respond(
            request
        )

    async def chat(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        history: Optional[list[Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AssistantResponse:
        return await self.assistant.chat(
            message,
            conversation_id=conversation_id,
            history=history,
            metadata=metadata,
        )

    async def research(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AssistantResponse:
        return await self.assistant.research(
            message,
            conversation_id=conversation_id,
            metadata=metadata,
        )

    async def rag(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AssistantResponse:
        return await self.assistant.rag(
            message,
            conversation_id=conversation_id,
            metadata=metadata,
        )


_default_service: Optional[
    AssistantService
] = None


def get_assistant_service(
    *,
    assistant: Optional[Assistant] = None,
) -> AssistantService:
    """
    Return the application-level AssistantService.
    """

    global _default_service

    if assistant is not None:
        return AssistantService(
            assistant=assistant
        )

    if _default_service is None:
        _default_service = AssistantService()

    return _default_service


async def run_assistant(
    request: AssistantRequest,
) -> AssistantResponse:
    """
    Convenience function for application code.
    """

    service = get_assistant_service()

    return await service.respond(
        request
    )