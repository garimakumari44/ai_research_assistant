from __future__ import annotations

"""
Diagnostics and health information for Adaptive RAG.

Responsibilities:

- Capture warnings/errors
- Track component health
- Track performance metrics
- Detect repeated failures
- Provide trace-level diagnostics
- Produce a safe diagnostic snapshot

This module does NOT replace application logging.

Logging answers:
    "What happened?"

Diagnostics answer:
    "Is the system healthy and why?"
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from statistics import mean
from typing import Any, Optional
import traceback
import uuid

from .events import (
    EventEmitter,
    EventSeverity,
    EventType,
    ObservabilityEvent,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class DiagnosticIssue:
    """A diagnostic warning/error."""

    message: str

    severity: EventSeverity

    issue_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    timestamp: datetime = field(
        default_factory=_utc_now
    )

    trace_id: Optional[str] = None

    component: Optional[str] = None

    operation: Optional[str] = None

    error_type: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    stack_trace: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "component": self.component,
            "operation": self.operation,
            "error_type": self.error_type,
            "metadata": self.metadata,
            "stack_trace": self.stack_trace,
        }


@dataclass(slots=True)
class ComponentHealth:
    """Current health information for a component."""

    component: str

    status: HealthStatus = HealthStatus.UNKNOWN

    last_check: datetime = field(
        default_factory=_utc_now
    )

    total_operations: int = 0

    successful_operations: int = 0

    failed_operations: int = 0

    total_duration_ms: float = 0.0

    last_error: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if self.total_operations == 0:
            return 1.0

        return (
            self.successful_operations
            / self.total_operations
        )

    @property
    def average_duration_ms(self) -> float:
        if self.total_operations == 0:
            return 0.0

        return (
            self.total_duration_ms
            / self.total_operations
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": self.success_rate,
            "average_duration_ms": self.average_duration_ms,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }


class DiagnosticsManager:
    """
    Central diagnostics manager.

    Thread-safe integration can be added later if the application requires
    multi-threaded mutation. The current Adaptive RAG execution path is
    primarily request/task oriented.
    """

    def __init__(
        self,
        emitter: Optional[EventEmitter] = None,
        *,
        max_issues: int = 1000,
    ) -> None:

        self.emitter = emitter or EventEmitter()

        self.max_issues = max(
            1,
            int(max_issues),
        )

        self._issues: list[DiagnosticIssue] = []

        self._components: dict[
            str,
            ComponentHealth,
        ] = {}

    def register_component(
        self,
        component: str,
        *,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ComponentHealth:

        health = self._components.get(component)

        if health is None:
            health = ComponentHealth(
                component=component,
                status=HealthStatus.HEALTHY,
                metadata=dict(metadata or {}),
            )

            self._components[component] = health

        elif metadata:
            health.metadata.update(metadata)

        return health

    def record_operation(
        self,
        *,
        component: str,
        success: bool,
        duration_ms: Optional[float] = None,
        error: Optional[BaseException] = None,
        trace_id: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> ComponentHealth:

        health = self.register_component(component)

        health.last_check = _utc_now()

        health.total_operations += 1

        if success:
            health.successful_operations += 1
        else:
            health.failed_operations += 1

            if error is not None:
                health.last_error = str(error)

        if duration_ms is not None:
            try:
                health.total_duration_ms += max(
                    0.0,
                    float(duration_ms),
                )
            except (TypeError, ValueError):
                pass

        health.status = self._calculate_health(
            health
        )

        if not success and error is not None:
            self.record_error(
                error,
                trace_id=trace_id,
                component=component,
                operation=operation,
            )

        return health

    @staticmethod
    def _calculate_health(
        health: ComponentHealth,
    ) -> HealthStatus:

        if health.total_operations == 0:
            return HealthStatus.UNKNOWN

        failure_rate = (
            health.failed_operations
            / health.total_operations
        )

        if failure_rate >= 0.50:
            return HealthStatus.UNHEALTHY

        if failure_rate >= 0.10:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def record_warning(
        self,
        message: str,
        *,
        trace_id: Optional[str] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DiagnosticIssue:

        issue = DiagnosticIssue(
            message=message,
            severity=EventSeverity.WARNING,
            trace_id=trace_id,
            component=component,
            operation=operation,
            metadata=dict(metadata or {}),
        )

        self._add_issue(issue)

        self.emitter.emit(
            ObservabilityEvent.create(
                EventType.WARNING,
                trace_id or "system",
                severity=EventSeverity.WARNING,
                component=component,
                operation=operation,
                message=message,
                data=metadata or {},
            )
        )

        return issue

    def record_error(
        self,
        error: BaseException,
        *,
        trace_id: Optional[str] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        include_stack_trace: bool = False,
    ) -> DiagnosticIssue:

        stack = None

        if include_stack_trace:
            stack = traceback.format_exc()

        issue = DiagnosticIssue(
            message=str(error),
            severity=EventSeverity.ERROR,
            trace_id=trace_id,
            component=component,
            operation=operation,
            error_type=type(error).__name__,
            metadata=dict(metadata or {}),
            stack_trace=stack,
        )

        self._add_issue(issue)

        self.emitter.emit(
            ObservabilityEvent.create(
                EventType.ERROR,
                trace_id or "system",
                severity=EventSeverity.ERROR,
                component=component,
                operation=operation,
                message=str(error),
                data=metadata or {},
                success=False,
                error=error,
            )
        )

        return issue

    def _add_issue(
        self,
        issue: DiagnosticIssue,
    ) -> None:

        self._issues.append(issue)

        if len(self._issues) > self.max_issues:
            del self._issues[
                : len(self._issues) - self.max_issues
            ]

    def get_issues(
        self,
        *,
        trace_id: Optional[str] = None,
        component: Optional[str] = None,
        severity: Optional[EventSeverity] = None,
        limit: Optional[int] = None,
    ) -> list[DiagnosticIssue]:

        issues = self._issues

        if trace_id is not None:
            issues = [
                issue
                for issue in issues
                if issue.trace_id == trace_id
            ]

        if component is not None:
            issues = [
                issue
                for issue in issues
                if issue.component == component
            ]

        if severity is not None:
            issues = [
                issue
                for issue in issues
                if issue.severity == severity
            ]

        if limit is not None:
            issues = issues[-limit:]

        return list(issues)

    def get_component_health(
        self,
        component: Optional[str] = None,
    ) -> Any:

        if component is not None:
            return self._components.get(component)

        return {
            name: health
            for name, health
            in self._components.items()
        }

    def overall_status(self) -> HealthStatus:
        """Calculate system-wide health."""

        if not self._components:
            return HealthStatus.UNKNOWN

        statuses = [
            component.status
            for component
            in self._components.values()
        ]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY

        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        if all(
            status == HealthStatus.HEALTHY
            for status in statuses
        ):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def snapshot(self) -> dict[str, Any]:
        """
        Return a complete diagnostics snapshot.

        Suitable for an internal health/debug endpoint.
        """

        return {
            "timestamp": _utc_now().isoformat(),
            "status": self.overall_status().value,
            "components": {
                name: health.to_dict()
                for name, health
                in self._components.items()
            },
            "recent_issues": [
                issue.to_dict()
                for issue in self._issues[-100:]
            ],
        }

    def clear(self) -> None:
        self._issues.clear()
        self._components.clear()