from __future__ import annotations

"""
Tracing primitives for Adaptive RAG.

This module provides vendor-neutral tracing.

A trace represents one complete user request.

A span represents one operation inside that request.

Example:

    Trace
      |
      +-- query_analysis
      |
      +-- planning
      |
      +-- retrieval
      |     |
      |     +-- dense_search
      |     +-- bm25_search
      |
      +-- evidence_evaluation
      |
      +-- generation
"""

from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Iterator, AsyncIterator, Optional
import uuid

from .events import (
    EventEmitter,
    EventSeverity,
    EventType,
    ObservabilityEvent,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Span:
    """Represents one operation inside a trace."""

    name: str
    trace_id: str

    span_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    parent_span_id: Optional[str] = None

    start_time: datetime = field(default_factory=_now)
    end_time: Optional[datetime] = None

    duration_ms: Optional[float] = None

    attributes: dict[str, Any] = field(default_factory=dict)

    status: str = "running"

    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def finish(
        self,
        *,
        success: bool = True,
        error: Optional[BaseException] = None,
    ) -> None:
        """Finish the span."""

        if self.end_time is not None:
            return

        self.end_time = _now()

        if self.duration_ms is None:
            self.duration_ms = (
                self.end_time - self.start_time
            ).total_seconds() * 1000.0

        self.status = "ok" if success else "error"

        if error is not None:
            self.error_type = type(error).__name__
            self.error_message = str(error)

    def set_attribute(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.attributes[key] = value

    def set_attributes(
        self,
        values: dict[str, Any],
    ) -> None:
        self.attributes.update(values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": (
                self.end_time.isoformat()
                if self.end_time
                else None
            ),
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


class Trace:
    """
    Complete execution trace for one request.

    The trace owns all spans created during the request.
    """

    def __init__(
        self,
        *,
        trace_id: Optional[str] = None,
        emitter: Optional[EventEmitter] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.trace_id = trace_id or str(uuid.uuid4())

        self.emitter = emitter

        self.metadata = dict(metadata or {})

        self.start_time = _now()
        self.end_time: Optional[datetime] = None

        self.duration_ms: Optional[float] = None

        self.status = "running"

        self.spans: list[Span] = []

        self.error: Optional[BaseException] = None

    def start_span(
        self,
        name: str,
        *,
        parent_span_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Span:
        """
        Create and register a span.
        """

        span = Span(
            name=name,
            trace_id=self.trace_id,
            parent_span_id=parent_span_id,
            attributes=dict(attributes or {}),
        )

        self.spans.append(span)

        if self.emitter:
            self.emitter.emit(
                ObservabilityEvent.create(
                    EventType.COMPONENT_STARTED,
                    self.trace_id,
                    span_id=span.span_id,
                    parent_span_id=span.parent_span_id,
                    component=name,
                    operation=name,
                    data=span.attributes,
                )
            )

        return span

    def finish(
        self,
        *,
        success: bool = True,
        error: Optional[BaseException] = None,
    ) -> None:
        """Finish the complete trace."""

        if self.end_time is not None:
            return

        self.end_time = _now()

        self.duration_ms = (
            self.end_time - self.start_time
        ).total_seconds() * 1000.0

        self.status = "ok" if success else "error"

        self.error = error

        if self.emitter:
            self.emitter.emit(
                ObservabilityEvent.create(
                    (
                        EventType.REQUEST_COMPLETED
                        if success
                        else EventType.REQUEST_FAILED
                    ),
                    self.trace_id,
                    severity=(
                        EventSeverity.INFO
                        if success
                        else EventSeverity.ERROR
                    ),
                    data=self.metadata,
                    duration_ms=self.duration_ms,
                    success=success,
                    error=error,
                )
            )

    def get_span(
        self,
        span_id: str,
    ) -> Optional[Span]:
        for span in self.spans:
            if span.span_id == span_id:
                return span

        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": (
                self.end_time.isoformat()
                if self.end_time
                else None
            ),
            "duration_ms": self.duration_ms,
            "status": self.status,
            "metadata": self.metadata,
            "spans": [
                span.to_dict()
                for span in self.spans
            ],
        }


class Tracer:
    """
    Main tracing facade.

    Usage:

        tracer = Tracer()

        with tracer.trace("research_request") as trace:
            with tracer.span("retrieval"):
                ...
    """

    def __init__(
        self,
        emitter: Optional[EventEmitter] = None,
    ) -> None:
        self.emitter = emitter or EventEmitter()

    def start_trace(
        self,
        name: str = "request",
        *,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Trace:
        trace = Trace(
            emitter=self.emitter,
            metadata={
                "trace_name": name,
                **(metadata or {}),
            },
        )

        self.emitter.emit(
            ObservabilityEvent.create(
                EventType.REQUEST_STARTED,
                trace.trace_id,
                component="tracer",
                operation=name,
                data=trace.metadata,
            )
        )

        return trace

    @contextmanager
    def trace(
        self,
        name: str = "request",
        *,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Iterator[Trace]:

        trace = self.start_trace(
            name,
            metadata=metadata,
        )

        try:
            yield trace
        except Exception as exc:
            trace.finish(
                success=False,
                error=exc,
            )
            raise
        else:
            trace.finish(success=True)

    @contextmanager
    def span(
        self,
        name: str,
        *,
        trace: Trace,
        parent_span: Optional[Span] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Iterator[Span]:

        span = trace.start_span(
            name,
            parent_span_id=(
                parent_span.span_id
                if parent_span
                else None
            ),
            attributes=attributes,
        )

        try:
            yield span
        except Exception as exc:
            span.finish(
                success=False,
                error=exc,
            )

            if self.emitter:
                self.emitter.emit(
                    ObservabilityEvent.create(
                        EventType.ERROR,
                        trace.trace_id,
                        span_id=span.span_id,
                        component=name,
                        operation=name,
                        severity=EventSeverity.ERROR,
                        error=exc,
                    )
                )

            raise
        else:
            span.finish(success=True)

            if self.emitter:
                self.emitter.emit(
                    ObservabilityEvent.create(
                        EventType.COMPONENT_COMPLETED,
                        trace.trace_id,
                        span_id=span.span_id,
                        parent_span_id=span.parent_span_id,
                        component=name,
                        operation=name,
                        data=span.attributes,
                        duration_ms=span.duration_ms,
                        success=True,
                    )
                )

    @asynccontextmanager
    async def async_span(
        self,
        name: str,
        *,
        trace: Trace,
        parent_span: Optional[Span] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[Span]:

        span = trace.start_span(
            name,
            parent_span_id=(
                parent_span.span_id
                if parent_span
                else None
            ),
            attributes=attributes,
        )

        try:
            yield span
        except Exception as exc:
            span.finish(
                success=False,
                error=exc,
            )

            if self.emitter:
                self.emitter.emit(
                    ObservabilityEvent.create(
                        EventType.ERROR,
                        trace.trace_id,
                        span_id=span.span_id,
                        component=name,
                        operation=name,
                        severity=EventSeverity.ERROR,
                        error=exc,
                    )
                )

            raise
        else:
            span.finish(success=True)

            if self.emitter:
                self.emitter.emit(
                    ObservabilityEvent.create(
                        EventType.COMPONENT_COMPLETED,
                        trace.trace_id,
                        span_id=span.span_id,
                        parent_span_id=span.parent_span_id,
                        component=name,
                        operation=name,
                        data=span.attributes,
                        duration_ms=span.duration_ms,
                        success=True,
                    )
                )


def create_trace(
    *,
    emitter: Optional[EventEmitter] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Trace:
    """Convenience trace factory."""

    return Trace(
        emitter=emitter,
        metadata=metadata,
    )