"""
Adaptive RAG controller.

The controller is the orchestration boundary between the API layer
and the Adaptive RAG engine.

Flow

Request
    ↓
Controller
    ↓
Planner
    ↓
RAG strategy mapping
    ↓
Router
    ↓
Strategy
    ↓
RetrievalAdapter
    ↓
RetrievalService
    ↓
RetrievalPipeline
    ↓
IndexRegistry
    ↓
Evaluator
    ↓
API model conversion
    ↓
Response
"""

from __future__ import annotations

import inspect
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

from app.adaptive_rag.domain_models import RetrievalStrategy
from app.adaptive_rag.evaluator import AdaptiveRAGEvaluator
from app.adaptive_rag.generation import (
    RAGAnswerEvaluator,
    RAGAnswerGenerator,
)
from app.adaptive_rag.planner import AdaptiveRAGPlanner
from app.adaptive_rag.router import AdaptiveRAGRouter
from app.adaptive_rag.state import (
    AdaptiveRAGState as RuntimeAdaptiveRAGState,
    RetrievedChunk as RuntimeRetrievedChunk,
)
from app.adaptive_rag.strategies.corrective import CorrectiveRAGStrategy
from app.adaptive_rag.strategies.direct import DirectRAGStrategy
from app.adaptive_rag.strategies.graph_augmented import (
    GraphAugmentedRAGStrategy,
)
from app.adaptive_rag.strategies.iterative import IterativeRAGStrategy
from app.adaptive_rag.strategies.multi_query import MultiQueryRAGStrategy

from app.schemas.adaptive_rag import (
    AdaptiveRAGConfig,
    AdaptiveRAGExecution,
    AdaptiveRAGExecutionList,
    AdaptiveRAGHealth,
    AdaptiveRAGRequest,
    AdaptiveRAGResponse,
    AdaptiveRAGState,
    ConfidenceLevel,
    ConfidenceScore,
    EvaluationResult,
    ExecutionStatus,
    QueryPlan,
    RAGStrategy,
    RetrievedChunk,
    RetrievalMode,
    RetrievalStep,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


class AdaptiveRAGController:
    """
    Orchestrates the complete Adaptive RAG execution lifecycle.

    Retrieval dependencies are injected into the controller:

        IndexRegistry
            ↓
        RetrievalPipeline
            ↓
        RetrievalService
            ↓
        RetrievalAdapter
            ↓
        AdaptiveRAGController
    """

    VERSION = "1.3.0"

    def __init__(
        self,
        *,
        planner: AdaptiveRAGPlanner | None = None,
        router: AdaptiveRAGRouter | None = None,
        evaluator: AdaptiveRAGEvaluator | None = None,
        retrieval_service: Any | None = None,
        generator: RAGAnswerGenerator | None = None,
        strategy_evaluator: RAGAnswerEvaluator | None = None,
    ) -> None:
        self.planner = planner or AdaptiveRAGPlanner()
        self.router = router or AdaptiveRAGRouter()
        self.evaluator = evaluator or AdaptiveRAGEvaluator()

        self.retrieval_service = retrieval_service

        if self.retrieval_service is None:
            logger.warning(
                "AdaptiveRAGController created without a retrieval service. "
                "Retrieval strategies will fail unless they provide their "
                "own retrieval implementation."
            )

        self.generator = generator or RAGAnswerGenerator()

        self.strategy_evaluator = (
            strategy_evaluator or RAGAnswerEvaluator()
        )

        self._executions: dict[
            str,
            RuntimeAdaptiveRAGState,
        ] = {}

        self._strategies: dict[
            RAGStrategy,
            Any,
        ] = {
            RAGStrategy.DIRECT: DirectRAGStrategy(
                retrieval_service=self.retrieval_service,
                generator=self.generator,
                evaluator=self.strategy_evaluator,
            ),
            RAGStrategy.ITERATIVE: IterativeRAGStrategy(
                retrieval_service=self.retrieval_service,
                generator=self.generator,
                evaluator=self.strategy_evaluator,
            ),
            RAGStrategy.MULTI_QUERY: MultiQueryRAGStrategy(
                retrieval_service=self.retrieval_service,
                generator=self.generator,
                evaluator=self.strategy_evaluator,
            ),
            RAGStrategy.CORRECTIVE: CorrectiveRAGStrategy(
                retrieval_service=self.retrieval_service,
                generator=self.generator,
                evaluator=self.strategy_evaluator,
            ),
            RAGStrategy.GRAPH_AUGMENTED: GraphAugmentedRAGStrategy(
                retrieval_service=self.retrieval_service,
                generator=self.generator,
                evaluator=self.strategy_evaluator,
            ),
        }

    # ==================================================================
    # MAIN EXECUTION
    # ==================================================================

    async def run(
        self,
        request: AdaptiveRAGRequest,
    ) -> AdaptiveRAGResponse:
        started_at = datetime.now(timezone.utc)
        started_monotonic = time.perf_counter()

        execution_id = (
            str(request.execution_id)
            if getattr(request, "execution_id", None)
            else str(uuid.uuid4())
        )

        requested_strategy = self._select_strategy(request)

        state = RuntimeAdaptiveRAGState(
            query=request.query,
            status=ExecutionStatus.PLANNING,
            iteration=0,
            max_iterations=request.max_iterations,
            strategy=self._map_retrieval_strategy(
                requested_strategy
            ),
            metadata=dict(
                getattr(request, "metadata", None) or {}
            ),
        )

        state.metadata["execution_id"] = execution_id
        state.metadata["started_at"] = started_at.isoformat()

        self._executions[execution_id] = state

        try:
            # ==========================================================
            # 1. PLANNING
            # ==========================================================

            planner_result = self.planner.plan(request.query)

            if inspect.isawaitable(planner_result):
                planner_result = await planner_result

            analysis, plan = self._unpack_planner_result(
                planner_result
            )

            state.metadata["query_analysis"] = (
                self._serialize_for_metadata(analysis)
            )

            state.plan = plan

            self._store_plan_metadata(
                state,
                plan,
            )

            # Planner strategy is authoritative only if the request
            # did not explicitly provide one.
            if getattr(request, "strategy", None) is None:
                planner_strategy = self._get_field(
                    plan,
                    "strategy",
                )

                planned_strategy = (
                    self._map_domain_strategy_to_api(
                        planner_strategy
                    )
                )

                if planned_strategy is not None:
                    requested_strategy = planned_strategy

                    state.strategy = (
                        self._map_retrieval_strategy(
                            planned_strategy
                        )
                    )

            # ==========================================================
            # 2. ROUTING
            # ==========================================================

            routing_decision = await self._call_router(state)

            state.routing_decision = routing_decision

            selected_strategy = (
                self._select_strategy_from_routing(
                    routing_decision,
                    fallback=requested_strategy,
                )
            )

            state.strategy = self._map_retrieval_strategy(
                selected_strategy
            )

            # ==========================================================
            # 3. STRATEGY / RETRIEVAL EXECUTION
            # ==========================================================

            state.status = ExecutionStatus.RETRIEVING

            strategy_impl = self._strategies.get(
                selected_strategy
            )

            if strategy_impl is None:
                raise ValueError(
                    "No implementation registered for strategy "
                    f"{selected_strategy.value}"
                )

            result = await self._execute_strategy(
                strategy_impl,
                request=request,
                state=state,
            )

            self._apply_strategy_result(
                state,
                result,
            )

            self._ensure_retrieval_steps(
                state,
                request=request,
            )

            # ==========================================================
            # 4. EVALUATION
            # ==========================================================

            state.status = ExecutionStatus.EVALUATING

            evaluation = await self._evaluate_state(state)

            state.evaluation = evaluation
            state.confidence = self._extract_confidence(
                evaluation
            )

            # ==========================================================
            # 5. COMPLETION
            # ==========================================================

            state.status = ExecutionStatus.COMPLETED

            self._finish_state(
                state,
                started_monotonic,
            )

            return self._build_response(
                execution_id=execution_id,
                state=state,
                started_at=started_at,
            )

        except Exception as exc:
            logger.exception(
                "Adaptive RAG execution failed: %s",
                execution_id,
            )

            state.status = ExecutionStatus.FAILED
            state.error = str(exc)

            self._finish_state(
                state,
                started_monotonic,
            )

            return self._build_response(
                execution_id=execution_id,
                state=state,
                started_at=started_at,
            )

    # ==================================================================
    # PLANNER NORMALIZATION
    # ==================================================================

    @staticmethod
    def _unpack_planner_result(
        result: Any,
    ) -> tuple[Any, Any]:
        """
        Supports planner implementations returning:

            (analysis, plan)

        as well as a plan directly.
        """

        if isinstance(result, tuple):
            if len(result) >= 2:
                return result[0], result[1]

            if len(result) == 1:
                return None, result[0]

        if isinstance(result, list):
            if len(result) >= 2:
                return result[0], result[1]

            if len(result) == 1:
                return None, result[0]

        return None, result

    # ==================================================================
    # LIFECYCLE
    # ==================================================================

    @staticmethod
    def _finish_state(
        state: RuntimeAdaptiveRAGState,
        started_monotonic: float,
    ) -> None:
        completed_at = datetime.now(timezone.utc)

        state.metadata["completed_at"] = (
            completed_at.isoformat()
        )

        state.metadata["duration_ms"] = int(
            (
                time.perf_counter()
                - started_monotonic
            )
            * 1000
        )

    # ==================================================================
    # PLANNER / ROUTER
    # ==================================================================

    async def _call_router(
        self,
        state: RuntimeAdaptiveRAGState,
    ) -> Any:
        route = getattr(
            self.router,
            "route",
            None,
        )

        if route is None or not callable(route):
            raise TypeError(
                "AdaptiveRAGRouter does not expose a callable route()"
            )

        result = route(state)

        if inspect.isawaitable(result):
            result = await result

        return result

    def _store_plan_metadata(
        self,
        state: RuntimeAdaptiveRAGState,
        plan: Any,
    ) -> None:
        """
        Persist planner settings in runtime metadata.
        """

        if plan is None:
            return

        data = self._object_to_dict(plan)

        retrieval_data: dict[str, Any] = {}

        for key in (
            "retrieval",
            "retrieval_plan",
            "retrieval_config",
            "retrieval_settings",
        ):
            nested = data.get(key)

            if nested is not None:
                nested_dict = self._object_to_dict(
                    nested
                )

                if nested_dict:
                    retrieval_data.update(
                        nested_dict
                    )

        merged = dict(data)
        merged.update(retrieval_data)

        fields = (
            "strategy",
            "mode",
            "retrieval_mode",
            "top_k",
            "max_queries",
            "vector_weight",
            "keyword_weight",
            "filters",
            "query_variants",
            "retrieval_required",
            "graph_required",
        )

        for field_name in fields:
            if field_name not in merged:
                continue

            state.metadata[
                f"planner_{field_name}"
            ] = self._serialize_for_metadata(
                merged[field_name]
            )

        if merged.get("strategy") is not None:
            state.metadata["planner_strategy"] = (
                self._serialize_for_metadata(
                    merged["strategy"]
                )
            )

    # ==================================================================
    # STRATEGY EXECUTION
    # ==================================================================

    async def _execute_strategy(
        self,
        strategy: Any,
        *,
        request: AdaptiveRAGRequest,
        state: RuntimeAdaptiveRAGState,
    ) -> Any:
        execute = getattr(
            strategy,
            "execute",
            None,
        )

        if execute is None or not callable(execute):
            raise TypeError(
                "Invalid Adaptive RAG strategy: "
                f"{type(strategy).__name__}"
            )

        retrieval_mode = self._resolve_retrieval_mode(
            request=request,
            state=state,
        )

        request_metadata = dict(
            getattr(request, "metadata", None) or {}
        )

        # --------------------------------------------------------------
        # Filters
        # --------------------------------------------------------------

        filters: dict[str, Any] = {}

        planner_filters = state.metadata.get(
            "planner_filters"
        )

        if isinstance(
            planner_filters,
            Mapping,
        ):
            filters.update(
                dict(planner_filters)
            )

        request_filters = getattr(
            request,
            "filters",
            None,
        )

        if isinstance(
            request_filters,
            Mapping,
        ):
            filters.update(
                dict(request_filters)
            )

        metadata_filters = request_metadata.get(
            "filters"
        )

        if isinstance(
            metadata_filters,
            Mapping,
        ):
            filters.update(
                dict(metadata_filters)
            )

        # --------------------------------------------------------------
        # Resource identifiers
        # --------------------------------------------------------------

        paper_id = request_metadata.get(
            "paper_id"
        )

        document_id = request_metadata.get(
            "document_id"
        )

        if paper_id is None:
            paper_id = filters.get(
                "paper_id"
            )

        if document_id is None:
            document_id = filters.get(
                "document_id"
            )

        if paper_id is not None:
            try:
                paper_id = int(
                    paper_id
                )
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                logger.warning(
                    "Invalid paper_id=%r; leaving it unchanged",
                    paper_id,
                )

        if document_id is not None:
            document_id = str(
                document_id
            )

        # --------------------------------------------------------------
        # Context
        # --------------------------------------------------------------

        context = {
            "execution_id": state.metadata.get(
                "execution_id"
            ),
            "strategy": self._api_strategy(
                state.strategy
            ),
            "retrieval_mode": retrieval_mode,
            "metadata": request_metadata,
            "max_iterations": request.max_iterations,
            "confidence_threshold": (
                request.confidence_threshold
            ),
            "enable_graph": request.enable_graph,
            "enable_multi_query": (
                request.enable_multi_query
            ),
            "enable_correction": (
                request.enable_correction
            ),
            "filters": filters,
            "paper_id": paper_id,
            "document_id": document_id,
        }

        # --------------------------------------------------------------
        # Retrieval contract
        # --------------------------------------------------------------

        retrieval_kwargs: dict[str, Any] = {
            "mode": retrieval_mode,
        }

        if paper_id is not None:
            retrieval_kwargs["paper_id"] = paper_id

        if document_id is not None:
            retrieval_kwargs["document_id"] = document_id

        # --------------------------------------------------------------
        # Retrieval weights
        # --------------------------------------------------------------

        for field_name in (
            "vector_weight",
            "keyword_weight",
        ):
            value = request_metadata.get(
                field_name
            )

            if value is None:
                value = state.metadata.get(
                    f"planner_{field_name}"
                )

            if value is None:
                continue

            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                logger.warning(
                    "Ignoring invalid %s=%r",
                    field_name,
                    value,
                )
                continue

            if 0.0 <= value <= 1.0:
                retrieval_kwargs[field_name] = value
            else:
                logger.warning(
                    "Ignoring out-of-range %s=%r",
                    field_name,
                    value,
                )

        vector_weight = retrieval_kwargs.get(
            "vector_weight"
        )

        keyword_weight = retrieval_kwargs.get(
            "keyword_weight"
        )

        if (
            vector_weight is not None
            and keyword_weight is not None
            and vector_weight <= 0.0
            and keyword_weight <= 0.0
        ):
            logger.warning(
                "Both retrieval weights were zero. "
                "Falling back to default hybrid weighting."
            )

            retrieval_kwargs.pop(
                "vector_weight",
                None,
            )

            retrieval_kwargs.pop(
                "keyword_weight",
                None,
            )

        if filters:
            retrieval_kwargs["filters"] = filters

        # --------------------------------------------------------------
        # Top-K
        # --------------------------------------------------------------

        top_k = getattr(
            request,
            "top_k",
            None,
        )

        if top_k is None:
            top_k = state.metadata.get(
                "planner_top_k"
            )

        if top_k is None:
            top_k = 5

        try:
            top_k = int(
                top_k
            )
        except (
            TypeError,
            ValueError,
        ):
            top_k = 5

        top_k = max(
            1,
            min(
                100,
                top_k,
            ),
        )

        # --------------------------------------------------------------
        # Dispatch logging
        # --------------------------------------------------------------

        logger.info(
            "Adaptive RAG retrieval dispatch: "
            "query=%r strategy=%r mode=%r top_k=%s "
            "paper_id=%r document_id=%r filters=%s "
            "vector_weight=%r keyword_weight=%r",
            request.query,
            self._api_strategy(state.strategy),
            retrieval_mode,
            top_k,
            paper_id,
            document_id,
            filters,
            retrieval_kwargs.get(
                "vector_weight"
            ),
            retrieval_kwargs.get(
                "keyword_weight"
            ),
        )

        # --------------------------------------------------------------
        # Execute
        # --------------------------------------------------------------

        execute_kwargs = {
            "query": request.query,
            "context": context,
            "top_k": top_k,
            **retrieval_kwargs,
        }

        execute_kwargs = (
            self._filter_supported_kwargs(
                execute,
                execute_kwargs,
            )
        )

        logger.debug(
            "Calling %s.execute() with kwargs=%s",
            type(strategy).__name__,
            sorted(
                execute_kwargs.keys()
            ),
        )

        started = time.perf_counter()

        try:
            result = execute(
                **execute_kwargs
            )

            if inspect.isawaitable(result):
                result = await result

        except TypeError as exc:
            logger.exception(
                "Adaptive RAG strategy interface mismatch. "
                "Strategy=%s kwargs=%s",
                type(strategy).__name__,
                sorted(
                    execute_kwargs.keys()
                ),
            )

            raise TypeError(
                "Adaptive RAG strategy execution failed. "
                f"strategy={type(strategy).__name__}; "
                f"accepted_kwargs="
                f"{sorted(execute_kwargs.keys())}; "
                f"original_error={exc}"
            ) from exc

        duration_ms = int(
            (
                time.perf_counter()
                - started
            )
            * 1000
        )

        self._ensure_result_retrieval_steps(
            result,
            request=request,
            state=state,
            retrieval_mode=retrieval_mode,
            duration_ms=duration_ms,
        )

        return result

    @staticmethod
    def _filter_supported_kwargs(
        callable_obj: Any,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            signature = inspect.signature(
                callable_obj
            )
        except (
            TypeError,
            ValueError,
        ):
            return kwargs

        parameters = signature.parameters

        accepts_kwargs = any(
            parameter.kind
            == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )

        if accepts_kwargs:
            return kwargs

        supported = set(
            parameters.keys()
        )

        return {
            key: value
            for key, value in kwargs.items()
            if key in supported
        }

    # ==================================================================
    # RETRIEVAL MODE
    # ==================================================================

    def _resolve_retrieval_mode(
        self,
        *,
        request: AdaptiveRAGRequest,
        state: RuntimeAdaptiveRAGState,
    ) -> str:
        request_mode = getattr(
            request,
            "retrieval_mode",
            None,
        )

        resolved = (
            self._normalize_retrieval_mode_value(
                request_mode
            )
        )

        if resolved is not None:
            return resolved

        metadata = (
            getattr(
                request,
                "metadata",
                None,
            )
            or {}
        )

        metadata_mode = metadata.get(
            "retrieval_mode"
        )

        resolved = (
            self._normalize_retrieval_mode_value(
                metadata_mode
            )
        )

        if resolved is not None:
            return resolved

        planner_mode = state.metadata.get(
            "planner_retrieval_mode"
        )

        resolved = (
            self._normalize_retrieval_mode_value(
                planner_mode
            )
        )

        if resolved is not None:
            return resolved

        planner_mode = state.metadata.get(
            "planner_mode"
        )

        resolved = (
            self._normalize_retrieval_mode_value(
                planner_mode
            )
        )

        if resolved is not None:
            return resolved

        return "hybrid"

    @staticmethod
    def _normalize_retrieval_mode_value(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        raw = getattr(
            value,
            "value",
            value,
        )

        if raw is None:
            return None

        normalized = str(
            raw
        ).strip().lower()

        aliases = {
            "dense": "vector",
            "vector": "vector",
            "sparse": "keyword",
            "bm25": "keyword",
            "keyword": "keyword",
            "hybrid": "hybrid",
        }

        return aliases.get(
            normalized
        )

    # ==================================================================
    # RETRIEVAL TELEMETRY
    # ==================================================================

    def _ensure_result_retrieval_steps(
        self,
        result: Any,
        *,
        request: AdaptiveRAGRequest,
        state: RuntimeAdaptiveRAGState,
        retrieval_mode: str,
        duration_ms: int,
    ) -> None:
        if result is None:
            return

        existing_steps = self._get_result_field(
            result,
            "retrieval_steps",
        )

        if existing_steps:
            return

        documents = self._extract_result_documents(
            result
        )

        if not documents:
            return

        step = {
            "step": 1,
            "query": request.query,
            "mode": retrieval_mode,
            "strategy": self._api_strategy(
                state.strategy
            ),
            "chunks": self._safe_api_chunks(
                documents
            ),
            "result_count": len(
                documents
            ),
            "duration_ms": duration_ms,
        }

        self._set_result_field(
            result,
            "retrieval_steps",
            [step],
        )

    def _ensure_retrieval_steps(
        self,
        state: RuntimeAdaptiveRAGState,
        *,
        request: AdaptiveRAGRequest,
    ) -> None:
        if state.retrieval_steps:
            return

        chunks = (
            state.retrieved_chunks
            or []
        )

        if not chunks:
            return

        retrieval_mode = self._resolve_retrieval_mode(
            request=request,
            state=state,
        )

        state.retrieval_steps = [
            {
                "step": 1,
                "query": request.query,
                "mode": retrieval_mode,
                "strategy": self._api_strategy(
                    state.strategy
                ),
                "chunks": self._safe_api_chunks(
                    chunks
                ),
                "result_count": len(
                    chunks
                ),
                "duration_ms": None,
            }
        ]

    @staticmethod
    def _get_result_field(
        result: Any,
        field_name: str,
    ) -> Any:
        if isinstance(
            result,
            Mapping,
        ):
            return result.get(
                field_name
            )

        return getattr(
            result,
            field_name,
            None,
        )

    @staticmethod
    def _set_result_field(
        result: Any,
        field_name: str,
        value: Any,
    ) -> None:
        if isinstance(
            result,
            dict,
        ):
            result[field_name] = value
            return

        try:
            setattr(
                result,
                field_name,
                value,
            )
        except Exception:
            logger.debug(
                "Could not attach %s to %s",
                field_name,
                type(result).__name__,
                exc_info=True,
            )

    @classmethod
    def _extract_result_documents(
        cls,
        result: Any,
    ) -> list[Any]:
        """
        Extract retrieval evidence from the many result shapes used
        across the Adaptive RAG strategies.

        Supported:

            result.documents
            result.retrieved_chunks
            result.retrieval_results
            result.retrieval_result
            result.retrieval_response
            result.retrieval
            result.sources
            result.results
            result.chunks
            result.items

        Also unwraps nested objects such as:

            result.retrieval_response.results
            result.retrieval_result.documents
            result.retrieval.documents
        """

        if result is None:
            return []

        candidate_fields = (
            "documents",
            "retrieved_chunks",
            "retrieval_results",
            "retrieval_result",
            "retrieval_response",
            "retrieval",
            "sources",
            "results",
            "chunks",
            "items",
        )

        visited: set[int] = set()

        def extract(
            value: Any,
            depth: int = 0,
        ) -> list[Any]:
            if value is None:
                return []

            if depth > 4:
                return []

            value_identity = id(value)

            if value_identity in visited:
                return []

            visited.add(
                value_identity
            )

            if isinstance(
                value,
                (list, tuple),
            ):
                return list(value)

            if isinstance(
                value,
                set,
            ):
                return list(value)

            if isinstance(
                value,
                Mapping,
            ):
                for field_name in candidate_fields:
                    if field_name not in value:
                        continue

                    candidate = value.get(
                        field_name
                    )

                    if candidate is None:
                        continue

                    extracted = extract(
                        candidate,
                        depth + 1,
                    )

                    if extracted:
                        return extracted

                # A mapping that itself looks like a retrieval
                # document is a valid single result.
                if any(
                    key in value
                    for key in (
                        "content",
                        "text",
                        "page_content",
                        "chunk_id",
                        "document_id",
                        "score",
                        "similarity",
                    )
                ):
                    return [value]

                return []

            for field_name in candidate_fields:
                candidate = getattr(
                    value,
                    field_name,
                    None,
                )

                if candidate is None:
                    continue

                extracted = extract(
                    candidate,
                    depth + 1,
                )

                if extracted:
                    return extracted

            # A retrieval result/document object itself.
            if any(
                getattr(
                    value,
                    key,
                    None,
                )
                is not None
                for key in (
                    "content",
                    "text",
                    "page_content",
                    "chunk_id",
                    "document_id",
                    "score",
                    "similarity",
                )
            ):
                return [value]

            return []

        return extract(
            result
        )

    @staticmethod
    def _as_list(
        value: Any,
    ) -> list[Any]:
        if value is None:
            return []

        if isinstance(
            value,
            (list, tuple),
        ):
            return list(value)

        if isinstance(
            value,
            set,
        ):
            return list(value)

        return [value]

    # ==================================================================
    # EVALUATION
    # ==================================================================

    async def _evaluate_state(
        self,
        state: RuntimeAdaptiveRAGState,
    ) -> Any:
        evaluate = getattr(
            self.evaluator,
            "evaluate",
            None,
        )

        if evaluate is None or not callable(evaluate):
            raise TypeError(
                "AdaptiveRAGEvaluator does not expose evaluate()"
            )

        result = evaluate(state)

        if inspect.isawaitable(result):
            result = await result

        return result

    @staticmethod
    def _extract_confidence(
        evaluation: Any,
    ) -> float:
        if evaluation is None:
            return 0.0

        if isinstance(
            evaluation,
            Mapping,
        ):
            value = evaluation.get(
                "confidence"
            )

            if value is None:
                value = evaluation.get(
                    "score"
                )

        else:
            value = getattr(
                evaluation,
                "confidence",
                None,
            )

            if value is None:
                value = getattr(
                    evaluation,
                    "score",
                    None,
                )

        if value is None:
            return 0.0

        if hasattr(
            value,
            "score",
        ):
            value = value.score

        try:
            value = float(
                value
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

    # ==================================================================
    # RESULT APPLICATION
    # ==================================================================

    def _apply_strategy_result(
        self,
        state: RuntimeAdaptiveRAGState,
        result: Any,
    ) -> None:
        if result is None:
            return

        answer = self._get_result_field(
            result,
            "answer",
        )

        if answer is not None:
            state.answer = str(
                answer
            )

        # --------------------------------------------------------------
        # Primary extraction
        # --------------------------------------------------------------

        chunks = self._extract_result_documents(
            result
        )

        # --------------------------------------------------------------
        # Some strategies expose retrieval evidence through nested
        # result metadata. Try that before giving up.
        # --------------------------------------------------------------

        if not chunks:
            metadata = self._get_result_field(
                result,
                "metadata",
            )

            if isinstance(
                metadata,
                Mapping,
            ):
                chunks = (
                    self._extract_result_documents(
                        metadata
                    )
                )

        # --------------------------------------------------------------
        # Normalize and surface evidence.
        # --------------------------------------------------------------

        if chunks:
            normalized_chunks = (
                self._normalize_runtime_chunks(
                    chunks
                )
            )

            if normalized_chunks:
                state.retrieved_chunks = (
                    normalized_chunks
                )

                logger.info(
                    "Adaptive RAG surfaced %s retrieved chunks.",
                    len(
                        normalized_chunks
                    ),
                )
            else:
                logger.warning(
                    "Retrieval returned %s raw chunks, "
                    "but runtime normalization produced zero chunks.",
                    len(
                        chunks
                    ),
                )

        retrieval_steps = self._get_result_field(
            result,
            "retrieval_steps",
        )

        if retrieval_steps is not None:
            state.retrieval_steps = list(
                retrieval_steps
            )

        iteration = self._get_result_field(
            result,
            "iteration",
        )

        if iteration is None:
            iteration = self._get_result_field(
                result,
                "iterations",
            )

        if iteration is not None:
            try:
                state.iteration = int(
                    iteration
                )
            except (
                TypeError,
                ValueError,
            ):
                logger.debug(
                    "Invalid strategy iteration: %r",
                    iteration,
                )

        metadata = self._get_result_field(
            result,
            "metadata",
        )

        if isinstance(
            metadata,
            Mapping,
        ):
            state.metadata.update(
                dict(metadata)
            )

        error = self._get_result_field(
            result,
            "error",
        )

        if error:
            state.error = str(
                error
            )

    # ==================================================================
    # RESPONSE
    # ==================================================================

    def _build_response(
        self,
        *,
        execution_id: str,
        state: RuntimeAdaptiveRAGState,
        started_at: datetime,
    ) -> AdaptiveRAGResponse:
        completed_at = self._get_datetime(
            state.metadata.get(
                "completed_at"
            )
        )

        duration_ms = state.metadata.get(
            "duration_ms"
        )

        try:
            duration_ms = (
                float(duration_ms)
                if duration_ms is not None
                else None
            )
        except (
            TypeError,
            ValueError,
        ):
            duration_ms = None

        return AdaptiveRAGResponse(
            execution_id=execution_id,
            status=self._api_status(
                state.status
            ),
            query=state.query,
            answer=state.answer,
            strategy=self._api_strategy(
                state.strategy
            ),
            routing_decision=(
                self._api_routing_decision(
                    state.routing_decision
                )
            ),
            state=self._to_api_state(
                state,
                execution_id=execution_id,
            ),
            plan=self._to_query_plan(
                state.plan
            ),
            confidence=self._to_confidence_score(
                state.confidence
            ),
            evaluation=self._to_evaluation_result(
                state.evaluation
            ),
            sources=self._to_api_chunks(
                state.retrieved_chunks
            ),
            retrieval_steps=(
                self._to_api_retrieval_steps(
                    state.retrieval_steps
                )
            ),
            iterations=state.iteration,
            duration_ms=duration_ms,
            error=state.error,
        )

    def _to_api_state(
        self,
        state: RuntimeAdaptiveRAGState,
        *,
        execution_id: str | None = None,
    ) -> AdaptiveRAGState:
        resolved_execution_id = (
            execution_id
            or state.metadata.get(
                "execution_id"
            )
            or str(uuid.uuid4())
        )

        return AdaptiveRAGState(
            execution_id=str(
                resolved_execution_id
            ),
            query=state.query,
            status=self._api_status(
                state.status
            ),
            iteration=state.iteration,
            max_iterations=state.max_iterations,
            strategy=self._api_strategy(
                state.strategy
            ),
            routing_decision=(
                self._api_routing_decision(
                    state.routing_decision
                )
            ),
            plan=self._to_query_plan(
                state.plan
            ),
            retrieval_steps=(
                self._to_api_retrieval_steps(
                    state.retrieval_steps
                )
            ),
            retrieved_chunks=self._to_api_chunks(
                state.retrieved_chunks
            ),
            answer=state.answer,
            confidence=self._to_confidence_score(
                state.confidence
            ),
            evaluation=self._to_evaluation_result(
                state.evaluation
            ),
            error=state.error,
            started_at=self._get_datetime(
                state.metadata.get(
                    "started_at"
                )
            ),
            completed_at=self._get_datetime(
                state.metadata.get(
                    "completed_at"
                )
            ),
            metadata=dict(
                state.metadata
            ),
        )

    # ==================================================================
    # API ENUM CONVERSION
    # ==================================================================

    @staticmethod
    def _api_status(
        value: Any,
    ) -> ExecutionStatus:
        if isinstance(
            value,
            ExecutionStatus,
        ):
            return value

        raw = getattr(
            value,
            "value",
            value,
        )

        try:
            return ExecutionStatus(
                raw
            )
        except (
            TypeError,
            ValueError,
        ):
            return ExecutionStatus.FAILED

    @staticmethod
    def _api_strategy(
        value: Any,
    ) -> RAGStrategy:
        if isinstance(
            value,
            RAGStrategy,
        ):
            return value

        raw = getattr(
            value,
            "value",
            value,
        )

        if raw is None:
            return RAGStrategy.DIRECT

        normalized = str(
            raw
        ).strip().lower()

        aliases = {
            "direct": RAGStrategy.DIRECT,
            "iterative": RAGStrategy.ITERATIVE,
            "multi_query": RAGStrategy.MULTI_QUERY,
            "multi-query": RAGStrategy.MULTI_QUERY,
            "multiquery": RAGStrategy.MULTI_QUERY,
            "corrective": RAGStrategy.CORRECTIVE,
            "graph_augmented": (
                RAGStrategy.GRAPH_AUGMENTED
            ),
            "graph-augmented": (
                RAGStrategy.GRAPH_AUGMENTED
            ),
            "graph": RAGStrategy.GRAPH_AUGMENTED,
            "vector": RAGStrategy.DIRECT,
            "dense": RAGStrategy.DIRECT,
            "keyword": RAGStrategy.DIRECT,
            "bm25": RAGStrategy.DIRECT,
            "sparse": RAGStrategy.DIRECT,
            "hybrid": RAGStrategy.ITERATIVE,
            "broad": RAGStrategy.GRAPH_AUGMENTED,
        }

        return aliases.get(
            normalized,
            RAGStrategy.DIRECT,
        )

    # ==================================================================
    # ROUTING
    # ==================================================================

    def _api_routing_decision(
        self,
        value: Any,
    ) -> RoutingDecision | None:
        if value is None:
            return None

        if isinstance(
            value,
            RoutingDecision,
        ):
            return value

        if isinstance(
            value,
            Mapping,
        ):
            raw = (
                value.get("decision")
                or value.get("action")
                or value.get("routing_decision")
                or value.get("value")
            )
        else:
            raw = (
                getattr(
                    value,
                    "decision",
                    None,
                )
                or getattr(
                    value,
                    "action",
                    None,
                )
                or getattr(
                    value,
                    "routing_decision",
                    None,
                )
                or getattr(
                    value,
                    "value",
                    None,
                )
            )

        if raw is None:
            strategy = self._api_strategy(
                value
            )

            if strategy == RAGStrategy.DIRECT:
                return RoutingDecision.DIRECT

            return RoutingDecision.RETRIEVE

        normalized = str(
            getattr(
                raw,
                "value",
                raw,
            )
        ).strip().lower()

        aliases = {
            "direct": RoutingDecision.DIRECT,
            "retrieve": RoutingDecision.RETRIEVE,
            "retrieval": RoutingDecision.RETRIEVE,
            "refine": RoutingDecision.REFINE,
            "retry": RoutingDecision.RETRY,
            "stop": RoutingDecision.STOP,
            "continue": RoutingDecision.REFINE,
        }

        return aliases.get(
            normalized,
            RoutingDecision.RETRIEVE,
        )

    def _select_strategy_from_routing(
        self,
        routing_decision: Any,
        *,
        fallback: RAGStrategy,
    ) -> RAGStrategy:
        if routing_decision is None:
            return fallback

        if isinstance(
            routing_decision,
            RAGStrategy,
        ):
            return routing_decision

        if isinstance(
            routing_decision,
            Mapping,
        ):
            strategy = routing_decision.get(
                "strategy"
            )

            if strategy is not None:
                return self._api_strategy(
                    strategy
                )

        strategy = getattr(
            routing_decision,
            "strategy",
            None,
        )

        if strategy is not None:
            return self._api_strategy(
                strategy
            )

        return fallback

    # ==================================================================
    # PLANNING
    # ==================================================================

    def _to_query_plan(
        self,
        value: Any,
    ) -> QueryPlan | None:
        if value is None:
            return None

        if isinstance(
            value,
            QueryPlan,
        ):
            return value

        data = self._object_to_dict(
            value
        )

        raw_strategy = data.get(
            "strategy",
            RAGStrategy.DIRECT,
        )

        reasoning = data.get(
            "reasoning"
        )

        estimated_iterations = data.get(
            "max_queries"
        )

        if estimated_iterations is None:
            estimated_iterations = data.get(
                "estimated_iterations",
                1,
            )

        retrieval_required = bool(
            data.get(
                "retrieval_required",
                True,
            )
        )

        graph_required = bool(
            data.get(
                "graph_required",
                False,
            )
        )

        steps_value = data.get(
            "steps"
        )

        strategy = self._api_strategy(
            raw_strategy
        )

        steps: list[str] = []

        if steps_value:
            if isinstance(
                steps_value,
                (list, tuple),
            ):
                for item in steps_value:
                    if item is None:
                        continue

                    if isinstance(
                        item,
                        Mapping,
                    ):
                        step_text = (
                            item.get("description")
                            or item.get("name")
                            or item.get("step")
                        )

                        if step_text is not None:
                            steps.append(
                                str(step_text)
                            )
                    else:
                        steps.append(
                            str(item)
                        )

        if reasoning and not steps:
            steps.append(
                str(reasoning)
            )

        try:
            estimated_iterations = int(
                estimated_iterations
            )
        except (
            TypeError,
            ValueError,
        ):
            estimated_iterations = 1

        estimated_iterations = max(
            1,
            estimated_iterations,
        )

        payload = {
            "strategy": strategy,
            "reasoning": (
                str(reasoning)
                if reasoning is not None
                else None
            ),
            "steps": steps,
            "estimated_iterations": (
                estimated_iterations
            ),
            "retrieval_required": (
                retrieval_required
            ),
            "graph_required": (
                graph_required
            ),
            "multi_query_required": (
                self._is_multi_query_strategy(
                    strategy
                )
            ),
            "corrective_retrieval": (
                strategy
                == RAGStrategy.CORRECTIVE
            ),
        }

        return self._construct_model(
            QueryPlan,
            payload,
        )

    # ==================================================================
    # CONFIDENCE
    # ==================================================================

    def _to_confidence_score(
        self,
        value: Any,
    ) -> ConfidenceScore | None:
        if value is None:
            return None

        if isinstance(
            value,
            ConfidenceScore,
        ):
            return value

        if isinstance(
            value,
            Mapping,
        ):
            score = value.get(
                "score"
            )

            if score is None:
                score = value.get(
                    "confidence"
                )

            level = value.get(
                "level"
            )

            threshold = value.get(
                "threshold"
            )

            reasons = value.get(
                "reasons",
                [],
            )

            grounded = bool(
                value.get(
                    "grounded",
                    False,
                )
            )

        else:
            score = getattr(
                value,
                "score",
                None,
            )

            if score is None:
                score = getattr(
                    value,
                    "confidence",
                    0.0,
                )

            level = getattr(
                value,
                "level",
                None,
            )

            threshold = getattr(
                value,
                "threshold",
                None,
            )

            reasons = getattr(
                value,
                "reasons",
                [],
            )

            grounded = bool(
                getattr(
                    value,
                    "grounded",
                    False,
                )
            )

        if hasattr(
            score,
            "score",
        ):
            score = score.score

        try:
            score = float(
                score
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            score = 0.0

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        if level is None:
            if score >= 0.8:
                level = ConfidenceLevel.HIGH
            elif score >= 0.5:
                level = ConfidenceLevel.MEDIUM
            else:
                level = ConfidenceLevel.LOW
        else:
            try:
                level = ConfidenceLevel(
                    getattr(
                        level,
                        "value",
                        level,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                if score >= 0.8:
                    level = ConfidenceLevel.HIGH
                elif score >= 0.5:
                    level = ConfidenceLevel.MEDIUM
                else:
                    level = ConfidenceLevel.LOW

        try:
            threshold_value = (
                float(threshold)
                if threshold is not None
                else None
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            threshold_value = None

        payload = {
            "score": score,
            "level": level,
            "threshold": threshold_value,
            "reasons": list(
                reasons or []
            ),
            "grounded": grounded,
        }

        try:
            return self._construct_model(
                ConfidenceScore,
                payload,
            )
        except Exception:
            logger.debug(
                "Could not convert confidence score",
                exc_info=True,
            )
            return None

    # ==================================================================
    # EVALUATION
    # ==================================================================

    def _to_evaluation_result(
        self,
        value: Any,
    ) -> EvaluationResult | None:
        if value is None:
            return None

        if isinstance(
            value,
            EvaluationResult,
        ):
            return value

        data = self._object_to_dict(
            value
        )

        confidence = data.get(
            "confidence"
        )

        answerable = bool(
            data.get(
                "answerable",
                True,
            )
        )

        grounded = bool(
            data.get(
                "grounded",
                False,
            )
        )

        complete = bool(
            data.get(
                "complete",
                True,
            )
        )

        relevant = bool(
            data.get(
                "relevant",
                True,
            )
        )

        should_continue = bool(
            data.get(
                "should_continue",
                False,
            )
        )

        should_retrieve_again = bool(
            data.get(
                "should_retrieve_again",
                False,
            )
        )

        feedback = list(
            data.get(
                "feedback",
                [],
            )
            or []
        )

        missing_information = list(
            data.get(
                "missing_information",
                [],
            )
            or []
        )

        api_confidence = (
            self._to_confidence_score(
                confidence
            )
        )

        if api_confidence is None:
            api_confidence = (
                self._to_confidence_score(
                    self._extract_confidence(
                        value
                    )
                )
            )

        if api_confidence is None:
            api_confidence = ConfidenceScore(
                score=0.0,
                level=ConfidenceLevel.LOW,
                grounded=grounded,
            )

        payload = {
            "confidence": api_confidence,
            "answerable": answerable,
            "grounded": grounded,
            "complete": complete,
            "relevant": relevant,
            "should_continue": should_continue,
            "should_retrieve_again": (
                should_retrieve_again
            ),
            "feedback": feedback,
            "missing_information": (
                missing_information
            ),
        }

        return self._construct_model(
            EvaluationResult,
            payload,
        )

    # ==================================================================
    # API CHUNK ADAPTERS
    # ==================================================================

    def _to_api_chunks(
        self,
        chunks: Any,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        result: list[RetrievedChunk] = []

        for rank, chunk in enumerate(
            chunks,
            start=1,
        ):
            converted = self._normalize_api_chunk(
                chunk,
                default_rank=rank,
            )

            if converted is not None:
                result.append(
                    converted
                )

        return result

    def _safe_api_chunks(
        self,
        chunks: Any,
    ) -> list[dict[str, Any]]:
        if not chunks:
            return []

        result: list[dict[str, Any]] = []

        for rank, chunk in enumerate(
            chunks,
            start=1,
        ):
            converted = self._normalize_api_chunk(
                chunk,
                default_rank=rank,
            )

            if converted is None:
                continue

            result.append(
                self._model_dump(
                    converted
                )
            )

        return result

    def _normalize_api_chunk(
        self,
        chunk: Any,
        *,
        default_rank: int,
    ) -> RetrievedChunk | None:
        if isinstance(
            chunk,
            RetrievedChunk,
        ):
            return chunk

        outer = self._object_to_dict(
            chunk
        )

        # --------------------------------------------------------------
        # Unwrap nested RetrievalResult.document
        # --------------------------------------------------------------

        document_obj = outer.get(
            "document"
        )

        if document_obj is None:
            document_obj = outer.get(
                "retrieved_document"
            )

        document = self._object_to_dict(
            document_obj
        )

        if not document:
            document = dict(
                outer
            )

        # --------------------------------------------------------------
        # Metadata
        # --------------------------------------------------------------

        outer_metadata = outer.get(
            "metadata"
        )

        if not isinstance(
            outer_metadata,
            Mapping,
        ):
            outer_metadata = {}

        document_metadata = document.get(
            "metadata"
        )

        if not isinstance(
            document_metadata,
            Mapping,
        ):
            document_metadata = {}

        metadata: dict[str, Any] = {}

        metadata.update(
            dict(document_metadata)
        )

        metadata.update(
            dict(outer_metadata)
        )

        for source_key in (
            "document_id",
            "document_name",
            "page_number",
            "section_id",
            "chunk_index",
            "source",
            "title",
            "url",
            "filename",
            "file_name",
            "paper_id",
            "arxiv_id",
        ):
            value = document.get(
                source_key
            )

            if value is None:
                value = outer.get(
                    source_key
                )

            if (
                value is not None
                and source_key not in metadata
            ):
                metadata[source_key] = value

        # --------------------------------------------------------------
        # Chunk ID
        # --------------------------------------------------------------

        chunk_id = (
            document.get("chunk_id")
            or document.get("id")
            or document.get("uuid")
            or outer.get("chunk_id")
            or outer.get("id")
            or outer.get("uuid")
        )

        if chunk_id is None:
            logger.error(
                "Cannot normalize API chunk: missing chunk_id. "
                "outer=%r document=%r",
                outer,
                document,
            )
            return None

        chunk_id = str(
            chunk_id
        )

        metadata["chunk_id"] = chunk_id

        # --------------------------------------------------------------
        # Content
        # --------------------------------------------------------------

        content = document.get(
            "content"
        )

        if content is None:
            content = document.get(
                "text"
            )

        if content is None:
            content = document.get(
                "page_content"
            )

        if content is None:
            content = outer.get(
                "content"
            )

        if content is None:
            content = outer.get(
                "text"
            )

        if content is None:
            content = outer.get(
                "page_content"
            )

        if content is None:
            content = ""

        content = str(
            content
        )

        # --------------------------------------------------------------
        # Score
        # --------------------------------------------------------------

        score = outer.get(
            "rerank_score"
        )

        if score is None:
            score = outer.get(
                "score"
            )

        if score is None:
            score = document.get(
                "rerank_score"
            )

        if score is None:
            score = document.get(
                "score"
            )

        if score is None:
            score = document.get(
                "similarity"
            )

        if score is None:
            score = document.get(
                "relevance_score"
            )

        try:
            score = (
                float(score)
                if score is not None
                else 0.0
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            score = 0.0

        # --------------------------------------------------------------
        # Rank
        # --------------------------------------------------------------

        rank = (
            outer.get("rank")
            or document.get("rank")
            or default_rank
        )

        try:
            rank = int(
                rank
            )
        except (
            TypeError,
            ValueError,
        ):
            rank = default_rank

        # --------------------------------------------------------------
        # IDs
        # --------------------------------------------------------------

        document_id = (
            document.get("document_id")
            or outer.get("document_id")
            or metadata.get("document_id")
        )

        if document_id is not None:
            document_id = str(
                document_id
            )

        section_id = (
            document.get("section_id")
            or outer.get("section_id")
            or metadata.get("section_id")
        )

        if section_id is not None:
            section_id = str(
                section_id
            )

        paper_id = (
            document.get("paper_id")
            or outer.get("paper_id")
            or metadata.get("paper_id")
        )

        if paper_id is not None:
            try:
                paper_id = int(
                    paper_id
                )
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                logger.warning(
                    "Invalid API paper_id=%r",
                    paper_id,
                )
                paper_id = None

        # --------------------------------------------------------------
        # Document name
        # --------------------------------------------------------------

        document_name = (
            document.get("document_name")
            or outer.get("document_name")
            or metadata.get("document_name")
            or document.get("title")
            or outer.get("title")
            or metadata.get("title")
            or document.get("filename")
            or metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("source")
        )

        if document_name is not None:
            document_name = str(
                document_name
            )

        # --------------------------------------------------------------
        # Build schema-compatible payload.
        #
        # Different versions of RetrievedChunk may use:
        #     chunk_id
        # or:
        #     id
        #
        # We provide both and let _filter_model_payload()
        # select the actual schema field.
        # --------------------------------------------------------------

        payload = {
            "chunk_id": chunk_id,
            "id": chunk_id,
            "document_id": document_id,
            "paper_id": paper_id,
            "section_id": section_id,
            "document_name": document_name,
            "content": content,
            "score": score,
            "rank": rank,
            "metadata": metadata,
        }

        try:
            return self._construct_model(
                RetrievedChunk,
                payload,
            )

        except Exception:
            logger.exception(
                "Could not normalize API chunk. "
                "chunk_id=%r payload=%r original=%r",
                chunk_id,
                payload,
                chunk,
            )
            return None

    # ==================================================================
    # RUNTIME CHUNK NORMALIZATION
    # ==================================================================

    def _normalize_runtime_chunks(
        self,
        chunks: Any,
    ) -> list[RuntimeRetrievedChunk]:
        if not chunks:
            return []

        result: list[RuntimeRetrievedChunk] = []

        for chunk in chunks:
            normalized = (
                self._normalize_single_chunk(
                    chunk
                )
            )

            if normalized is not None:
                result.append(
                    normalized
                )

        return result

    def _normalize_single_chunk(
        self,
        chunk: Any,
    ) -> RuntimeRetrievedChunk | None:
        """
        Convert retrieval-layer objects into the runtime
        Adaptive RAG RetrievedChunk model.

        Handles:

            RetrievedChunk

        and:

            RetrievalResult(
                document=RetrievedDocument(...),
                rank=...,
                score=...,
            )

        The real chunk ID is always preferred.
        """

        if isinstance(
            chunk,
            RuntimeRetrievedChunk,
        ):
            return chunk

        # --------------------------------------------------------------
        # Outer result
        # --------------------------------------------------------------

        outer = self._object_to_dict(
            chunk
        )

        # --------------------------------------------------------------
        # Nested document
        # --------------------------------------------------------------

        document_obj = outer.get(
            "document"
        )

        if document_obj is None:
            document_obj = outer.get(
                "retrieved_document"
            )

        if document_obj is None:
            document_obj = outer.get(
                "chunk"
            )

        document = self._object_to_dict(
            document_obj
        )

        if not document:
            document = dict(
                outer
            )

        # --------------------------------------------------------------
        # Metadata
        # --------------------------------------------------------------

        outer_metadata = outer.get(
            "metadata"
        )

        if not isinstance(
            outer_metadata,
            Mapping,
        ):
            outer_metadata = {}

        document_metadata = document.get(
            "metadata"
        )

        if not isinstance(
            document_metadata,
            Mapping,
        ):
            document_metadata = {}

        metadata: dict[str, Any] = {}

        metadata.update(
            dict(document_metadata)
        )

        metadata.update(
            dict(outer_metadata)
        )

        # --------------------------------------------------------------
        # Canonical chunk ID
        # --------------------------------------------------------------

        chunk_id = (
            document.get("chunk_id")
            or document.get("id")
            or document.get("uuid")
            or outer.get("chunk_id")
            or outer.get("id")
            or outer.get("uuid")
        )

        if chunk_id is None:
            logger.error(
                "Retrieved result has no chunk_id. "
                "outer=%r document=%r",
                outer,
                document,
            )
            return None

        chunk_id = str(
            chunk_id
        )

        # --------------------------------------------------------------
        # Canonical document ID
        # --------------------------------------------------------------

        document_id = (
            document.get("document_id")
            or outer.get("document_id")
            or metadata.get("document_id")
        )

        if document_id is not None:
            document_id = str(
                document_id
            )

        # --------------------------------------------------------------
        # Paper ID
        #
        # papers.id is INTEGER.
        # --------------------------------------------------------------

        paper_id = (
            document.get("paper_id")
            or outer.get("paper_id")
            or metadata.get("paper_id")
        )

        if paper_id is not None:
            try:
                paper_id = int(
                    paper_id
                )
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                logger.warning(
                    "Invalid paper_id in retrieved chunk: %r",
                    paper_id,
                )
                paper_id = None

        # --------------------------------------------------------------
        # Section ID
        # --------------------------------------------------------------

        section_id = (
            document.get("section_id")
            or outer.get("section_id")
            or metadata.get("section_id")
        )

        if section_id is not None:
            section_id = str(
                section_id
            )

        # --------------------------------------------------------------
        # Content
        # --------------------------------------------------------------

        content = document.get(
            "content"
        )

        if content is None:
            content = document.get(
                "text"
            )

        if content is None:
            content = document.get(
                "page_content"
            )

        if content is None:
            content = outer.get(
                "content"
            )

        if content is None:
            content = outer.get(
                "text"
            )

        if content is None:
            content = outer.get(
                "page_content"
            )

        if content is None:
            content = ""

        content = str(
            content
        )

        # --------------------------------------------------------------
        # Score
        # --------------------------------------------------------------

        score = outer.get(
            "rerank_score"
        )

        if score is None:
            score = outer.get(
                "score"
            )

        if score is None:
            score = document.get(
                "rerank_score"
            )

        if score is None:
            score = document.get(
                "score"
            )

        if score is None:
            score = document.get(
                "similarity"
            )

        if score is None:
            score = document.get(
                "relevance_score"
            )

        try:
            score = (
                float(score)
                if score is not None
                else 0.0
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            score = 0.0

        # --------------------------------------------------------------
        # Rank
        # --------------------------------------------------------------

        rank = (
            outer.get("rank")
            or document.get("rank")
            or 0
        )

        try:
            rank = int(
                rank
            )
        except (
            TypeError,
            ValueError,
        ):
            rank = 0

        # --------------------------------------------------------------
        # Preserve document/retrieval metadata.
        # --------------------------------------------------------------

        for source_key in (
            "document_id",
            "document_name",
            "page_number",
            "section_id",
            "chunk_index",
            "source",
            "title",
            "url",
            "filename",
            "file_name",
            "paper_id",
            "arxiv_id",
        ):
            value = document.get(
                source_key
            )

            if value is None:
                value = outer.get(
                    source_key
                )

            if (
                value is not None
                and source_key not in metadata
            ):
                metadata[source_key] = value

        metadata["chunk_id"] = chunk_id

        if document_id is not None:
            metadata["document_id"] = (
                document_id
            )

        if paper_id is not None:
            metadata["paper_id"] = (
                paper_id
            )

        if section_id is not None:
            metadata["section_id"] = (
                section_id
            )

        # --------------------------------------------------------------
        # Optional descriptive fields.
        # --------------------------------------------------------------

        document_name = (
            document.get("document_name")
            or outer.get("document_name")
            or metadata.get("document_name")
            or document.get("title")
            or outer.get("title")
            or metadata.get("title")
            or document.get("filename")
            or metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("source")
        )

        title = (
            document.get("title")
            or outer.get("title")
            or metadata.get("title")
        )

        source = (
            document.get("source")
            or outer.get("source")
            or metadata.get("source")
        )

        author = (
            document.get("author")
            or outer.get("author")
            or metadata.get("author")
        )

        # --------------------------------------------------------------
        # Canonical runtime payload.
        #
        # We intentionally provide both chunk_id and id because
        # different runtime schema revisions used different names.
        # --------------------------------------------------------------

        payload: dict[str, Any] = {
            "chunk_id": chunk_id,
            "id": chunk_id,
            "document_id": document_id,
            "paper_id": paper_id,
            "section_id": section_id,
            "document_name": (
                str(document_name)
                if document_name is not None
                else None
            ),
            "title": (
                str(title)
                if title is not None
                else None
            ),
            "author": (
                str(author)
                if author is not None
                else None
            ),
            "source": (
                str(source)
                if source is not None
                else None
            ),
            "content": content,
            "score": score,
            "rank": rank,
            "metadata": metadata,
        }

        # --------------------------------------------------------------
        # Construct using actual runtime schema fields.
        # --------------------------------------------------------------

        try:
            filtered_payload = (
                self._filter_model_payload(
                    RuntimeRetrievedChunk,
                    payload,
                )
            )

            normalized = RuntimeRetrievedChunk(
                **filtered_payload
            )

            logger.debug(
                "Normalized runtime chunk: "
                "chunk_id=%s document_id=%s paper_id=%r "
                "score=%s rank=%s",
                chunk_id,
                document_id,
                paper_id,
                score,
                rank,
            )

            return normalized

        except Exception:
            logger.exception(
                "Could not normalize runtime chunk. "
                "chunk_id=%r document_id=%r paper_id=%r "
                "payload=%r original=%r",
                chunk_id,
                document_id,
                paper_id,
                payload,
                chunk,
            )

            return None

    # ==================================================================
    # RETRIEVAL STEPS
    # ==================================================================

    def _to_api_retrieval_steps(
        self,
        steps: Any,
    ) -> list[RetrievalStep]:
        if not steps:
            return []

        result: list[RetrievalStep] = []

        for index, step in enumerate(
            steps,
            start=1,
        ):
            if isinstance(
                step,
                RetrievalStep,
            ):
                result.append(
                    step
                )
                continue

            data = self._object_to_dict(
                step
            )

            if data.get(
                "step"
            ) is None:
                data["step"] = index

            if data.get(
                "query"
            ) is None:
                data["query"] = ""

            mode = (
                data.get("mode")
                or data.get(
                    "retrieval_mode"
                )
                or RetrievalMode.VECTOR
            )

            normalized_mode = (
                self._api_retrieval_mode(
                    mode
                )
            )

            data["mode"] = (
                normalized_mode
                or RetrievalMode.VECTOR
            )

            strategy = data.get(
                "strategy"
            )

            if strategy is not None:
                data["strategy"] = (
                    self._api_strategy(
                        strategy
                    )
                )

            chunks = (
                data.get("chunks")
                if data.get("chunks") is not None
                else data.get("results")
            )

            data["chunks"] = (
                self._to_api_chunks(
                    chunks or []
                )
            )

            if data.get(
                "result_count"
            ) is None:
                data["result_count"] = len(
                    data["chunks"]
                )

            try:
                payload = (
                    self._filter_model_payload(
                        RetrievalStep,
                        data,
                    )
                )

                result.append(
                    RetrievalStep(
                        **payload
                    )
                )

            except Exception:
                logger.exception(
                    "Skipping invalid retrieval step: %r",
                    step,
                )

        return result

    @staticmethod
    def _api_retrieval_mode(
        value: Any,
    ) -> RetrievalMode | None:
        if value is None:
            return None

        if isinstance(
            value,
            RetrievalMode,
        ):
            return value

        raw = getattr(
            value,
            "value",
            value,
        )

        aliases = {
            "dense": "vector",
            "vector": "vector",
            "sparse": "keyword",
            "bm25": "keyword",
            "keyword": "keyword",
            "hybrid": "hybrid",
        }

        normalized = str(
            raw
        ).strip().lower()

        normalized = aliases.get(
            normalized,
            normalized,
        )

        try:
            return RetrievalMode(
                normalized
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    # ==================================================================
    # STRATEGY SELECTION
    # ==================================================================

    def _select_strategy(
        self,
        request: AdaptiveRAGRequest,
    ) -> RAGStrategy:
        request_strategy = getattr(
            request,
            "strategy",
            None,
        )

        if request_strategy is not None:
            return self._api_strategy(
                request_strategy
            )

        return RAGStrategy.DIRECT

    @staticmethod
    def _map_retrieval_strategy(
        strategy: Any,
    ) -> RetrievalStrategy:
        raw = getattr(
            strategy,
            "value",
            strategy,
        )

        normalized = str(
            raw
        ).strip().lower()

        candidates: dict[
            str,
            tuple[str, ...],
        ] = {
            "direct": (
                "direct",
            ),
            "iterative": (
                "iterative",
                "hybrid",
            ),
            "multi_query": (
                "multi_query",
            ),
            "multi-query": (
                "multi_query",
            ),
            "multiquery": (
                "multi_query",
            ),
            "corrective": (
                "corrective",
            ),
            "graph_augmented": (
                "graph_augmented",
                "broad",
            ),
            "graph-augmented": (
                "graph_augmented",
                "broad",
            ),
            "graph": (
                "graph_augmented",
                "broad",
            ),
        }

        values = candidates.get(
            normalized,
            (
                "direct",
            ),
        )

        for candidate in values:
            try:
                member = getattr(
                    RetrievalStrategy,
                    candidate.upper(),
                )

                if member is not None:
                    return member

            except AttributeError:
                pass

        for candidate in values:
            try:
                return RetrievalStrategy(
                    candidate
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        return AdaptiveRAGController._retrieval_direct_member()

    @staticmethod
    def _retrieval_direct_member() -> RetrievalStrategy:
        try:
            return RetrievalStrategy.DIRECT
        except AttributeError:
            try:
                return RetrievalStrategy(
                    "direct"
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise RuntimeError(
                    "RetrievalStrategy does not define a DIRECT/direct "
                    "member."
                ) from exc

    @staticmethod
    def _map_domain_strategy_to_api(
        strategy: Any,
    ) -> RAGStrategy | None:
        if strategy is None:
            return None

        raw = getattr(
            strategy,
            "value",
            strategy,
        )

        normalized = str(
            raw
        ).strip().lower()

        mapping = {
            "direct": RAGStrategy.DIRECT,
            "vector": RAGStrategy.DIRECT,
            "dense": RAGStrategy.DIRECT,
            "keyword": RAGStrategy.DIRECT,
            "bm25": RAGStrategy.DIRECT,
            "sparse": RAGStrategy.DIRECT,
            "hybrid": RAGStrategy.ITERATIVE,
            "iterative": RAGStrategy.ITERATIVE,
            "multi_query": RAGStrategy.MULTI_QUERY,
            "multi-query": RAGStrategy.MULTI_QUERY,
            "multiquery": RAGStrategy.MULTI_QUERY,
            "corrective": RAGStrategy.CORRECTIVE,
            "broad": RAGStrategy.GRAPH_AUGMENTED,
            "graph": RAGStrategy.GRAPH_AUGMENTED,
            "graph_augmented": (
                RAGStrategy.GRAPH_AUGMENTED
            ),
            "graph-augmented": (
                RAGStrategy.GRAPH_AUGMENTED
            ),
        }

        return mapping.get(
            normalized
        )

    @staticmethod
    def _is_multi_query_strategy(
        strategy: RAGStrategy,
    ) -> bool:
        return strategy in {
            RAGStrategy.MULTI_QUERY,
        }

    # ==================================================================
    # EXECUTION MANAGEMENT
    # ==================================================================

    def get_execution(
        self,
        execution_id: str,
    ) -> AdaptiveRAGExecution | None:
        state = self._executions.get(
            execution_id
        )

        if state is None:
            return None

        confidence = self._extract_confidence(
            state.evaluation
        )

        payload = {
            "execution_id": execution_id,
            "query": state.query,
            "status": self._api_status(
                state.status
            ),
            "strategy": self._api_strategy(
                state.strategy
            ),
            "iteration": state.iteration,
            "confidence": (
                confidence
                if state.evaluation is not None
                else None
            ),
            "created_at": self._get_datetime(
                state.metadata.get(
                    "started_at"
                )
            ),
            "completed_at": self._get_datetime(
                state.metadata.get(
                    "completed_at"
                )
            ),
        }

        return self._construct_model(
            AdaptiveRAGExecution,
            payload,
        )

    def get_state(
        self,
        execution_id: str,
    ) -> AdaptiveRAGState | None:
        state = self._executions.get(
            execution_id
        )

        if state is None:
            return None

        return self._to_api_state(
            state,
            execution_id=execution_id,
        )

    def list_executions(
        self,
    ) -> AdaptiveRAGExecutionList:
        executions: list[
            AdaptiveRAGExecution
        ] = []

        for execution_id in self._executions:
            execution = self.get_execution(
                execution_id
            )

            if execution is not None:
                executions.append(
                    execution
                )

        return AdaptiveRAGExecutionList(
            items=executions,
            total=len(executions),
        )

    def stop(
        self,
        execution_id: str,
    ) -> bool:
        state = self._executions.get(
            execution_id
        )

        if state is None:
            return False

        state.status = ExecutionStatus.STOPPED

        state.metadata["completed_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return True

    # ==================================================================
    # HEALTH / CONFIGURATION
    # ==================================================================

    def health(
        self,
    ) -> AdaptiveRAGHealth:
        return AdaptiveRAGHealth(
            status="healthy",
            adaptive_rag_enabled=True,
            available_strategies=list(
                self._strategies.keys()
            ),
            version=self.VERSION,
        )

    def config(
        self,
    ) -> AdaptiveRAGConfig:
        return AdaptiveRAGConfig(
            default_strategy=RAGStrategy.DIRECT,
            default_top_k=5,
            default_max_iterations=3,
            default_confidence_threshold=0.75,
            enabled_strategies=list(
                self._strategies.keys()
            ),
            enabled_retrieval_modes=list(
                RetrievalMode
            ),
            graph_enabled=True,
            corrective_retrieval_enabled=True,
            multi_query_enabled=True,
        )

    # ==================================================================
    # INTERNAL HELPERS
    # ==================================================================

    def _get_state(
        self,
        execution_id: str,
    ) -> RuntimeAdaptiveRAGState:
        state = self._executions.get(
            execution_id
        )

        if state is None:
            raise KeyError(
                "Adaptive RAG execution not found: "
                f"{execution_id}"
            )

        return state

    @staticmethod
    def _get_field(
        obj: Any,
        field_name: str,
        default: Any = None,
    ) -> Any:
        if obj is None:
            return default

        if isinstance(
            obj,
            Mapping,
        ):
            return obj.get(
                field_name,
                default,
            )

        return getattr(
            obj,
            field_name,
            default,
        )

    @staticmethod
    def _object_to_dict(
        value: Any,
    ) -> dict[str, Any]:
        """
        Convert mappings, Pydantic models, dataclasses and ordinary
        retrieval objects into dictionaries.

        The explicit fallback field list intentionally contains the
        retrieval-layer fields used by RetrievalResult and
        RetrievedDocument.
        """

        if value is None:
            return {}

        if isinstance(
            value,
            Mapping,
        ):
            return dict(
                value
            )

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                dumped = value.model_dump(
                    mode="python"
                )

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(
                        dumped
                    )

            except Exception:
                pass

        if hasattr(
            value,
            "dict",
        ):
            try:
                dumped = value.dict()

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(
                        dumped
                    )

            except Exception:
                pass

        result: dict[str, Any] = {}

        fields = (
            # ----------------------------------------------------------
            # Planner
            # ----------------------------------------------------------
            "strategy",
            "mode",
            "retrieval_mode",
            "top_k",
            "max_queries",
            "vector_weight",
            "keyword_weight",
            "filters",
            "query_variants",
            "reasoning",
            "retrieval_required",
            "graph_required",
            "steps",

            # ----------------------------------------------------------
            # Evaluation
            # ----------------------------------------------------------
            "confidence",
            "answerable",
            "grounded",
            "complete",
            "relevant",
            "should_continue",
            "should_retrieve_again",
            "feedback",
            "missing_information",

            # ----------------------------------------------------------
            # Retrieval containers
            # ----------------------------------------------------------
            "document",
            "retrieved_document",
            "retrieval_result",
            "retrieval_response",
            "retrieval",
            "documents",
            "retrieved_chunks",
            "retrieval_results",
            "sources",
            "results",
            "chunks",
            "items",

            # ----------------------------------------------------------
            # Retrieval document/result
            # ----------------------------------------------------------
            "id",
            "chunk_id",
            "uuid",
            "document_id",
            "paper_id",
            "section_id",
            "document_name",
            "content",
            "text",
            "page_content",
            "score",
            "rerank_score",
            "similarity",
            "relevance_score",
            "rank",
            "metadata",

            # ----------------------------------------------------------
            # Document metadata
            # ----------------------------------------------------------
            "source",
            "title",
            "author",
            "url",
            "filename",
            "file_name",
            "page_number",
            "chunk_index",
            "arxiv_id",

            # ----------------------------------------------------------
            # Strategy result
            # ----------------------------------------------------------
            "answer",
            "error",
            "iteration",
            "iterations",
            "retrieval_steps",
        )

        for name in fields:
            value_for_field = getattr(
                value,
                name,
                None,
            )

            if value_for_field is not None:
                result[name] = (
                    value_for_field
                )

        return result

    @staticmethod
    def _get_datetime(
        value: Any,
    ) -> datetime | None:
        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        try:
            return datetime.fromisoformat(
                str(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _serialize_for_metadata(
        value: Any,
    ) -> Any:
        if value is None:
            return None

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                return value.model_dump(
                    mode="json"
                )
            except Exception:
                pass

        if hasattr(
            value,
            "value",
        ):
            raw = value.value

            if isinstance(
                raw,
                (
                    str,
                    int,
                    float,
                    bool,
                ),
            ):
                return raw

        if isinstance(
            value,
            Mapping,
        ):
            return {
                str(key): (
                    AdaptiveRAGController
                    ._serialize_for_metadata(
                        item
                    )
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            return [
                AdaptiveRAGController
                ._serialize_for_metadata(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        return str(
            value
        )

    # ==================================================================
    # PYDANTIC COMPATIBILITY HELPERS
    # ==================================================================

    @staticmethod
    def _model_field_names(
        model_type: Any,
    ) -> set[str]:
        """
        Supports both Pydantic v2 and v1.
        """

        fields = getattr(
            model_type,
            "model_fields",
            None,
        )

        if fields:
            return set(
                fields.keys()
            )

        fields = getattr(
            model_type,
            "__fields__",
            None,
        )

        if fields:
            return set(
                fields.keys()
            )

        annotations = getattr(
            model_type,
            "__annotations__",
            None,
        )

        if annotations:
            return set(
                annotations.keys()
            )

        return set()

    @classmethod
    def _filter_model_payload(
        cls,
        model_type: Any,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        fields = cls._model_field_names(
            model_type
        )

        if not fields:
            return dict(
                payload
            )

        return {
            key: value
            for key, value in payload.items()
            if key in fields
        }

    @classmethod
    def _construct_model(
        cls,
        model_type: Any,
        payload: Mapping[str, Any],
    ) -> Any:
        filtered = cls._filter_model_payload(
            model_type,
            payload,
        )

        return model_type(
            **filtered
        )

    @staticmethod
    def _model_dump(
        model: Any,
    ) -> dict[str, Any]:
        if hasattr(
            model,
            "model_dump",
        ):
            try:
                return model.model_dump(
                    mode="json"
                )
            except Exception:
                pass

        if hasattr(
            model,
            "dict",
        ):
            try:
                return model.dict()
            except Exception:
                pass

        if isinstance(
            model,
            Mapping,
        ):
            return dict(
                model
            )

        return {
            "value": str(
                model
            )
        }


__all__ = [
    "AdaptiveRAGController",
]