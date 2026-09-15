from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class QualityResult:
    """
    Aggregate evidence quality.

    Quality combines:
        relevance
        retrieval confidence
        coverage
        diversity
    """

    score: float
    relevance: float
    confidence: float
    coverage: float
    diversity: float


def _clamp(value: float) -> float:
    if not isfinite(value):
        return 0.0

    return max(0.0, min(1.0, value))


def calculate_quality(
    *,
    relevance: float,
    confidence: float,
    coverage: float,
    diversity: float,
) -> QualityResult:
    """
    Calculate a deterministic aggregate quality score.

    Weighting intentionally favors relevance because irrelevant evidence
    should not be compensated for simply by having many documents.
    """
    relevance = _clamp(relevance)
    confidence = _clamp(confidence)
    coverage = _clamp(coverage)
    diversity = _clamp(diversity)

    score = (
        0.40 * relevance
        + 0.25 * confidence
        + 0.25 * coverage
        + 0.10 * diversity
    )

    return QualityResult(
        score=round(_clamp(score), 6),
        relevance=round(relevance, 6),
        confidence=round(confidence, 6),
        coverage=round(coverage, 6),
        diversity=round(diversity, 6),
    )