"""
Assistant orchestration.

Coordinates:

    request
       |
       +--> mode resolution
       |
       +--> research
       |
       +--> retrieval
       |
       +--> prompt construction
       |
       +--> LLM execution
       |
       +--> response normalization
       |
       v
    AssistantResponse
"""

from __future__ import annotations

import inspect
import logging
import time
import uuid
from typing import Any, Optional

from app.assistant.context import ConversationContext
from app.assistant.exceptions import (
    AssistantConfigurationError,
    AssistantLLMError,
    AssistantResearchError,
    AssistantRetrievalError,
)
from app.assistant.models import (
    AssistantContext,
    AssistantMode,
    AssistantRequest,
    AssistantResponse,
    AssistantSource,
    LLMResponse,
)
from app.assistant.prompts import AssistantPromptBuilder
from app.assistant.response import ResponseBuilder

from app.llm.factory import get_llm_provider
from app.research.models import ResearchQuery
from app.research.pipeline import ResearchPipeline


logger = logging.getLogger(__name__)


class AssistantOrchestrator:
    """
    Coordinates assistant execution.

    The orchestrator owns execution flow but does not own persistence.
    """

    def __init__(
        self,
        *,
        llm_provider: Optional[Any] = None,
        research_pipeline: Optional[ResearchPipeline] = None,
        retrieval_service: Optional[Any] = None,
        context_manager: Optional[ConversationContext] = None,
        prompt_builder: Optional[AssistantPromptBuilder] = None,
        response_builder: Optional[ResponseBuilder] = None,
    ) -> None:

        self.llm_provider = (
            llm_provider
            if llm_provider is not None
            else get_llm_provider()
        )

        self.research_pipeline = (
            research_pipeline
            if research_pipeline is not None
            else ResearchPipeline()
        )

        self.retrieval_service = retrieval_service

        self.context_manager = (
            context_manager
            if context_manager is not None
            else ConversationContext()
        )

        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else AssistantPromptBuilder()
        )

        self.response_builder = (
            response_builder
            if response_builder is not None
            else ResponseBuilder()
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def run(
        self,
        request: AssistantRequest,
    ) -> AssistantResponse:

        started = time.perf_counter()

        execution_id = str(
            uuid.uuid4()
        )

        context = self.context_manager.build(
            request
        )

        context.metadata[
            "execution_id"
        ] = execution_id

        mode = self._resolve_mode(
            request
        )

        context.mode = mode

        logger.info(
            "Starting assistant execution "
            "execution_id=%s mode=%s",
            execution_id,
            mode.value,
        )

        try:
            self.context_manager.append_user_message(
                context
            )

            # ---------------------------------------------------------------
            # RESEARCH
            # ---------------------------------------------------------------

            if mode == AssistantMode.RESEARCH:
                await self._run_research(
                    context
                )

            # ---------------------------------------------------------------
            # RETRIEVAL / RAG
            # ---------------------------------------------------------------

            elif mode in {
                AssistantMode.RAG,
                AssistantMode.RETRIEVAL,
            }:
                await self._run_retrieval(
                    context
                )

            # ---------------------------------------------------------------
            # GENERATION
            # ---------------------------------------------------------------

            llm_response = await self._generate(
                context
            )

            duration = (
                time.perf_counter()
                - started
            )

            context.final_answer = (
                llm_response.content
            )

            self.context_manager.append_assistant_message(
                context,
                llm_response.content,
            )

            return self.response_builder.from_llm(
                llm_response,
                conversation_id=request.conversation_id,
                mode=mode,
                sources=context.sources,
                execution_metadata={
                    "execution_id": execution_id,
                    "duration_seconds": duration,
                    "llm_used": True,
                    "retrieval_used": bool(
                        context.retrieved_context
                    ),
                    "research_used": (
                        context.research_result
                        is not None
                    ),
                },
            )

        except Exception as exc:
            logger.exception(
                "Assistant execution failed "
                "execution_id=%s",
                execution_id,
            )

            raise exc

    # ========================================================================
    # MODE
    # ========================================================================

    @staticmethod
    def _resolve_mode(
        request: AssistantRequest,
    ) -> AssistantMode:
        """
        Resolve AUTO into the appropriate execution mode.
        """

        if request.mode != AssistantMode.AUTO:
            return request.mode

        if request.is_research_request():
            return AssistantMode.RESEARCH

        if request.is_retrieval_request():
            return AssistantMode.RAG

        return AssistantMode.CHAT

    # ========================================================================
    # RESEARCH
    # ========================================================================

    async def _run_research(
        self,
        context: AssistantContext,
    ) -> None:

        try:
            research_query = ResearchQuery(
                query=context.query,
                depth="deep",
                include_papers=True,
                include_github=True,
                include_docs=True,
            )

            result = await self.research_pipeline.run(
                research_query
            )

            context.research_result = result

            self._extract_research_sources(
                context,
                result,
            )

        except Exception as exc:
            raise AssistantResearchError(
                f"Research execution failed: {exc}"
            ) from exc

    # ========================================================================
    # RETRIEVAL
    # ========================================================================

    async def _run_retrieval(
        self,
        context: AssistantContext,
    ) -> None:

        if self.retrieval_service is None:
            logger.warning(
                "RAG/retrieval mode requested but no "
                "retrieval service is configured. "
                "Falling back to direct LLM."
            )
            return

        try:
            result = await self._call_retrieval_service(
                self.retrieval_service,
                context.query,
            )

            items = self._normalize_collection(
                result
            )

            self.context_manager.add_retrieved_context(
                context,
                items,
            )

            self._extract_retrieval_sources(
                context,
                items,
            )

        except Exception as exc:
            raise AssistantRetrievalError(
                f"Retrieval execution failed: {exc}"
            ) from exc

    async def _call_retrieval_service(
        self,
        service: Any,
        query: str,
    ) -> Any:

        if hasattr(service, "search"):
            method = service.search

        elif hasattr(service, "retrieve"):
            method = service.retrieve

        elif hasattr(service, "run"):
            method = service.run

        elif callable(service):
            method = service

        else:
            raise AssistantConfigurationError(
                "Retrieval service must expose "
                "`search()`, `retrieve()`, `run()`, "
                "or be callable."
            )

        try:
            signature = inspect.signature(
                method
            )

            parameters = signature.parameters

            if "query" in parameters:
                result = method(
                    query=query
                )
            else:
                result = method(
                    query
                )

        except (ValueError, TypeError):
            result = method(
                query
            )

        return await self._resolve_awaitable(
            result
        )

    # ========================================================================
    # LLM
    # ========================================================================

    async def _generate(
        self,
        context: AssistantContext,
    ) -> LLMResponse:

        if self.llm_provider is None:
            raise AssistantConfigurationError(
                "LLM provider is not configured."
            )

        system_prompt = (
            self.prompt_builder.build_system_prompt(
                mode=context.mode
            )
        )

        context.system_prompt = system_prompt

        messages = (
            self.prompt_builder.build_messages(
                context,
                system_prompt=system_prompt,
            )
        )

        user_prompt = (
            self.prompt_builder.build_user_prompt(
                context
            )
        )

        # --------------------------------------------------------------------
        # Ensure enriched user prompt is present.
        # --------------------------------------------------------------------

        filtered_messages = []

        for message in messages:
            role = getattr(
                message,
                "role",
                None,
            )

            content = getattr(
                message,
                "content",
                None,
            )

            if (
                role == "user"
                and content == context.query
            ):
                continue

            filtered_messages.append(
                message
            )

        # Use ChatMessage if available.
        from app.assistant.models import ChatMessage

        filtered_messages.append(
            ChatMessage(
                role="user",
                content=user_prompt,
            )
        )

        messages = filtered_messages

        context.assembled_context = user_prompt

        try:
            raw_response = await self._call_llm(
                messages
            )

            return self._normalize_llm_response(
                raw_response
            )

        except Exception as exc:
            raise AssistantLLMError(
                f"LLM generation failed: {exc}"
            ) from exc

    async def _call_llm(
        self,
        messages: list[Any],
    ) -> Any:

        provider = self.llm_provider

        if hasattr(provider, "chat"):
            method = provider.chat

        elif hasattr(provider, "generate"):
            method = provider.generate

        elif hasattr(provider, "complete"):
            method = provider.complete

        elif callable(provider):
            method = provider

        else:
            raise AssistantConfigurationError(
                "Configured LLM provider does not expose "
                "`chat()`, `generate()`, `complete()`, "
                "or callable interface."
            )

        try:
            signature = inspect.signature(
                method
            )

            parameters = signature.parameters

            if "messages" in parameters:
                result = method(
                    messages=messages
                )

            elif "prompt" in parameters:
                result = method(
                    prompt=self._messages_to_prompt(
                        messages
                    )
                )

            elif "input" in parameters:
                result = method(
                    input=self._messages_to_prompt(
                        messages
                    )
                )

            else:
                result = method(
                    messages
                )

        except (ValueError, TypeError):
            result = method(
                messages
            )

        return await self._resolve_awaitable(
            result
        )

    # ========================================================================
    # RESPONSE NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_llm_response(
        value: Any,
    ) -> LLMResponse:

        if isinstance(
            value,
            LLMResponse,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            return LLMResponse(
                content=value
            )

        if isinstance(
            value,
            dict,
        ):
            data = dict(value)

        elif hasattr(
            value,
            "model_dump",
        ):
            try:
                data = value.model_dump()
            except Exception:
                data = {}

        elif hasattr(
            value,
            "__dict__",
        ):
            try:
                data = dict(
                    value.__dict__
                )
            except Exception:
                data = {}

        else:
            data = {
                "content": str(value)
            }

        # --------------------------------------------------------------------
        # Direct content
        # --------------------------------------------------------------------

        content = (
            data.get("content")
            or data.get("text")
            or data.get("output")
            or data.get("response")
        )

        # --------------------------------------------------------------------
        # OpenAI/OpenRouter style response
        # --------------------------------------------------------------------

        if content is None:
            choices = data.get(
                "choices"
            )

            if isinstance(
                choices,
                list,
            ) and choices:

                first = choices[0]

                if isinstance(
                    first,
                    dict,
                ):

                    message = first.get(
                        "message"
                    )

                    if isinstance(
                        message,
                        dict,
                    ):
                        content = message.get(
                            "content"
                        )

                    content = (
                        content
                        or first.get("text")
                    )

        if content is None:
            raise AssistantLLMError(
                "LLM response did not contain "
                "usable content."
            )

        finish_reason = None

        choices = data.get(
            "choices"
        )

        if isinstance(
            choices,
            list,
        ) and choices:

            first = choices[0]

            if isinstance(
                first,
                dict,
            ):
                finish_reason = first.get(
                    "finish_reason"
                )

        return LLMResponse(
            content=str(content),
            model=(
                str(data["model"])
                if data.get("model")
                else None
            ),
            provider=(
                str(data["provider"])
                if data.get("provider")
                else None
            ),
            usage=(
                data.get("usage")
                if isinstance(
                    data.get("usage"),
                    dict,
                )
                else {}
            ),
            finish_reason=finish_reason,
            metadata={
                key: value
                for key, value in data.items()
                if key not in {
                    "content",
                    "text",
                    "output",
                    "response",
                    "model",
                    "provider",
                    "usage",
                    "choices",
                }
            },
        )

    # ========================================================================
    # SOURCES
    # ========================================================================

    def _extract_research_sources(
        self,
        context: AssistantContext,
        result: Any,
    ) -> None:

        if result is None:
            return

        sources = getattr(
            result,
            "sources",
            None,
        )

        if sources is None and isinstance(
            result,
            dict,
        ):
            sources = result.get(
                "sources"
            )

        if not sources:
            return

        for source in sources:

            source_data = self._to_dict(
                source
            )

            source_id = (
                source_data.get("id")
                or source_data.get("source_id")
                or source_data.get("url")
                or str(uuid.uuid4())
            )

            authors = (
                source_data.get(
                    "authors",
                    [],
                )
                or []
            )

            if isinstance(
                authors,
                str,
            ):
                authors = [
                    authors
                ]

            metadata = source_data.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            source_model = AssistantSource(
                id=str(source_id),
                title=str(
                    source_data.get(
                        "title",
                        "Research source",
                    )
                ),
                source_type=str(
                    source_data.get(
                        "source_type",
                        "research",
                    )
                ),
                url=source_data.get(
                    "url"
                ),
                authors=[
                    str(author)
                    for author in authors
                ],
                metadata=metadata,
            )

            self.context_manager.add_source(
                context,
                source_model,
            )

    def _extract_retrieval_sources(
        self,
        context: AssistantContext,
        items: list[Any],
    ) -> None:

        for index, item in enumerate(
            items
        ):

            data = self._to_dict(
                item
            )

            source = data.get(
                "source"
            )

            if source is not None:
                source_data = self._to_dict(
                    source
                )

                merged = dict(data)
                merged.update(source_data)
                data = merged

            source_id = (
                data.get("id")
                or data.get("source_id")
                or data.get("url")
                or f"retrieved-{index + 1}"
            )

            metadata = data.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            source_model = AssistantSource(
                id=str(source_id),
                title=str(
                    data.get(
                        "title",
                        f"Retrieved source {index + 1}",
                    )
                ),
                source_type=str(
                    data.get(
                        "source_type",
                        "retrieval",
                    )
                ),
                url=data.get(
                    "url"
                ),
                document_id=data.get(
                    "document_id"
                ),
                chunk_id=data.get(
                    "chunk_id"
                ),
                score=self._safe_float(
                    data.get("score")
                ),
                metadata=metadata,
            )

            self.context_manager.add_source(
                context,
                source_model,
            )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _normalize_collection(
        value: Any,
    ) -> list[Any]:

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            tuple,
        ):
            return list(value)

        if isinstance(
            value,
            set,
        ):
            return list(value)

        if isinstance(
            value,
            dict,
        ):

            for key in (
                "results",
                "items",
                "documents",
                "sources",
                "data",
            ):

                nested = value.get(
                    key
                )

                if isinstance(
                    nested,
                    (list, tuple, set),
                ):
                    return list(
                        nested
                    )

        return [value]

    @staticmethod
    def _to_dict(
        value: Any,
    ) -> dict[str, Any]:

        if isinstance(
            value,
            dict,
        ):
            return dict(value)

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                return value.model_dump()
            except Exception:
                pass

        if hasattr(
            value,
            "__dict__",
        ):
            try:
                return dict(
                    value.__dict__
                )
            except Exception:
                pass

        return {
            "title": str(value)
        }

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _messages_to_prompt(
        messages: list[Any],
    ) -> str:

        parts = []

        for message in messages:

            role = getattr(
                message,
                "role",
                "user",
            )

            content = getattr(
                message,
                "content",
                str(message),
            )

            parts.append(
                f"{str(role).upper()}:\n{content}"
            )

        return "\n\n".join(
            parts
        )

    @staticmethod
    async def _resolve_awaitable(
        value: Any,
    ) -> Any:

        if inspect.isawaitable(
            value
        ):
            return await value

        return value


def get_assistant_orchestrator(
    **kwargs: Any,
) -> AssistantOrchestrator:
    """
    Factory for application-level assistant orchestration.
    """

    return AssistantOrchestrator(
        **kwargs
    )


__all__ = [
    "AssistantOrchestrator",
    "get_assistant_orchestrator",
]