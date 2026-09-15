
from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from app.adaptive_rag.adapters.retrieval import RetrievalAdapter
from app.adaptive_rag.controller import AdaptiveRAGController
from app.retrieval.models import RetrievalQuery
from app.retrieval.service import RetrievalService
from app.schemas.adaptive_rag import (
    AdaptiveRAGRequest,
    RetrievedChunk,
)
from app.schemas.retrieval import (
    Provenance,
    RetrievalResponse as PublicRetrievalResponse,
    RetrievalResult as PublicRetrievalResult,
)

from .models import ExploreContext, ExploreResult
from .schemas import ExploreRequest, ExploreResponse


logger = logging.getLogger(__name__)


class ExploreService:
    """
    Application-level orchestration service for research exploration.

    Architecture
    ------------

        ExploreService
              |
              +--------------------------+
              |                          |
              v                          v
        RetrievalService         AdaptiveRAGController
              |                          |
              |                          v
              |                  RetrievalAdapter
              |                          |
              |                          v
              +----------------> RetrievalService
                                         |
                                         v
                                  RetrievalPipeline
                                         |
                                         v
                                    IndexRegistry
                                   /             \
                                  v               v
                           VectorIndexer    KeywordIndexer

    ExploreService does not implement retrieval algorithms itself.
    """

    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        adaptive_rag_controller: AdaptiveRAGController | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service

        self.adaptive_rag_controller = (
            adaptive_rag_controller
            or AdaptiveRAGController(
                retrieval_service=RetrievalAdapter(
                    retrieval_service
                )
            )
        )

    # ==================================================================
    # PUBLIC ENTRY POINT
    # ==================================================================

    async def explore(
        self,
        request: ExploreRequest,
    ) -> ExploreResult:
        started_at = time.perf_counter()

        try:
            context = self._build_context(request)

            logger.info(
                "Explore execution started: "
                "query=%r adaptive=%s mode=%s strategy=%s "
                "top_k=%s paper_id=%r document_id=%r filters=%s",
                context.query,
                context.adaptive,
                context.retrieval_mode,
                context.strategy,
                context.top_k,
                context.paper_id,
                context.document_id,
                context.filters,
            )

            if context.adaptive:
                result = await self._run_adaptive(context)
            else:
                result = await self._run_retrieval(context)

            result.duration_ms = (
                time.perf_counter() - started_at
            ) * 1000.0

            logger.info(
                "Explore execution completed: "
                "query=%r duration_ms=%.2f "
                "adaptive=%s has_answer=%s source_count=%s",
                context.query,
                result.duration_ms,
                context.adaptive,
                bool(
                    result.adaptive_rag
                    and result.adaptive_rag.answer
                ),
                self._result_source_count(result),
            )

            return result

        except Exception:
            logger.exception(
                "Explore execution failed: query=%r",
                getattr(request, "query", None),
            )
            raise

    # ==================================================================
    # ADAPTIVE RAG
    # ==================================================================

    async def _run_adaptive(
        self,
        context: ExploreContext,
    ) -> ExploreResult:
        metadata = self._build_adaptive_metadata(context)

        adaptive_request = AdaptiveRAGRequest(
            query=context.query,
            adaptive=True,
            strategy=context.strategy,
            max_iterations=context.max_iterations,
            confidence_threshold=context.confidence_threshold,
            top_k=context.top_k,
            retrieval_mode=context.retrieval_mode,
            enable_graph=context.enable_graph,
            enable_multi_query=context.enable_multi_query,
            enable_correction=context.enable_correction,
            metadata=metadata,
        )

        logger.debug(
            "Running Adaptive RAG: "
            "query=%r strategy=%r retrieval_mode=%r "
            "top_k=%s max_iterations=%s confidence_threshold=%s "
            "metadata=%s",
            context.query,
            context.strategy,
            context.retrieval_mode,
            context.top_k,
            context.max_iterations,
            context.confidence_threshold,
            metadata,
        )

        adaptive_response = await self.adaptive_rag_controller.run(
            adaptive_request
        )

        source_count = len(
            getattr(adaptive_response, "sources", None) or []
        )

        logger.info(
            "Adaptive RAG completed: "
            "query=%r status=%s error=%r "
            "answer_present=%s source_count=%s iterations=%s",
            context.query,
            getattr(adaptive_response, "status", None),
            getattr(adaptive_response, "error", None),
            bool(getattr(adaptive_response, "answer", None)),
            source_count,
            getattr(adaptive_response, "iterations", 0),
        )

        # --------------------------------------------------------------
        # CONTROLLED FALLBACK
        # --------------------------------------------------------------

        if (
            getattr(adaptive_response, "error", None) is None
            and source_count == 0
        ):
            logger.warning(
                "Adaptive RAG returned zero sources for query=%r. "
                "Running one direct retrieval fallback.",
                context.query,
            )

            fallback_result = await self._run_retrieval(
                context,
                execution_mode="adaptive_rag_fallback",
            )

            fallback_sources = (
                fallback_result.retrieval.results
                if fallback_result.retrieval is not None
                else []
            )

            fallback_count = len(fallback_sources)

            logger.info(
                "Adaptive RAG fallback completed: "
                "query=%r fallback_source_count=%s",
                context.query,
                fallback_count,
            )

            if fallback_count > 0:
                logger.warning(
                    "Evidence was found by direct retrieval but was not "
                    "surfaced by Adaptive RAG: query=%r count=%s",
                    context.query,
                    fallback_count,
                )

                converted_sources: list[RetrievedChunk] = []

                for item in fallback_sources:
                    converted = (
                        self._retrieval_result_to_adaptive_chunk(
                            item
                        )
                    )

                    if converted is not None:
                        converted_sources.append(converted)

                if converted_sources:
                    adaptive_response = adaptive_response.model_copy(
                        update={
                            "sources": converted_sources,
                        }
                    )

                    logger.info(
                        "Injected fallback sources into Adaptive RAG "
                        "response: query=%r count=%s",
                        context.query,
                        len(converted_sources),
                    )

        return ExploreResult(
            query=context.query,
            adaptive_rag=adaptive_response,
            metadata={
                "execution_mode": "adaptive_rag",
                "retrieval_mode": context.retrieval_mode,
                "strategy": context.strategy,
                "top_k": context.top_k,
                "paper_id": context.paper_id,
                "document_id": context.document_id,
                "filters": context.filters,
                **context.metadata,
            },
        )

    # ==================================================================
    # DIRECT RETRIEVAL
    # ==================================================================

    async def _run_retrieval(
        self,
        context: ExploreContext,
        *,
        execution_mode: str = "retrieval",
    ) -> ExploreResult:
        retrieval_query = self._build_retrieval_query(context)

        logger.debug(
            "Running direct retrieval: "
            "query=%r mode=%r top_k=%s filters=%s metadata=%s",
            context.query,
            context.retrieval_mode,
            context.top_k,
            context.filters,
            retrieval_query.metadata,
        )

        retrieval_response = await self.retrieval_service.search(
            retrieval_query
        )

        result_count = len(
            getattr(retrieval_response, "results", None) or []
        )

        logger.info(
            "Direct retrieval completed: "
            "query=%r mode=%r result_count=%s",
            context.query,
            context.retrieval_mode,
            result_count,
        )

        if result_count == 0:
            logger.warning(
                "Retrieval returned zero results: "
                "query=%r mode=%r top_k=%s filters=%s",
                context.query,
                context.retrieval_mode,
                context.top_k,
                context.filters,
            )

        return ExploreResult(
            query=context.query,
            retrieval=retrieval_response,
            metadata={
                "execution_mode": execution_mode,
                "retrieval_mode": context.retrieval_mode,
                "top_k": context.top_k,
                "paper_id": context.paper_id,
                "document_id": context.document_id,
                "filters": context.filters,
                **context.metadata,
            },
        )

    # ==================================================================
    # CONTEXT CONSTRUCTION
    # ==================================================================

    @staticmethod
    def _build_context(
        request: ExploreRequest,
    ) -> ExploreContext:
        query = request.query.strip()

        if not query:
            raise ValueError(
                "Explore query must not be empty."
            )

        filters = dict(request.filters or {})
        metadata = dict(request.metadata or {})

        if request.paper_id is not None:
            filters.setdefault(
                "paper_id",
                request.paper_id,
            )

        if request.document_id is not None:
            filters.setdefault(
                "document_id",
                request.document_id,
            )

        strategy = (
            request.strategy.value
            if request.strategy is not None
            else None
        )

        retrieval_mode = (
            request.retrieval_mode.value
            if hasattr(request.retrieval_mode, "value")
            else str(request.retrieval_mode)
        )

        return ExploreContext(
            query=query,
            top_k=request.top_k,
            retrieval_mode=retrieval_mode,
            adaptive=request.adaptive,
            strategy=strategy,
            max_iterations=request.max_iterations,
            confidence_threshold=request.confidence_threshold,
            paper_id=request.paper_id,
            document_id=request.document_id,
            filters=filters,
            enable_graph=request.enable_graph,
            enable_multi_query=request.enable_multi_query,
            enable_correction=request.enable_correction,
            metadata=metadata,
        )

    # ==================================================================
    # ADAPTIVE METADATA
    # ==================================================================

    @staticmethod
    def _build_adaptive_metadata(
        context: ExploreContext,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = dict(
            context.metadata
        )

        metadata["filters"] = dict(
            context.filters
        )

        if context.paper_id is not None:
            metadata["paper_id"] = context.paper_id

        if context.document_id is not None:
            metadata["document_id"] = context.document_id

        metadata["retrieval_mode"] = context.retrieval_mode

        metadata["explore"] = {
            "query": context.query,
            "retrieval_mode": context.retrieval_mode,
            "strategy": context.strategy,
            "top_k": context.top_k,
            "paper_id": context.paper_id,
            "document_id": context.document_id,
            "filters": dict(context.filters),
        }

        return metadata

    # ==================================================================
    # RETRIEVAL QUERY CONSTRUCTION
    # ==================================================================

    @staticmethod
    def _build_retrieval_query(
        context: ExploreContext,
    ) -> RetrievalQuery:
        metadata: dict[str, Any] = dict(
            context.metadata
        )

        if context.paper_id is not None:
            metadata["paper_id"] = context.paper_id

        if context.document_id is not None:
            metadata["document_id"] = context.document_id

        metadata["explore"] = True

        return RetrievalQuery(
            query=context.query,
            top_k=context.top_k,
            mode=context.retrieval_mode,
            filters=dict(context.filters),
            metadata=metadata,
        )

    # ==================================================================
    # PUBLIC RESPONSE CONVERSION
    # ==================================================================

    @staticmethod
    def to_response(
        result: ExploreResult,
    ) -> ExploreResponse:
        if result.adaptive_rag is not None:
            adaptive = result.adaptive_rag

            confidence = None

            if adaptive.confidence is not None:
                confidence = adaptive.confidence.score

            sources = list(
                getattr(adaptive, "sources", None) or []
            )

            retrieval = (
                ExploreService._adaptive_sources_to_retrieval(
                    query=result.query,
                    sources=sources,
                    top_k=result.metadata.get(
                        "top_k",
                        len(sources) or 10,
                    ),
                    retrieval_mode=result.metadata.get(
                        "retrieval_mode",
                        "hybrid",
                    ),
                )
            )

            logger.debug(
                "Converting Adaptive RAG result to ExploreResponse: "
                "query=%r answer_present=%s source_count=%s "
                "confidence=%r error=%r retrieval_results=%s",
                result.query,
                bool(adaptive.answer),
                len(sources),
                confidence,
                adaptive.error,
                len(retrieval.results),
            )

            return ExploreResponse(
                query=result.query,
                retrieval=retrieval,
                adaptive_rag=adaptive,
                answer=adaptive.answer,
                sources=sources,
                confidence=confidence,
                metadata=result.metadata,
                duration_ms=result.duration_ms,
                success=adaptive.error is None,
            )

        internal_retrieval = result.retrieval

        public_retrieval = (
            ExploreService._retrieval_response_to_public(
                query=result.query,
                retrieval=internal_retrieval,
                top_k=result.metadata.get(
                    "top_k",
                    10,
                ),
                retrieval_mode=result.metadata.get(
                    "retrieval_mode",
                    "hybrid",
                ),
            )
            if internal_retrieval is not None
            else None
        )

        sources = (
            list(public_retrieval.results)
            if public_retrieval is not None
            else []
        )

        return ExploreResponse(
            query=result.query,
            retrieval=public_retrieval,
            adaptive_rag=None,
            answer=None,
            sources=sources,
            confidence=None,
            metadata=result.metadata,
            duration_ms=result.duration_ms,
            success=True,
        )

    # ==================================================================
    # INTERNAL RETRIEVAL RESPONSE -> PUBLIC RESPONSE
    # ==================================================================

    @staticmethod
    def _retrieval_response_to_public(
        *,
        query: str,
        retrieval: Any,
        top_k: int,
        retrieval_mode: str,
    ) -> PublicRetrievalResponse:
        internal_results = list(
            getattr(retrieval, "results", None) or []
        )

        public_results: list[PublicRetrievalResult] = []

        for index, source in enumerate(
            internal_results,
            start=1,
        ):
            converted = (
                ExploreService._retrieval_result_to_public(
                    source,
                    fallback_rank=index,
                    retrieval_mode=retrieval_mode,
                )
            )

            if converted is not None:
                public_results.append(converted)

        metadata = dict(
            getattr(retrieval, "metadata", None) or {}
        )

        metadata.setdefault(
            "source",
            "retrieval_service",
        )

        metadata["converted"] = True

        return PublicRetrievalResponse(
            query=query,
            results=public_results,
            total=len(public_results),
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            evidence=[
                item.evidence
                for item in public_results
                if item.evidence is not None
            ],
            metadata=metadata,
        )

    # ==================================================================
    # INTERNAL RETRIEVAL RESULT -> PUBLIC RESULT
    # ==================================================================

    @staticmethod
    def _retrieval_result_to_public(
        source: Any,
        *,
        fallback_rank: int,
        retrieval_mode: str,
    ) -> PublicRetrievalResult | None:
        document = getattr(
            source,
            "document",
            None,
        )

        if document is None:
            logger.warning(
                "Skipping retrieval result without document: %r",
                source,
            )
            return None

        chunk_id = ExploreService._to_uuid(
            getattr(document, "chunk_id", None)
            or getattr(document, "id", None)
            or getattr(source, "chunk_id", None)
            or getattr(source, "id", None)
        )

        if chunk_id is None:
            logger.warning(
                "Skipping retrieval result with invalid chunk id: "
                "document=%r result=%r",
                document,
                source,
            )
            return None

        document_id = ExploreService._to_uuid(
            getattr(document, "document_id", None)
            or getattr(source, "document_id", None)
        )

        if document_id is None:
            logger.warning(
                "Skipping retrieval result with invalid document id: "
                "chunk_id=%r document=%r",
                chunk_id,
                document,
            )
            return None

        # paper_id is an integer in the research schema.
        paper_id = ExploreService._to_int(
            getattr(document, "paper_id", None)
            or getattr(source, "paper_id", None)
        )

        section_id = ExploreService._to_uuid(
            getattr(document, "section_id", None)
            or getattr(source, "section_id", None)
        )

        content = getattr(
            document,
            "text",
            None,
        )

        if content is None:
            content = getattr(
                document,
                "content",
                None,
            )

        if content is None:
            content = ""

        content = str(content)

        if not content.strip():
            logger.warning(
                "Skipping retrieval result with empty content: "
                "chunk_id=%r",
                chunk_id,
            )
            return None

        score = ExploreService._safe_float(
            getattr(source, "score", None)
        )

        if score is None:
            score = ExploreService._safe_float(
                getattr(document, "score", None)
            )

        if score is None:
            score = 0.0

        rank = ExploreService._safe_int(
            getattr(source, "rank", None)
        )

        if rank is None or rank < 1:
            rank = fallback_rank

        vector_score = ExploreService._safe_float(
            getattr(source, "vector_score", None)
        )

        keyword_score = ExploreService._safe_float(
            getattr(source, "keyword_score", None)
        )

        rerank_score = ExploreService._safe_float(
            getattr(source, "rerank_score", None)
        )

        source_method = getattr(
            source,
            "retrieval_method",
            None,
        )

        if source_method is not None:
            if hasattr(source_method, "value"):
                retrieval_method = str(
                    source_method.value
                )
            else:
                retrieval_method = str(
                    source_method
                )
        else:
            retrieval_method = retrieval_mode

        metadata: dict[str, Any] = {}

        document_metadata = getattr(
            document,
            "metadata",
            None,
        )

        if isinstance(document_metadata, dict):
            metadata.update(document_metadata)

        source_metadata = getattr(
            source,
            "metadata",
            None,
        )

        if isinstance(source_metadata, dict):
            metadata.update(source_metadata)

        metadata.setdefault(
            "retrieval_source",
            "retrieval_service",
        )

        metadata.setdefault(
            "chunk_id",
            str(chunk_id),
        )

        metadata.setdefault(
            "document_id",
            str(document_id),
        )

        if paper_id is not None:
            metadata.setdefault(
                "paper_id",
                paper_id,
            )

        if section_id is not None:
            metadata.setdefault(
                "section_id",
                str(section_id),
            )

        page = ExploreService._safe_int(
            metadata.get("page")
            or metadata.get("page_number")
        )

        section = (
            metadata.get("section")
            or metadata.get("section_name")
        )

        provenance = Provenance(
            document_id=document_id,
            chunk_id=chunk_id,
            page=page,
            section=(
                str(section)
                if section is not None
                else None
            ),
            source=(
                str(metadata.get("source"))
                if metadata.get("source") is not None
                else None
            ),
        )

        return PublicRetrievalResult(
            chunk_id=chunk_id,
            document_id=document_id,
            paper_id=paper_id,
            section_id=section_id,
            content=content,
            score=score,
            rank=rank,
            retrieval_method=retrieval_method,
            rerank_score=rerank_score,
            vector_score=vector_score,
            keyword_score=keyword_score,
            provenance=provenance,
            evidence=None,
            metadata=metadata,
        )

    # ==================================================================
    # ADAPTIVE SOURCES -> CANONICAL RETRIEVAL RESPONSE
    # ==================================================================

    @staticmethod
    def _adaptive_sources_to_retrieval(
        *,
        query: str,
        sources: list[RetrievedChunk],
        top_k: int,
        retrieval_mode: str,
    ) -> PublicRetrievalResponse:
        results: list[PublicRetrievalResult] = []

        for index, source in enumerate(
            sources,
            start=1,
        ):
            result = (
                ExploreService._adaptive_chunk_to_retrieval_result(
                    source,
                    fallback_rank=index,
                    retrieval_mode=retrieval_mode,
                )
            )

            if result is not None:
                results.append(result)

        return PublicRetrievalResponse(
            query=query,
            results=results,
            total=len(results),
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            evidence=[
                item.evidence
                for item in results
                if item.evidence is not None
            ],
            metadata={
                "source": "adaptive_rag",
                "converted": True,
            },
        )

    # ==================================================================
    # ADAPTIVE CHUNK -> PUBLIC RESULT
    # ==================================================================

    @staticmethod
    def _adaptive_chunk_to_retrieval_result(
        source: RetrievedChunk,
        *,
        fallback_rank: int,
        retrieval_mode: str,
    ) -> PublicRetrievalResult | None:
        chunk_id = ExploreService._to_uuid(
            source.id
        )

        if chunk_id is None:
            logger.warning(
                "Skipping Adaptive RAG source with invalid chunk id: %r",
                source.id,
            )
            return None

        document_id = (
            ExploreService._to_uuid(
                source.document_id
            )
            if source.document_id is not None
            else None
        )

        if document_id is None:
            logger.warning(
                "Skipping Adaptive RAG source with invalid "
                "document_id: chunk_id=%r document_id=%r",
                source.id,
                source.document_id,
            )
            return None

        metadata = dict(
            source.metadata or {}
        )

        paper_id = ExploreService._to_int(
            metadata.get("paper_id")
        )

        section_id = ExploreService._to_uuid(
            metadata.get("section_id")
        )

        provenance = Provenance(
            document_id=document_id,
            chunk_id=chunk_id,
            page=ExploreService._safe_int(
                metadata.get("page")
                or metadata.get("page_number")
            ),
            section=(
                str(
                    metadata.get("section")
                    or metadata.get("section_name")
                )
                if (
                    metadata.get("section")
                    or metadata.get("section_name")
                )
                else None
            ),
            source=(
                str(metadata.get("source"))
                if metadata.get("source") is not None
                else None
            ),
        )

        score = ExploreService._safe_float(
            source.score
        )

        if score is None:
            score = 0.0

        rank = ExploreService._safe_int(
            source.rank
        )

        if rank is None or rank < 1:
            rank = fallback_rank

        return PublicRetrievalResult(
            chunk_id=chunk_id,
            document_id=document_id,
            paper_id=paper_id,
            section_id=section_id,
            content=str(
                source.content or ""
            ),
            score=score,
            rank=rank,
            retrieval_method=retrieval_mode,
            rerank_score=ExploreService._safe_float(
                metadata.get("rerank_score")
            ),
            vector_score=ExploreService._safe_float(
                metadata.get("vector_score")
            ),
            keyword_score=ExploreService._safe_float(
                metadata.get("keyword_score")
            ),
            provenance=provenance,
            evidence=None,
            metadata={
                **metadata,
                "document_name": source.document_name,
                "adaptive_rag": True,
            },
        )

    # ==================================================================
    # INTERNAL RESULT -> ADAPTIVE CHUNK
    # ==================================================================

    @staticmethod
    def _retrieval_result_to_adaptive_chunk(
        source: Any,
    ) -> RetrievedChunk | None:
        document = getattr(
            source,
            "document",
            None,
        )

        if document is None:
            logger.warning(
                "Cannot convert retrieval result to AdaptiveChunk: "
                "missing document. result=%r",
                source,
            )
            return None

        raw_chunk_id = (
            getattr(document, "chunk_id", None)
            or getattr(document, "id", None)
            or getattr(source, "chunk_id", None)
            or getattr(source, "id", None)
        )

        if raw_chunk_id is None:
            logger.warning(
                "Cannot convert retrieval result to AdaptiveChunk: "
                "missing chunk id. document=%r result=%r",
                document,
                source,
            )
            return None

        chunk_id = str(raw_chunk_id)

        raw_document_id = (
            getattr(document, "document_id", None)
            or getattr(source, "document_id", None)
        )

        document_id = (
            str(raw_document_id)
            if raw_document_id is not None
            else None
        )

        content = getattr(
            document,
            "text",
            None,
        )

        if content is None:
            content = getattr(
                document,
                "content",
                None,
            )

        if content is None:
            content = ""

        content = str(content)

        if not content.strip():
            logger.warning(
                "Cannot convert retrieval result to AdaptiveChunk: "
                "empty content. chunk_id=%r",
                chunk_id,
            )
            return None

        metadata: dict[str, Any] = {}

        document_metadata = getattr(
            document,
            "metadata",
            None,
        )

        if isinstance(document_metadata, dict):
            metadata.update(document_metadata)

        source_metadata = getattr(
            source,
            "metadata",
            None,
        )

        if isinstance(source_metadata, dict):
            metadata.update(source_metadata)

        metadata.setdefault(
            "chunk_id",
            chunk_id,
        )

        if document_id is not None:
            metadata.setdefault(
                "document_id",
                document_id,
            )

        paper_id = (
            getattr(document, "paper_id", None)
            or getattr(source, "paper_id", None)
            or metadata.get("paper_id")
        )

        if paper_id is not None:
            safe_paper_id = ExploreService._to_int(
                paper_id
            )

            if safe_paper_id is not None:
                metadata.setdefault(
                    "paper_id",
                    safe_paper_id,
                )

        section_id = (
            getattr(document, "section_id", None)
            or getattr(source, "section_id", None)
            or metadata.get("section_id")
        )

        if section_id is not None:
            metadata.setdefault(
                "section_id",
                str(section_id),
            )

        page_number = (
            getattr(document, "page_number", None)
            or metadata.get("page_number")
            or metadata.get("page")
        )

        if page_number is not None:
            safe_page = ExploreService._safe_int(
                page_number
            )

            if safe_page is not None:
                metadata.setdefault(
                    "page_number",
                    safe_page,
                )
                metadata.setdefault(
                    "page",
                    safe_page,
                )

        section_name = (
            metadata.get("section")
            or metadata.get("section_name")
        )

        if section_name is not None:
            metadata.setdefault(
                "section",
                str(section_name),
            )

        for field_name in (
            "vector_score",
            "keyword_score",
            "rerank_score",
        ):
            value = ExploreService._safe_float(
                getattr(source, field_name, None)
            )

            if value is not None:
                metadata.setdefault(
                    field_name,
                    value,
                )

        document_name = (
            getattr(document, "document_name", None)
            or getattr(document, "name", None)
            or metadata.get("document_name")
            or metadata.get("filename")
            or metadata.get("file_name")
        )

        if document_name is not None:
            document_name = str(
                document_name
            )

        score = ExploreService._safe_float(
            getattr(source, "score", None)
        )

        if score is None:
            score = 0.0

        rank = ExploreService._safe_int(
            getattr(source, "rank", None)
        )

        if rank is None or rank < 1:
            rank = 1

        return RetrievedChunk(
            id=chunk_id,
            document_id=document_id,
            document_name=document_name,
            content=content,
            score=score,
            rank=rank,
            metadata={
                **metadata,
                "retrieval_source": "direct_retrieval_fallback",
                "adaptive_rag": True,
            },
        )

    # ==================================================================
    # HELPERS
    # ==================================================================

    @staticmethod
    def _to_uuid(
        value: Any,
    ) -> UUID | None:
        if value is None:
            return None

        if isinstance(value, UUID):
            return value

        try:
            return UUID(str(value))
        except (
            ValueError,
            TypeError,
            AttributeError,
        ):
            return None

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None

    @staticmethod
    def _result_source_count(
        result: ExploreResult,
    ) -> int:
        if result.adaptive_rag is not None:
            return len(
                getattr(
                    result.adaptive_rag,
                    "sources",
                    None,
                )
                or []
            )

        if result.retrieval is not None:
            return len(
                getattr(
                    result.retrieval,
                    "results",
                    None,
                )
                or []
            )

        return 0


__all__ = [
    "ExploreService",
]

