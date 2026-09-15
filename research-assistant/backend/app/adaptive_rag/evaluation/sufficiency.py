from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SufficiencyResult:
    """
    Determines whether retrieved evidence is sufficient to continue
    toward answer generation.
    """

    sufficient: bool
    score: float
    reason: str


def calculate_sufficiency(
    *,
    quality_score: float,
    coverage_score: float,
    confidence_score: float,
    result_count: int,
    minimum_results: int = 1,
    quality_threshold: float = 0.65,
    coverage_threshold: float = 0.55,
    confidence_threshold: float = 0.60,
) -> SufficiencyResult:
    """
    Determine whether retrieval produced enough useful evidence.

    The decision intentionally requires both:
        - enough evidence
        - adequate evidence quality
        - adequate query coverage

    This prevents a high-scoring single document from automatically being
    treated as sufficient for a complex query.
    """
    if result_count < minimum_results:
        return SufficiencyResult(
            sufficient=False,
            score=0.0,
            reason="insufficient_result_count",
        )

    quality = max(0.0, min(1.0, quality_score))
    coverage = max(0.0, min(1.0, coverage_score))
    confidence = max(0.0, min(1.0, confidence_score))

    score = (
        0.45 * quality
        + 0.35 * coverage
        + 0.20 * confidence
    )

    sufficient = (
        quality >= quality_threshold
        and coverage >= coverage_threshold
        and confidence >= confidence_threshold
    )

    if sufficient:
        reason = "evidence_sufficient"
    elif coverage < coverage_threshold:
        reason = "insufficient_query_coverage"
    elif confidence < confidence_threshold:
        reason = "low_retrieval_confidence"
    else:
        reason = "low_evidence_quality"

    return SufficiencyResult(
        sufficient=sufficient,
        score=round(score, 6),
        reason=reason,
    )