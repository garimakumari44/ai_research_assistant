
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Sequence
from uuid import uuid4

from .budget_manager import (
    BudgetExceededError,
    BudgetManager,
    BudgetSnapshot,
)
from .executor import (
    ExecutionContext,
    ExecutionResult,
    Executor,
)
from .planner import (
    ExecutionPlan,
    Planner,
    PlanningError,
)

logger = logging.getLogger(__name__)


class OrchestrationStatus(str, Enum):
    """Lifecycle status of an orchestration request."""

    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(slots=True)
class OrchestrationRequest:
    """
    Input to the orchestration layer.

    Parameters
    ----------
    query:
        User's research/query request.

    context:
        Optional contextual information accumulated by upstream systems.

    metadata:
        Arbitrary request metadata useful for tracing and routing.
    """

    query: str
    context: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")


@dataclass(slots=True)
class OrchestrationResult:
    """Final result returned by the coordinator."""

    request_id: str
    status: OrchestrationStatus
    answer: Any = None

    plan: Optional[ExecutionPlan] = None
    execution_results: list[ExecutionResult] = field(default_factory=list)

    budget: Optional[BudgetSnapshot] = None

    error: Optional[str] = None
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None

    @property
    def success(self) -> bool:
        return self.status == OrchestrationStatus.COMPLETED


class OrchestrationError(RuntimeError):
    """Base exception for orchestration failures."""


class Coordinator:
    """
    High-level Adaptive RAG orchestration coordinator.

    Responsibilities
    ----------------
    1. Validate incoming requests.
    2. Ask the planner to create an execution plan.
    3. Validate the plan against resource budgets.
    4. Execute plan steps.
    5. Track execution state.
    6. Stop safely when budgets are exhausted.
    7. Return a deterministic orchestration result.

    The coordinator intentionally does NOT implement retrieval,
    generation, evidence evaluation, or individual strategies.
    Those concerns belong to their respective layers.

    Typical flow:

        request
           |
           v
        Planner
           |
           v
        ExecutionPlan
           |
           v
        BudgetManager
           |
           v
        Executor
           |
           v
        results
           |
           v
        final answer
    """

    def __init__(
        self,
        *,
        planner: Planner,
        executor: Executor,
        budget_manager: BudgetManager,
    ) -> None:
        if planner is None:
            raise ValueError("planner is required")

        if executor is None:
            raise ValueError("executor is required")

        if budget_manager is None:
            raise ValueError("budget_manager is required")

        self._planner = planner
        self._executor = executor
        self._budget_manager = budget_manager

    async def run(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """
        Execute a complete orchestration request.

        This method is the primary entry point for the orchestration layer.
        """

        request.validate()

        request_id = str(uuid4())
        started_at = datetime.now(timezone.utc)

        logger.info(
            "Starting orchestration",
            extra={
                "request_id": request_id,
                "query_length": len(request.query),
            },
        )

        plan: Optional[ExecutionPlan] = None
        execution_results: list[ExecutionResult] = []

        try:
            self._budget_manager.start_request(request_id)

            # ---------------------------------------------------------
            # Planning
            # ---------------------------------------------------------
            logger.debug(
                "Creating execution plan",
                extra={"request_id": request_id},
            )

            plan = await self._planner.create_plan(
                query=request.query,
                context=request.context,
                metadata=request.metadata,
            )

            self._validate_plan(plan)

            self._budget_manager.reserve_plan(plan)

            # ---------------------------------------------------------
            # Execution
            # ---------------------------------------------------------
            context = ExecutionContext(
                request_id=request_id,
                query=request.query,
                context=dict(request.context),
                metadata=dict(request.metadata),
            )

            for step in plan.steps:
                self._budget_manager.check_before_step(step)

                logger.info(
                    "Executing orchestration step",
                    extra={
                        "request_id": request_id,
                        "step_id": step.step_id,
                        "step_type": step.step_type,
                    },
                )

                result = await self._executor.execute(
                    step=step,
                    context=context,
                )

                execution_results.append(result)

                self._budget_manager.record_step(result)

                context.add_result(result)

                if not result.success:
                    logger.warning(
                        "Orchestration step failed",
                        extra={
                            "request_id": request_id,
                            "step_id": step.step_id,
                            "error": result.error,
                        },
                    )

                    if step.required:
                        raise OrchestrationError(
                            f"Required step '{step.step_id}' failed: "
                            f"{result.error or 'unknown error'}"
                        )

            # ---------------------------------------------------------
            # Final answer
            # ---------------------------------------------------------
            answer = self._build_answer(
                plan=plan,
                results=execution_results,
                context=context,
            )

            self._budget_manager.finish_request()

            completed_at = datetime.now(timezone.utc)

            logger.info(
                "Orchestration completed",
                extra={"request_id": request_id},
            )

            return OrchestrationResult(
                request_id=request_id,
                status=OrchestrationStatus.COMPLETED,
                answer=answer,
                plan=plan,
                execution_results=execution_results,
                budget=self._budget_manager.snapshot(),
                started_at=started_at,
                completed_at=completed_at,
            )

        except BudgetExceededError as exc:
            logger.warning(
                "Orchestration stopped because budget was exceeded",
                extra={
                    "request_id": request_id,
                    "error": str(exc),
                },
            )

            self._budget_manager.abort_request()

            return OrchestrationResult(
                request_id=request_id,
                status=OrchestrationStatus.BUDGET_EXCEEDED,
                plan=plan,
                execution_results=execution_results,
                budget=self._budget_manager.snapshot(),
                error=str(exc),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except PlanningError as exc:
            logger.exception(
                "Planning failed",
                extra={"request_id": request_id},
            )

            self._budget_manager.abort_request()

            return OrchestrationResult(
                request_id=request_id,
                status=OrchestrationStatus.FAILED,
                plan=plan,
                execution_results=execution_results,
                budget=self._budget_manager.snapshot(),
                error=str(exc),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as exc:
            logger.exception(
                "Orchestration failed",
                extra={"request_id": request_id},
            )

            self._budget_manager.abort_request()

            return OrchestrationResult(
                request_id=request_id,
                status=OrchestrationStatus.FAILED,
                plan=plan,
                execution_results=execution_results,
                budget=self._budget_manager.snapshot(),
                error=str(exc),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

    @staticmethod
    def _validate_plan(plan: ExecutionPlan) -> None:
        if plan is None:
            raise PlanningError("Planner returned no execution plan")

        if not plan.steps:
            raise PlanningError("Planner returned an empty execution plan")

        step_ids: set[str] = set()

        for step in plan.steps:
            if step.step_id in step_ids:
                raise PlanningError(
                    f"Duplicate step id: {step.step_id}"
                )

            step_ids.add(step.step_id)

    @staticmethod
    def _build_answer(
        *,
        plan: ExecutionPlan,
        results: Sequence[ExecutionResult],
        context: ExecutionContext,
    ) -> Any:
        """
        Build the final answer from execution output.

        If an executor already produced a final answer, prefer it.
        Otherwise return the accumulated execution context.
        """

        for result in reversed(results):
            if result.final_answer is not None:
                return result.final_answer

        if context.final_answer is not None:
            return context.final_answer

        return {
            "plan_id": plan.plan_id,
            "results": [
                result.output
                for result in results
                if result.success
            ],
        }

