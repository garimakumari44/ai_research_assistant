
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence
from uuid import uuid4

logger = logging.getLogger(__name__)


class PlanningError(RuntimeError):
    """Raised when an execution plan cannot be created or validated."""


class StepType(str, Enum):
    """Supported high-level orchestration operations."""

    ANALYZE = "analyze"
    RETRIEVE = "retrieve"
    EVALUATE = "evaluate"
    REFINE = "refine"
    GENERATE = "generate"
    VERIFY = "verify"


@dataclass(frozen=True, slots=True)
class PlanStep:
    """
    One executable unit in an orchestration plan.
    """

    step_id: str
    step_type: str

    description: str = ""

    parameters: Mapping[str, Any] = field(default_factory=dict)

    depends_on: tuple[str, ...] = ()

    required: bool = True

    estimated_cost: float = 0.0
    estimated_tokens: int = 0

    max_retries: int = 0

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.step_id.strip():
            raise PlanningError("Plan step requires step_id")

        if not self.step_type.strip():
            raise PlanningError(
                f"Plan step '{self.step_id}' requires step_type"
            )

        if self.estimated_cost < 0:
            raise PlanningError(
                f"Negative estimated cost for '{self.step_id}'"
            )

        if self.estimated_tokens < 0:
            raise PlanningError(
                f"Negative estimated tokens for '{self.step_id}'"
            )

        if self.max_retries < 0:
            raise PlanningError(
                f"Negative max_retries for '{self.step_id}'"
            )


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """
    Immutable execution plan produced by Planner.
    """

    plan_id: str

    query: str

    steps: tuple[PlanStep, ...]

    strategy: str = "direct"

    max_iterations: int = 1

    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def estimated_cost(self) -> float:
        return sum(step.estimated_cost for step in self.steps)

    @property
    def estimated_tokens(self) -> int:
        return sum(step.estimated_tokens for step in self.steps)

    def validate(self) -> None:
        if not self.query.strip():
            raise PlanningError("ExecutionPlan query cannot be empty")

        if not self.steps:
            raise PlanningError("ExecutionPlan must contain steps")

        if self.max_iterations < 1:
            raise PlanningError(
                "max_iterations must be >= 1"
            )

        known_ids: set[str] = set()

        for step in self.steps:
            step.validate()

            if step.step_id in known_ids:
                raise PlanningError(
                    f"Duplicate step id: {step.step_id}"
                )

            known_ids.add(step.step_id)

        for step in self.steps:
            for dependency in step.depends_on:
                if dependency not in known_ids:
                    raise PlanningError(
                        f"Step '{step.step_id}' depends on unknown "
                        f"step '{dependency}'"
                    )

        self._validate_dependency_order()

    def _validate_dependency_order(self) -> None:
        """
        Ensure dependencies do not point forward.

        This keeps execution deterministic for a simple sequential
        executor.
        """

        positions = {
            step.step_id: index
            for index, step in enumerate(self.steps)
        }

        for step in self.steps:
            current_position = positions[step.step_id]

            for dependency in step.depends_on:
                dependency_position = positions[dependency]

                if dependency_position >= current_position:
                    raise PlanningError(
                        f"Step '{step.step_id}' depends on "
                        f"'{dependency}', but dependency is not earlier "
                        f"in the plan"
                    )


class Planner:
    """
    Adaptive RAG execution planner.

    The planner converts a user query into an explicit execution graph.

    The default policy is intentionally conservative:

        analyze
           ↓
        retrieve
           ↓
        evaluate
           ↓
        generate

    More sophisticated routing can be injected through
    `strategy_selector`.
    """

    def __init__(
        self,
        *,
        strategy_selector: Optional[Any] = None,
        default_top_k: int = 5,
        max_steps: int = 12,
        max_iterations: int = 3,
    ) -> None:
        if default_top_k < 1:
            raise ValueError("default_top_k must be >= 1")

        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")

        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")

        self._strategy_selector = strategy_selector
        self._default_top_k = default_top_k
        self._max_steps = max_steps
        self._max_iterations = max_iterations

    async def create_plan(
        self,
        *,
        query: str,
        context: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ExecutionPlan:
        """
        Create and validate an execution plan.
        """

        query = query.strip()

        if not query:
            raise PlanningError("Cannot plan an empty query")

        context = context or {}
        metadata = metadata or {}

        strategy = await self._select_strategy(
            query=query,
            context=context,
            metadata=metadata,
        )

        steps = self._build_steps(
            query=query,
            strategy=strategy,
            context=context,
            metadata=metadata,
        )

        if len(steps) > self._max_steps:
            raise PlanningError(
                f"Generated plan contains {len(steps)} steps; "
                f"maximum is {self._max_steps}"
            )

        plan = ExecutionPlan(
            plan_id=str(uuid4()),
            query=query,
            steps=tuple(steps),
            strategy=strategy,
            max_iterations=self._max_iterations,
            metadata={
                "planner": self.__class__.__name__,
            },
        )

        plan.validate()

        logger.info(
            "Execution plan created",
            extra={
                "plan_id": plan.plan_id,
                "strategy": strategy,
                "steps": len(plan.steps),
                "estimated_cost": plan.estimated_cost,
                "estimated_tokens": plan.estimated_tokens,
            },
        )

        return plan

    async def _select_strategy(
        self,
        *,
        query: str,
        context: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> str:
        if self._strategy_selector is None:
            return self._default_strategy(query)

        selector = self._strategy_selector

        if hasattr(selector, "select"):
            strategy = selector.select(
                query=query,
                context=context,
                metadata=metadata,
            )

            if hasattr(strategy, "__await__"):
                strategy = await strategy

        elif callable(selector):
            strategy = selector(
                query=query,
                context=context,
                metadata=metadata,
            )

            if hasattr(strategy, "__await__"):
                strategy = await strategy

        else:
            raise PlanningError(
                "strategy_selector must be callable or expose select()"
            )

        if not strategy:
            raise PlanningError(
                "Strategy selector returned an empty strategy"
            )

        return str(strategy)

    @staticmethod
    def _default_strategy(query: str) -> str:
        """
        Conservative heuristic strategy selection.

        This is deliberately simple; production systems can replace it
        with the Adaptive RAG router.
        """

        normalized = query.lower()

        research_markers = (
            "compare",
            "comparison",
            "why",
            "how",
            "explain",
            "research",
            "evidence",
            "according to",
            "latest",
            "sources",
        )

        if any(marker in normalized for marker in research_markers):
            return "evidence"

        return "direct"

    def _build_steps(
        self,
        *,
        query: str,
        strategy: str,
        context: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> list[PlanStep]:

        steps: list[PlanStep] = []

        steps.append(
            PlanStep(
                step_id="analyze",
                step_type=StepType.ANALYZE.value,
                description="Analyze query intent and retrieval requirements.",
                parameters={
                    "query": query,
                },
                estimated_cost=0.0,
            )
        )

        if strategy == "evidence":
            steps.append(
                PlanStep(
                    step_id="retrieve",
                    step_type=StepType.RETRIEVE.value,
                    description="Retrieve candidate evidence.",
                    parameters={
                        "query": query,
                        "top_k": self._default_top_k,
                        "strategy": strategy,
                    },
                    depends_on=("analyze",),
                    estimated_cost=0.0,
                )
            )

            steps.append(
                PlanStep(
                    step_id="evaluate",
                    step_type=StepType.EVALUATE.value,
                    description="Evaluate evidence quality, coverage, "
                    "and contradictions.",
                    parameters={
                        "query": query,
                    },
                    depends_on=("retrieve",),
                    estimated_cost=0.0,
                )
            )

            steps.append(
                PlanStep(
                    step_id="generate",
                    step_type=StepType.GENERATE.value,
                    description="Generate an answer grounded in evaluated "
                    "evidence.",
                    parameters={
                        "query": query,
                        "grounded": True,
                    },
                    depends_on=("evaluate",),
                    estimated_cost=0.0,
                )
            )

        else:
            steps.append(
                PlanStep(
                    step_id="retrieve",
                    step_type=StepType.RETRIEVE.value,
                    description="Retrieve relevant context.",
                    parameters={
                        "query": query,
                        "top_k": self._default_top_k,
                        "strategy": strategy,
                    },
                    depends_on=("analyze",),
                    estimated_cost=0.0,
                )
            )

            steps.append(
                PlanStep(
                    step_id="generate",
                    step_type=StepType.GENERATE.value,
                    description="Generate the final answer.",
                    parameters={
                        "query": query,
                        "grounded": True,
                    },
                    depends_on=("retrieve",),
                    estimated_cost=0.0,
                )
            )

        return steps

