from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Iterable, List, Optional

from app.assistant.exceptions import AssistantResponseError
from app.assistant.models import (
    AssistantExecution,
    AssistantResponse,
    AssistantSource,
    LLMResponse,
)

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """
    Converts internal LLM/research/retrieval results into
    the stable AssistantResponse contract.
    """

    def build(
        self,
        *,
        content: str,
        mode: str = "chat",
        conversation_id: Optional[str] = None,
        sources: Optional[Iterable[Any]] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "completed",
    ) -> AssistantResponse:
        normalized_content = self._normalize_content(content)

        normalized_sources = self._normalize_sources(sources or [])

        execution_metadata = (
            execution_metadata
            if isinstance(execution_metadata, dict)
            else {}
        )

        metadata = (
            metadata
            if isinstance(metadata, dict)
            else {}
        )

        execution = AssistantExecution(
            mode=mode,
            execution_id=(
                execution_metadata.get("execution_id")
                or str(uuid.uuid4())
            ),
            duration_seconds=float(
                execution_metadata.get(
                    "duration_seconds",
                    0.0,
                )
                or 0.0
            ),
            llm_used=bool(
                execution_metadata.get(
                    "llm_used",
                    False,
                )
            ),
            retrieval_used=bool(
                execution_metadata.get(
                    "retrieval_used",
                    False,
                )
            ),
            research_used=bool(
                execution_metadata.get(
                    "research_used",
                    False,
                )
            ),
            source_count=len(normalized_sources),
            metadata=execution_metadata,
        )

        return AssistantResponse(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message=normalized_content,
            answer=normalized_content,
            response=normalized_content,
            status=status,
            mode=mode,
            sources=normalized_sources,
            execution=execution,
            metadata=metadata,
        )

    # ========================================================================
    # LLM
    # ========================================================================

    def from_llm(
        self,
        response: LLMResponse,
        *,
        conversation_id: Optional[str] = None,
        mode: str = "chat",
        sources: Optional[Iterable[Any]] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> AssistantResponse:
        metadata: Dict[str, Any] = {}

        if response.model:
            metadata["model"] = response.model

        if response.provider:
            metadata["provider"] = response.provider

        if response.usage:
            metadata["usage"] = response.usage

        metadata.update(response.metadata or {})

        return self.build(
            content=response.content,
            mode=mode,
            conversation_id=conversation_id,
            sources=sources,
            execution_metadata=execution_metadata,
            metadata=metadata,
        )

    # ========================================================================
    # CONTENT
    # ========================================================================

    @staticmethod
    def _normalize_content(
        content: Any,
    ) -> str:
        if content is None:
            raise AssistantResponseError(
                "LLM returned an empty response."
            )

        if isinstance(content, str):
            value = content.strip()

        elif isinstance(content, list):
            value = "\n".join(
                str(item)
                for item in content
            ).strip()

        elif isinstance(content, dict):
            value = (
                content.get("content")
                or content.get("message")
                or content.get("text")
                or content.get("output")
                or ""
            )

            value = str(value).strip()

        else:
            value = str(content).strip()

        if not value:
            raise AssistantResponseError(
                "LLM returned an empty response."
            )

        return value

    # ========================================================================
    # SOURCES
    # ========================================================================

    def _normalize_sources(
        self,
        sources: Iterable[Any],
    ) -> List[AssistantSource]:
        result: List[AssistantSource] = []

        for index, item in enumerate(sources):
            try:
                source = self._normalize_source(
                    item,
                    index,
                )

                if source is not None:
                    result.append(source)

            except Exception:
                logger.warning(
                    "Failed to normalize assistant source.",
                    exc_info=True,
                )

        return result

    @staticmethod
    def _normalize_source(
        item: Any,
        index: int,
    ) -> Optional[AssistantSource]:
        if item is None:
            return None

        if isinstance(
            item,
            AssistantSource,
        ):
            return item

        if hasattr(
            item,
            "model_dump",
        ):
            data = item.model_dump()

        elif isinstance(
            item,
            dict,
        ):
            data = dict(item)

        elif hasattr(
            item,
            "__dict__",
        ):
            data = dict(item.__dict__)

        else:
            data = {
                "title": str(item)
            }

        source_id = (
            data.get("id")
            or data.get("source_id")
            or data.get("url")
            or f"source-{index + 1}"
        )

        title = (
            data.get("title")
            or data.get("name")
            or f"Source {index + 1}"
        )

        authors = data.get(
            "authors",
            [],
        )

        if isinstance(
            authors,
            str,
        ):
            authors = [authors]

        if not isinstance(
            authors,
            list,
        ):
            authors = []

        metadata = data.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        score = data.get("score")

        return AssistantSource(
            id=str(source_id),
            title=str(title),
            source_type=str(
                data.get(
                    "source_type",
                    "other",
                )
            ),
            url=(
                str(data["url"])
                if data.get("url")
                else None
            ),
            authors=[
                str(author)
                for author in authors
            ],
            score=(
                float(score)
                if score is not None
                else None
            ),
            metadata=metadata,
        )


def get_response_builder() -> ResponseBuilder:
    """Return a stateless response builder."""

    return ResponseBuilder()
