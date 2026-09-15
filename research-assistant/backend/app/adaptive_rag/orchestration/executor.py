
from __future__ import annotations

import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional
from uuid import uuid4

from .planner import PlanStep

logger = logging.getLogger(__name__)


class ExecutionError(RuntimeError):
    """Raised for unrecoverable execution failures."""


@dataclass(slots=True)
class ExecutionResult:
    """Result of executing one plan step."""

    execution_id: str
    step_id: str
    step_type: str

    success: bool

    output: Any = None
    final_answer: Any = None
    error: Optional[str] = None

    latency_ms: float = 0.0

    tokens_used: int = 0
    cost: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionContext:
    """
    Mutable state shared between orchestration steps.

    This object intentionally contains only orchestration state.
    Domain-specific objects should remain in their respective layers.
    """

    request_id: str
    query: str

    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    results: dict[str, ExecutionResult] = field(default_factory=dict)

    final_answer: Any = None

    def add_result(self, result: ExecutionResult) -> None:
        self.results[result.step_id] = result

        if result.final_answer is not None:
            self.final_answer = result.final_answer

    def get_result(self, step_id: str) -> Optional[ExecutionResult]:
        return self.results.get(step_id)

    def successful_outputs(self) -> dict[str, Any]:
        return {
            step_id: result.output
            for step_id, result in self.results.items()
            if result.success
        }


class Executor:
    """
    Generic orchestration executor.

    `handlers` maps plan step types to implementations.

    Example:

        Executor(
            handlers={
                "analyze": analyzer,
                "retrieve": retriever,
                "evaluate": evaluator,
                "generate": generator,
            }
        )

    A handler may expose:

        async def execute(...)

    or:

        async def run(...)

    or:

        callable(...)

    Both synchronous and asynchronous handlers are supported.
    """

    def __init__(
        self,
        *,
        handlers: Mapping[str, Any],
        default_timeout_seconds: Optional[float] = None,
    ) -> None:
        if not handlers:
            raise ValueError("At least one executor handler is required")

        if (
            default_timeout_seconds is not None
            and default_timeout_seconds <= 0
        ):
            raise ValueError(
                "default_timeout_seconds must be positive"
            )

        self._handlers = dict(handlers)
        self._default_timeout_seconds = default_timeout_seconds

    async def execute(
        self,
        *,
        step: PlanStep,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute one plan step.
        """

        execution_id = str(uuid4())
        started = time.perf_counter()

        handler = self._handlers.get(step.step_type)

        if handler is None:
            return ExecutionResult(
                execution_id=execution_id,
                step_id=step.step_id,
                step_type=step.step_type,
                success=False,
                error=(
                    f"No executor handler registered for "
                    f"step type '{step.step_type}'"
                ),
            )

        logger.debug(
            "Executing handler",
            extra={
                "request_id": context.request_id,
                "execution_id": execution_id,
                "step_id": step.step_id,
                "step_type": step.step_type,
            },
        )

        try:
            raw_result = await self._invoke_handler(
                handler=handler,
                step=step,
                context=context,
            )

            normalized = self._normalize_result(
                execution_id=execution_id,
                step=step,
                raw_result=raw_result,
            )

            normalized.latency_ms = (
                time.perf_counter() - started
            ) * 1000.0

            return normalized

        except Exception as exc:
            latency_ms = (
                time.perf_counter() - started
            ) * 1000.0

            logger.exception(
                "Execution step failed",
                extra={
                    "request_id": context.request_id,
                    "execution_id": execution_id,
                    "step_id": step.step_id,
                },
            )

            return ExecutionResult(
                execution_id=execution_id,
                step_id=step.step_id,
                step_type=step.step_type,
                success=False,
                error=str(exc),
                latency_ms=latency_ms,
            )

    async def _invoke_handler(
        self,
        *,
        handler: Any,
        step: PlanStep,
        context: ExecutionContext,
    ) -> Any:
        """
        Resolve the supported handler interface.
        """

        if hasattr(handler, "execute"):
            method = handler.execute

        elif hasattr(handler, "run"):
            method = handler.run

        elif callable(handler):
            method = handler

        else:
            raise ExecutionError(
                f"Handler for '{step.step_type}' is not executable"
            )

        kwargs = {
            "step": step,
            "context": context,
            "parameters": dict(step.parameters),
        }

        result = self._call_with_supported_arguments(
            method,
            kwargs,
        )

        if inspect.isawaitable(result):
            return await result

        return result

    @staticmethod
    def _call_with_supported_arguments(
        method: Any,
        kwargs: Mapping[str, Any],
    ) -> Any:
        """
        Pass only arguments supported by the handler.

        This allows simple handlers such as:

            async def run(query)

        alongside richer handlers such as:

            async def execute(step, context, parameters)
        """

        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            return method(**kwargs)

        parameters = signature.parameters

        accepts_kwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )

        if accepts_kwargs:
            return method(**kwargs)

        accepted = {
            key: value
            for key, value in kwargs.items()
            if key in parameters
        }

        return method(**accepted)

    @staticmethod
    def _normalize_result(
        *,
        execution_id: str,
        step: PlanStep,
        raw_result: Any,
    ) -> ExecutionResult:
        """
        Normalize heterogeneous handler outputs.

        Supported outputs:

        - ExecutionResult
        - dict
        - arbitrary Python value
        - None
        """

        if isinstance(raw_result, ExecutionResult):
            raw_result.execution_id = execution_id
            raw_result.step_id = step.step_id
            raw_result.step_type = step.step_type
            return raw_result

        if isinstance(raw_result, Mapping):
            output = raw_result.get(
                "output",
                raw_result.get("result"),
            )

            return ExecutionResult(
                execution_id=execution_id,
                step_id=step.step_id,
                step_type=step.step_type,
                success=bool(raw_result.get("success", True)),
                output=output,
                final_answer=raw_result.get("final_answer"),
                error=raw_result.get("error"),
                tokens_used=int(
                    raw_result.get("tokens_used", 0) or 0
                ),
                cost=float(
                    raw_result.get("cost", 0.0) or 0.0
                ),
                metadata=dict(
                    raw_result.get("metadata", {}) or {}
                ),
            )

        return ExecutionResult(
            execution_id=execution_id,
            step_id=step.step_id,
            step_type=step.step_type,
            success=True,
            output=raw_result,
        )

