from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ConfidenceBreakdown:
    """
    Detailed confidence calculation for retrieved evidence.

    All values are normalized to [0.0, 1.0].
    """

    score_strength: float
    score_consistency: float
    evidence_density: float
    confidence: float


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if not isfinite(value):
        return minimum

    return max(minimum, min(maximum, value))


def _normalize_score(score: float) -> float:
    """
    Normalize a retrieval score into [0, 1].

    Retrieval systems do not necessarily use the same score scale, so this
    function intentionally handles common bounded/unbounded cases defensively.

    Expected input:
        cosine-like similarity: [-1, 1]
        probability-like score: [0, 1]
        ranking score: arbitrary positive values
    """
    if not isfinite(score):
        return 0.0

    if 0.0 <= score <= 1.0:
        return score

    if -1.0 <= score < 0.0:
        return (score + 1.0) / 2.0

    # For scores > 1, use a saturating transform.
    return 1.0 - (1.0 / (1.0 + score))


def calculate_confidence(
    scores: Iterable[float],
    *,
    expected_evidence: int = 3,
) -> ConfidenceBreakdown:
    """
    Calculate confidence from retrieval evidence.

    Confidence considers:
        1. Absolute retrieval score strength.
        2. Consistency between retrieved results.
        3. Evidence density relative to expected evidence.

    This deliberately avoids an LLM so evaluation remains:
        deterministic
        cheap
        reproducible
        provider-independent
    """
    normalized = [
        _normalize_score(float(score))
        for score in scores
        if isfinite(float(score))
    ]

    if not normalized:
        return ConfidenceBreakdown(
            score_strength=0.0,
            score_consistency=0.0,
            evidence_density=0.0,
            confidence=0.0,
        )

    score_strength = sum(normalized) / len(normalized)

    if len(normalized) == 1:
        consistency = 1.0
    else:
        mean = score_strength
        variance = sum((score - mean) ** 2 for score in normalized) / len(
            normalized
        )
        stddev = variance**0.5

        consistency = _clamp(1.0 - stddev)

    expected = max(1, expected_evidence)
    evidence_density = _clamp(len(normalized) / expected)

    confidence = (
        0.50 * score_strength
        + 0.25 * consistency
        + 0.25 * evidence_density
    )

    return ConfidenceBreakdown(
        score_strength=round(score_strength, 6),
        score_consistency=round(consistency, 6),
        evidence_density=round(evidence_density, 6),
        confidence=round(_clamp(confidence), 6),
    )