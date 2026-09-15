from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence


class SourceType(str, Enum):
    """Supported retrieval source classes."""

    INTERNAL_VECTOR = "internal_vector"
    INTERNAL_KEYWORD = "internal_keyword"
    INTERNAL_HYBRID = "internal_hybrid"

    WEB = "web"
    ACADEMIC = "academic"
    DATABASE = "database"
    API = "api"


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """A source that may participate in retrieval."""

    source: SourceType
    priority: float = 0.5
    reliability: float = 0.5
    freshness: float = 0.5
    latency: float = 0.5
    coverage: float = 0.5
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "priority",
            "reliability",
            "freshness",
            "latency",
            "coverage",
        ):
            value = getattr(self, field_name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{field_name} must be between 0 and 1"
                )


@dataclass(frozen=True, slots=True)
class SourceSelection:
    """Result of source selection."""

    sources: tuple[SourceType, ...]
    scores: Mapping[SourceType, float]
    rationale: str


@dataclass(frozen=True, slots=True)
class SourceSelectionContext:
    """Signals controlling source selection."""

    requires_freshness: bool = False
    requires_academic_sources: bool = False
    requires_external_sources: bool = False
    domain_specificity: float = 0.0
    reliability_requirement: float = 0.5
    latency_sensitivity: float = 0.5
    diversity_requirement: float = 0.5
    max_sources: int = 3

    def __post_init__(self) -> None:
        if not 0.0 <= self.domain_specificity <= 1.0:
            raise ValueError("domain_specificity must be between 0 and 1")

        if not 0.0 <= self.reliability_requirement <= 1.0:
            raise ValueError(
                "reliability_requirement must be between 0 and 1"
            )

        if not 0.0 <= self.latency_sensitivity <= 1.0:
            raise ValueError(
                "latency_sensitivity must be between 0 and 1"
            )

        if not 0.0 <= self.diversity_requirement <= 1.0:
            raise ValueError(
                "diversity_requirement must be between 0 and 1"
            )

        if self.max_sources < 1:
            raise ValueError("max_sources must be >= 1")


class SourceSelector:
    """
    Selects retrieval sources based on query requirements.

    The selector does not execute retrieval.
    """

    def __init__(
        self,
        candidates: Optional[Sequence[SourceCandidate]] = None,
    ) -> None:
        self._candidates = tuple(
            candidates
            or (
                SourceCandidate(
                    source=SourceType.INTERNAL_HYBRID,
                    priority=0.90,
                    reliability=0.90,
                    freshness=0.60,
                    latency=0.85,
                    coverage=0.90,
                ),
                SourceCandidate(
                    source=SourceType.INTERNAL_VECTOR,
                    priority=0.80,
                    reliability=0.85,
                    freshness=0.55,
                    latency=0.90,
                    coverage=0.85,
                ),
                SourceCandidate(
                    source=SourceType.INTERNAL_KEYWORD,
                    priority=0.75,
                    reliability=0.85,
                    freshness=0.55,
                    latency=0.95,
                    coverage=0.75,
                ),
                SourceCandidate(
                    source=SourceType.ACADEMIC,
                    priority=0.80,
                    reliability=0.95,
                    freshness=0.65,
                    latency=0.55,
                    coverage=0.80,
                ),
                SourceCandidate(
                    source=SourceType.WEB,
                    priority=0.70,
                    reliability=0.60,
                    freshness=0.95,
                    latency=0.60,
                    coverage=0.95,
                ),
                SourceCandidate(
                    source=SourceType.DATABASE,
                    priority=0.75,
                    reliability=0.90,
                    freshness=0.90,
                    latency=0.75,
                    coverage=0.80,
                ),
                SourceCandidate(
                    source=SourceType.API,
                    priority=0.70,
                    reliability=0.85,
                    freshness=0.90,
                    latency=0.70,
                    coverage=0.70,
                ),
            )
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _score_candidate(
        self,
        candidate: SourceCandidate,
        context: SourceSelectionContext,
    ) -> float:
        score = (
            candidate.priority * 0.20
            + candidate.reliability * 0.25
            + candidate.coverage * 0.20
            + candidate.freshness * 0.15
            + candidate.latency * 0.20
        )

        if context.requires_freshness:
            score += candidate.freshness * 0.25

        if context.requires_academic_sources:
            if candidate.source == SourceType.ACADEMIC:
                score += 0.40
            else:
                score -= 0.15

        if context.requires_external_sources:
            internal_sources = {
                SourceType.INTERNAL_VECTOR,
                SourceType.INTERNAL_KEYWORD,
                SourceType.INTERNAL_HYBRID,
            }

            if candidate.source in internal_sources:
                score -= 0.20
            else:
                score += 0.20

        # High reliability requirements penalize unreliable sources.
        if (
            candidate.reliability
            < context.reliability_requirement
        ):
            score -= 0.25

        # Latency-sensitive queries favor fast sources.
        score += (
            candidate.latency
            * context.latency_sensitivity
            * 0.20
        )

        # Domain-specific queries favor high coverage/reliability.
        score += (
            candidate.coverage
            * context.domain_specificity
            * 0.15
        )

        return self._clamp(score)

    def select(
        self,
        context: SourceSelectionContext,
    ) -> SourceSelection:
        """Select and rank the best available sources."""

        enabled = [
            candidate
            for candidate in self._candidates
            if candidate.enabled
        ]

        if not enabled:
            raise RuntimeError(
                "No retrieval sources are currently enabled."
            )

        ranked = sorted(
            (
                (
                    candidate,
                    self._score_candidate(candidate, context),
                )
                for candidate in enabled
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        selected: list[SourceType] = []
        scores: dict[SourceType, float] = {}

        for candidate, score in ranked:
            if len(selected) >= context.max_sources:
                break

            selected.append(candidate.source)
            scores[candidate.source] = score

        if not selected:
            raise RuntimeError(
                "Source selection produced no usable sources."
            )

        if context.diversity_requirement > 0.6:
            selected = self._ensure_diversity(
                selected,
                ranked,
                context.max_sources,
            )

        return SourceSelection(
            sources=tuple(selected),
            scores=scores,
            rationale=self._build_rationale(
                selected,
                context,
            ),
        )

    @staticmethod
    def _ensure_diversity(
        selected: list[SourceType],
        ranked: list[tuple[SourceCandidate, float]],
        max_sources: int,
    ) -> list[SourceType]:
        """
        Prefer multiple source classes when diversity is important.
        """

        if len(selected) >= max_sources:
            return selected

        existing = set(selected)

        for candidate, _score in ranked:
            if candidate.source in existing:
                continue

            selected.append(candidate.source)
            existing.add(candidate.source)

            if len(selected) >= max_sources:
                break

        return selected

    @staticmethod
    def _build_rationale(
        selected: Sequence[SourceType],
        context: SourceSelectionContext,
    ) -> str:
        reasons: list[str] = []

        if context.requires_freshness:
            reasons.append("freshness requirement")

        if context.requires_academic_sources:
            reasons.append("academic-source requirement")

        if context.requires_external_sources:
            reasons.append("external-source requirement")

        if context.diversity_requirement > 0.6:
            reasons.append("source diversity")

        if not reasons:
            reasons.append("balanced reliability, coverage and latency")

        source_names = ", ".join(source.value for source in selected)

        return (
            f"Selected sources [{source_names}] based on "
            + ", ".join(reasons)
            + "."
        )

    def available_sources(self) -> tuple[SourceType, ...]:
        """Return currently enabled source types."""

        return tuple(
            candidate.source
            for candidate in self._candidates
            if candidate.enabled
        )