"""
Public assistant facade.

The Assistant class is the application-facing API.

Complex execution is delegated to AssistantOrchestrator.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.assistant.models import (
    AssistantRequest,
    AssistantResponse,
)
from app.assistant.orchestrator import (
    AssistantOrchestrator,
)


logger = logging.getLogger(__name__)


class Assistant:
    """
    Public assistant facade.

    Responsibilities:

        - provide a stable application API
        - construct AssistantRequest objects
        - delegate execution to AssistantOrchestrator
    """

    def __init__(
        self,
        *,
        orchestrator: Optional[
            AssistantOrchestrator
        ] = None,
    ) -> None:

        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else AssistantOrchestrator()
        )

    # ========================================================================
    # GENERIC RESPONSE
    # ========================================================================

    async def respond(
        self,
        request: AssistantRequest,
    ) -> AssistantResponse:
        """
        Generate an assistant response.
        """

        return await self.orchestrator.run(
            request
        )

    # ========================================================================
    # CHAT
    # ========================================================================

    async def chat(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        history: Optional[list[Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AssistantResponse:
        """
        Convenience chat interface.
        """

        request = AssistantRequest(
            query=message,
            conversation_id=conversation_id,
            mode="chat",
            messages=history or [],
            retrieval_enabled=False,
            use_retrieval=False,
            research=False,
            research_enabled=False,
            use_research=False,
            metadata=metadata or {},
        )

        return await self.respond(
            request
        )

    # ========================================================================
    # RESEARCH
    # ========================================================================

    async def research(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AssistantResponse:
        """
        Convenience research interface.
        """

        request = AssistantRequest(
            query=message,
            conversation_id=conversation_id,
            mode="research",
            research=True,
            research_enabled=True,
            use_research=True,
            retrieval_enabled=False,
            use_retrieval=False,
            metadata=metadata or {},
        )

        return await self.respond(
            request
        )

    # ========================================================================
    # RAG
    # ========================================================================

    async def rag(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AssistantResponse:
        """
        Convenience retrieval-augmented interface.
        """

        request = AssistantRequest(
            query=message,
            conversation_id=conversation_id,
            mode="rag",
            retrieval_enabled=True,
            use_retrieval=True,
            research=False,
            research_enabled=False,
            use_research=False,
            metadata=metadata or {},
        )

        return await self.respond(
            request
        )


# ============================================================================
# DEFAULT ASSISTANT
# ============================================================================


_default_assistant: Optional[
    Assistant
] = None


def get_assistant(
    *,
    orchestrator: Optional[
        AssistantOrchestrator
    ] = None,
) -> Assistant:
    """
    Return the application-level Assistant.

    A singleton is used when dependency injection is not explicitly
    requested.
    """

    global _default_assistant

    if orchestrator is not None:
        return Assistant(
            orchestrator=orchestrator
        )

    if _default_assistant is None:
        _default_assistant = Assistant()

    return _default_assistant


__all__ = [
    "Assistant",
    "get_assistant",
]