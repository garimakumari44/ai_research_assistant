from __future__ import annotations

"""
Decision observability for Adaptive RAG.

Adaptive RAG is fundamentally a decision-making system.

Examples:

- Which retrieval strategy?
- How many documents?
- Dense vs BM25 vs hybrid?
- Should retrieval continue?
- Is evidence sufficient?
- Should the query be rewritten?
- Should another iteration happen?
- Which LLM/model should be used?

This module records those decisions in a consistent structure.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from .events import (
    EventEmitter,
    EventSeverity,
    EventType,
    ObservabilityEvent,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Decision:
    """
    Represents one Adaptive RAG decision.
    """

    decision_type: str
    selected_option: Any

    trace_id: str

    decision_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    timestamp: datetime = field(
        default_factory=_utc_now
    )

    candidates: list[Any] = field(default_factory=list)

    scores: dict[str, float] = field(default_factory=dict)

    confidence: Optional[float] = None

    rationale: Optional[str] = None

    constraints: dict[str, Any] = field(default_factory=dict)

    context: dict[str, Any] = field(default_factory=dict)

    reversible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "selected_option": self.selected_option,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "candidates": self.candidates,
            "scores": self.scores,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "constraints": self.constraints,
            "context": self.context,
            "reversible": self.reversible,
        }


class DecisionRecorder:
    """
    Records Adaptive RAG decisions.

    This is intentionally separate from the actual planner/router.

    The planner makes the decision.

    DecisionRecorder observes and records it.
    """

    def __init__(
        self,
        emitter: Optional[EventEmitter] = None,
    ) -> None:
        self.emitter = emitter or EventEmitter()

        self._decisions: list[Decision] = []

    def record(
        self,
        *,
        trace_id: str,
        decision_type: str,
        selected_option: Any,
        candidates: Optional[list[Any]] = None,
        scores: Optional[dict[str, float]] = None,
        confidence: Optional[float] = None,
        rationale: Optional[str] = None,
        constraints: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        reversible: bool = True,
    ) -> Decision:
        """
        Record a decision and emit an event.
        """

        decision = Decision(
            trace_id=trace_id,
            decision_type=decision_type,
            selected_option=selected_option,
            candidates=list(candidates or []),
            scores=dict(scores or {}),
            confidence=confidence,
            rationale=rationale,
            constraints=dict(constraints or {}),
            context=dict(context or {}),
            reversible=reversible,
        )

        self._decisions.append(decision)

        event_type = self._event_type_for(
            decision_type
        )

        self.emitter.emit(
            ObservabilityEvent.create(
                event_type,
                trace_id,
                severity=EventSeverity.INFO,
                component="decision_engine",
                operation=decision_type,
                data=decision.to_dict(),
                success=True,
            )
        )

        return decision

    def _event_type_for(
        self,
        decision_type: str,
    ) -> EventType:

        normalized = decision_type.lower()

        if "strategy" in normalized:
            return EventType.STRATEGY_SELECTED

        if "route" in normalized:
            return EventType.ROUTE_SELECTED

        if "plan" in normalized:
            return EventType.PLAN_CREATED

        if "budget" in normalized:
            return EventType.BUDGET_CHECKED

        return EventType.COMPONENT_COMPLETED

    def get_decisions(
        self,
        *,
        trace_id: Optional[str] = None,
        decision_type: Optional[str] = None,
    ) -> list[Decision]:

        decisions = self._decisions

        if trace_id is not None:
            decisions = [
                decision
                for decision in decisions
                if decision.trace_id == trace_id
            ]

        if decision_type is not None:
            decisions = [
                decision
                for decision in decisions
                if decision.decision_type
                == decision_type
            ]

        return list(decisions)

    def get_last_decision(
        self,
        *,
        trace_id: str,
        decision_type: Optional[str] = None,
    ) -> Optional[Decision]:

        decisions = self.get_decisions(
            trace_id=trace_id,
            decision_type=decision_type,
        )

        if not decisions:
            return None

        return decisions[-1]

    def count(
        self,
        *,
        trace_id: Optional[str] = None,
    ) -> int:

        return len(
            self.get_decisions(
                trace_id=trace_id
            )
        )

    def clear(self) -> None:
        self._decisions.clear()


class DecisionContext:
    """
    Helper for recording repeated decisions against one trace.

    Example:

        context = DecisionContext(
            trace_id=trace.trace_id,
            recorder=recorder,
        )

        context.record(
            "retrieval_strategy",
            "hybrid",
            confidence=0.92,
        )
    """

    def __init__(
        self,
        *,
        trace_id: str,
        recorder: Optional[DecisionRecorder] = None,
    ) -> None:

        self.trace_id = trace_id

        self.recorder = recorder or DecisionRecorder()

    def record(
        self,
        decision_type: str,
        selected_option: Any,
        *,
        candidates: Optional[list[Any]] = None,
        scores: Optional[dict[str, float]] = None,
        confidence: Optional[float] = None,
        rationale: Optional[str] = None,
        constraints: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        reversible: bool = True,
    ) -> Decision:

        return self.recorder.record(
            trace_id=self.trace_id,
            decision_type=decision_type,
            selected_option=selected_option,
            candidates=candidates,
            scores=scores,
            confidence=confidence,
            rationale=rationale,
            constraints=constraints,
            context=context,
            reversible=reversible,
        )