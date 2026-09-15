from __future__ import annotations

"""
Observability events for the Adaptive RAG system.

This module defines the canonical event model used across the system.

Design goals:
- Strongly typed events
- JSON serializable payloads
- Correlation via trace_id / span_id
- No dependency on a specific observability vendor
- Safe handling of arbitrary metadata
- Support for synchronous and asynchronous consumers
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional
import json
import math
import uuid


class EventType(str, Enum):
    """Canonical Adaptive RAG observability events."""

    # Request lifecycle
    REQUEST_STARTED = "request.started"
    REQUEST_COMPLETED = "request.completed"
    REQUEST_FAILED = "request.failed"

    # Query lifecycle
    QUERY_ANALYZED = "query.analyzed"
    QUERY_REWRITTEN = "query.rewritten"
    QUERY_DECOMPOSED = "query.decomposed"

    # Planning
    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"

    # Routing
    STRATEGY_SELECTED = "strategy.selected"
    ROUTE_SELECTED = "route.selected"

    # Retrieval
    RETRIEVAL_STARTED = "retrieval.started"
    RETRIEVAL_COMPLETED = "retrieval.completed"
    RETRIEVAL_FAILED = "retrieval.failed"

    # Evidence
    EVIDENCE_COLLECTED = "evidence.collected"
    EVIDENCE_VALIDATED = "evidence.validated"
    CONTRADICTION_DETECTED = "evidence.contradiction_detected"
    CORROBORATION_DETECTED = "evidence.corroboration_detected"

    # Evaluation
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"

    # Reflection
    REFLECTION_STARTED = "reflection.started"
    REFLECTION_COMPLETED = "reflection.completed"
    GAP_DETECTED = "reflection.gap_detected"

    # Generation
    GENERATION_STARTED = "generation.started"
    GENERATION_COMPLETED = "generation.completed"
    GENERATION_FAILED = "generation.failed"

    # Budget
    BUDGET_CHECKED = "budget.checked"
    BUDGET_EXCEEDED = "budget.exceeded"

    # Diagnostics
    WARNING = "diagnostics.warning"
    ERROR = "diagnostics.error"

    # System
    COMPONENT_STARTED = "component.started"
    COMPONENT_COMPLETED = "component.completed"


class EventSeverity(str, Enum):
    """Severity used for event filtering and alerting."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
    """
    Convert arbitrary Python values into JSON-safe representations.

    Observability must never crash the application because a diagnostic
    value is not serializable.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    if hasattr(value, "model_dump"):
        try:
            return _json_safe(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "dict"):
        try:
            return _json_safe(value.dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return _json_safe(vars(value))
        except Exception:
            pass

    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


@dataclass(slots=True)
class ObservabilityEvent:
    """
    Canonical event emitted by the Adaptive RAG system.
    """

    event_type: EventType
    trace_id: str

    event_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    timestamp: datetime = field(default_factory=_utc_now)

    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    severity: EventSeverity = EventSeverity.INFO

    component: Optional[str] = None
    operation: Optional[str] = None

    message: Optional[str] = None

    data: dict[str, Any] = field(default_factory=dict)

    duration_ms: Optional[float] = None

    success: Optional[bool] = None

    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        self.data = dict(_json_safe(self.data) or {})

        if self.duration_ms is not None:
            try:
                self.duration_ms = float(self.duration_ms)

                if not math.isfinite(self.duration_ms):
                    self.duration_ms = None

            except (TypeError, ValueError):
                self.duration_ms = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary representation."""

        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "severity": self.severity.value,
            "component": self.component,
            "operation": self.operation,
            "message": self.message,
            "data": _json_safe(self.data),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }

    def to_json(self) -> str:
        """Serialize the event as JSON."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @classmethod
    def create(
        cls,
        event_type: EventType,
        trace_id: str,
        *,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        severity: EventSeverity = EventSeverity.INFO,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
        error: Optional[BaseException] = None,
    ) -> "ObservabilityEvent":
        """Convenience factory."""

        return cls(
            event_type=event_type,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=severity,
            component=component,
            operation=operation,
            message=message,
            data=dict(data or {}),
            duration_ms=duration_ms,
            success=success,
            error_type=(
                type(error).__name__
                if error is not None
                else None
            ),
            error_message=(
                str(error)
                if error is not None
                else None
            ),
        )


class EventEmitter:
    """
    Lightweight in-process event emitter.

    The emitter intentionally does not depend on logging, OpenTelemetry,
    Kafka, Redis, etc.

    Those integrations can subscribe later.

    Example:

        emitter = EventEmitter()

        emitter.emit(
            ObservabilityEvent.create(
                EventType.RETRIEVAL_COMPLETED,
                trace_id,
                data={"documents": 5},
            )
        )
    """

    def __init__(self) -> None:
        self._events: list[ObservabilityEvent] = []

    def emit(self, event: ObservabilityEvent) -> None:
        """Store an event."""

        self._events.append(event)

    def get_events(
        self,
        *,
        trace_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None,
    ) -> list[ObservabilityEvent]:
        """Return matching events."""

        events = self._events

        if trace_id is not None:
            events = [
                event
                for event in events
                if event.trace_id == trace_id
            ]

        if event_type is not None:
            events = [
                event
                for event in events
                if event.event_type == event_type
            ]

        if limit is not None:
            events = events[-limit:]

        return list(events)

    def clear(self) -> None:
        """Clear in-memory events."""

        self._events.clear()

    def count(self) -> int:
        return len(self._events)