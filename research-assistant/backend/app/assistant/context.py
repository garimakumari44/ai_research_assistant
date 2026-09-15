"""
Conversation context management for the assistant layer.

This module manages in-memory conversation and execution state.

Persistence is intentionally outside this module.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, List

from app.assistant.models import (
    AssistantContext,
    AssistantMessage,
    AssistantRequest,
    AssistantSource,
)

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Manages conversation history and assistant execution context.
    """

    def __init__(
        self,
        *,
        max_messages: int = 30,
    ) -> None:
        if max_messages < 1:
            raise ValueError(
                "max_messages must be greater than zero."
            )

        self.max_messages = max_messages

    # ========================================================================
    # BUILD
    # ========================================================================

    def build(
        self,
        request: AssistantRequest,
    ) -> AssistantContext:
        """
        Build execution context from an assistant request.
        """

        context = request.build_context()

        context.messages = self._trim_history(
            list(request.messages)
        )

        context.metadata.setdefault(
            "conversation_id",
            request.conversation_id,
        )

        return context

    # ========================================================================
    # MESSAGE MANAGEMENT
    # ========================================================================

    def append_user_message(
        self,
        context: AssistantContext,
    ) -> None:
        """
        Append the current user query to the conversation.
        """

        context.messages.append(
            AssistantMessage(
                role="user",
                content=context.query,
            )
        )

        context.messages = self._trim_history(
            context.messages
        )

        context.touch()

    def append_assistant_message(
        self,
        context: AssistantContext,
        content: str,
    ) -> None:
        """
        Append an assistant response.
        """

        if not content:
            return

        context.messages.append(
            AssistantMessage(
                role="assistant",
                content=content,
            )
        )

        context.messages = self._trim_history(
            context.messages
        )

        context.touch()

    # ========================================================================
    # RETRIEVAL
    # ========================================================================

    def add_retrieved_context(
        self,
        context: AssistantContext,
        items: Iterable[Any],
    ) -> None:
        """
        Add retrieved items to the runtime context.
        """

        if items is None:
            return

        context.retrieved_context.extend(
            list(items)
        )

        context.touch()

    # ========================================================================
    # SOURCES
    # ========================================================================

    def add_source(
        self,
        context: AssistantContext,
        source: AssistantSource,
    ) -> None:
        """
        Add a source if it has not already been added.
        """

        existing_ids = {
            item.id
            for item in context.sources
            if item.id is not None
        }

        if (
            source.id is None
            or source.id not in existing_ids
        ):
            context.sources.append(source)
            context.touch()

    def add_sources(
        self,
        context: AssistantContext,
        sources: Iterable[AssistantSource],
    ) -> None:
        """
        Add multiple sources while avoiding duplicates.
        """

        if sources is None:
            return

        for source in sources:
            self.add_source(
                context,
                source,
            )

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _trim_history(
        self,
        messages: List[AssistantMessage],
    ) -> List[AssistantMessage]:
        """
        Keep only the most recent messages.
        """

        if len(messages) <= self.max_messages:
            return messages

        return messages[
            -self.max_messages:
        ]


def build_assistant_context(
    request: AssistantRequest,
    *,
    max_messages: int = 30,
) -> AssistantContext:
    """
    Convenience helper for building assistant context.
    """

    manager = ConversationContext(
        max_messages=max_messages
    )

    return manager.build(request)


__all__ = [
    "ConversationContext",
    "build_assistant_context",
]