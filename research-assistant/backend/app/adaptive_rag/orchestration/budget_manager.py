
from __future__ import annotations

import logging
from dataclasses import dataclass
from time import monotonic
from typing import Optional

from .planner import ExecutionPlan, PlanStep
from .executor import ExecutionResult

logger = logging.getLogger(__name__)


class BudgetExceededError(RuntimeError):
    """Raised when an orchestration budget is exhausted."""


@dataclass(frozen=True, slots=True)
class BudgetConfig:
    """
    Hard limits for one orchestration request.

    A value of None means that resource has no explicit limit.
    """

    max_steps: Optional[int] = 12
    max_tokens: Optional[int] = 20_000
    max_cost: Optional[float] = 1.0
    max_latency_seconds: Optional[float] = 60.0
    max_iterations: Optional[int] = 3

    def validate(self) -> None:
        if self.max_steps is not None and self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")

        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")

        if self.max_cost is not None and self.max_cost < 0:
            raise ValueError("max_cost must be >= 0")

        if (
            self.max_latency_seconds is not None
            and self.max_latency_seconds <= 0
        ):
            raise ValueError(
                "max_latency_seconds must be > 0"
            )

        if (
            self.max_iterations is not None
            and self.max_iterations < 1
        ):
            raise ValueError("max_iterations must be >= 1")


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    """Immutable view of current budget consumption."""

    request_id: Optional[str]

    steps_used: int
    tokens_used: int
    cost_used: float

    elapsed_seconds: float

    config: BudgetConfig

    @property
    def steps_remaining(self) -> Optional[int]:
        if self.config.max_steps is None:
            return None

        return max(
            0,
            self.config.max_steps - self.steps_used,
        )

    @property
    def tokens_remaining(self) -> Optional[int]:
        if self.config.max_tokens is None:
            return None

        return max(
            0,
            self.config.max_tokens - self.tokens_used,
        )

    @property
    def cost_remaining(self) -> Optional[float]:
        if self.config.max_cost is None:
            return None

        return max(
            0.0,
            self.config.max_cost - self.cost_used,
        )

    @property
    def latency_remaining(self) -> Optional[float]:
        if self.config.max_latency_seconds is None:
            return None

        return max(
            0.0,
            self.config.max_latency_seconds
            - self.elapsed_seconds,
        )


class BudgetManager:
    """
    Central resource-budget enforcement for Adaptive RAG.

    BudgetManager is intentionally independent of a particular LLM,
    retriever, database, or provider.

    It tracks:

    - orchestration steps
    - tokens
    - estimated/actual cost
    - wall-clock execution time
    - request lifecycle

    The manager enforces HARD limits. It should therefore be consulted
    before every expensive orchestration step.
    """

    def __init__(
        self,
        config: Optional[BudgetConfig] = None,
    ) -> None:
        self._config = config or BudgetConfig()
        self._config.validate()

        self._request_id: Optional[str] = None

        self._steps_used = 0
        self._tokens_used = 0
        self._cost_used = 0.0

        self._started_at: Optional[float] = None
        self._active = False

    @property
    def config(self) -> BudgetConfig:
        return self._config

    def start_request(self, request_id: str) -> None:
        if not request_id:
            raise ValueError("request_id is required")

        if self._active:
            raise RuntimeError(
                "BudgetManager is already tracking a request"
            )

        self._request_id = request_id

        self._steps_used = 0
        self._tokens_used = 0
        self._cost_used = 0.0

        self._started_at = monotonic()
        self._active = True

    def finish_request(self) -> None:
        if not self._active:
            return

        self._check_latency()

        self._active = False

    def abort_request(self) -> None:
        self._active = False

    def reserve_plan(
        self,
        plan: ExecutionPlan,
    ) -> None:
        """
        Validate that a plan is potentially executable within budget.

        This does not consume budget.
        """

        if not self._active:
            raise RuntimeError(
                "No active request"
            )

        plan.validate()

        if (
            self._config.max_steps is not None
            and len(plan.steps) > self._config.max_steps
        ):
            raise BudgetExceededError(
                f"Plan requires {len(plan.steps)} steps, "
                f"but budget allows only "
                f"{self._config.max_steps}"
            )

        if (
            self._config.max_tokens is not None
            and plan.estimated_tokens > self._config.max_tokens
        ):
            raise BudgetExceededError(
                f"Plan estimates {plan.estimated_tokens} tokens, "
                f"but budget allows only "
                f"{self._config.max_tokens}"
            )

        if (
            self._config.max_cost is not None
            and plan.estimated_cost > self._config.max_cost
        ):
            raise BudgetExceededError(
                f"Plan estimates cost {plan.estimated_cost:.6f}, "
                f"but budget allows only "
                f"{self._config.max_cost:.6f}"
            )

        if (
            self._config.max_iterations is not None
            and plan.max_iterations > self._config.max_iterations
        ):
            raise BudgetExceededError(
                f"Plan requires {plan.max_iterations} iterations, "
                f"but budget allows only "
                f"{self._config.max_iterations}"
            )

    def check_before_step(
        self,
        step: PlanStep,
    ) -> None:
        """
        Check whether a step can start.
        """

        if not self._active:
            raise RuntimeError(
                "No active budget request"
            )

        self._check_latency()

        if (
            self._config.max_steps is not None
            and self._steps_used >= self._config.max_steps
        ):
            raise BudgetExceededError(
                "Maximum orchestration steps exceeded"
            )

        if (
            self._config.max_tokens is not None
            and self._tokens_used
            + step.estimated_tokens
            > self._config.max_tokens
        ):
            raise BudgetExceededError(
                f"Step '{step.step_id}' would exceed token budget"
            )

        if (
            self._config.max_cost is not None
            and self._cost_used
            + step.estimated_cost
            > self._config.max_cost
        ):
            raise BudgetExceededError(
                f"Step '{step.step_id}' would exceed cost budget"
            )

    def record_step(
        self,
        result: ExecutionResult,
    ) -> None:
        """
        Record actual consumption after a step completes.
        """

        if not self._active:
            raise RuntimeError(
                "No active budget request"
            )

        if result.tokens_used < 0:
            raise ValueError(
                "tokens_used cannot be negative"
            )

        if result.cost < 0:
            raise ValueError(
                "cost cannot be negative"
            )

        self._steps_used += 1
        self._tokens_used += result.tokens_used
        self._cost_used += result.cost

        self._check_hard_limits()
        self._check_latency()

    def snapshot(self) -> BudgetSnapshot:
        elapsed = 0.0

        if self._started_at is not None:
            elapsed = monotonic() - self._started_at

        return BudgetSnapshot(
            request_id=self._request_id,
            steps_used=self._steps_used,
            tokens_used=self._tokens_used,
            cost_used=self._cost_used,
            elapsed_seconds=elapsed,
            config=self._config,
        )

    def _check_hard_limits(self) -> None:
        if (
            self._config.max_steps is not None
            and self._steps_used > self._config.max_steps
        ):
            raise BudgetExceededError(
                "Maximum orchestration steps exceeded"
            )

        if (
            self._config.max_tokens is not None
            and self._tokens_used > self._config.max_tokens
        ):
            raise BudgetExceededError(
                "Maximum token budget exceeded"
            )

        if (
            self._config.max_cost is not None
            and self._cost_used > self._config.max_cost
        ):
            raise BudgetExceededError(
                "Maximum cost budget exceeded"
            )

    def _check_latency(self) -> None:
        if (
            self._config.max_latency_seconds is None
            or self._started_at is None
        ):
            return

        elapsed = monotonic() - self._started_at

        if elapsed > self._config.max_latency_seconds:
            raise BudgetExceededError(
                "Maximum orchestration latency exceeded"
            )

