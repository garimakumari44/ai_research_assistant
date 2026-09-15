from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence, Any

from .answer_checker import AnswerCheckResult
from .gap_detector import GapDetectionResult, GapSeverity
from .hallucination_detector import HallucinationResult
from .retrieval_checker import RetrievalCheckResult


class CriticSeverity(str, Enum):
    PASS = "pass"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CriticResult:
    """
    Final structured quality judgment.
    """

    accepted: bool
    severity: CriticSeverity
    score: float
    reasons: tuple[str, ...]
    recommendations: tuple[str, ...]
    requires_retrieval: bool
    requires_regeneration: bool
    metadata: dict[str, Any]


class Critic:
    """
    Aggregates retrieval, gap, answer, and hallucination checks.

    The critic does not perform retrieval or generation. It only determines
    what the orchestration layer should do next.
    """

    def __init__(
        self,
        *,
        acceptance_threshold: float = 0.72,
        hallucination_weight: float = 0.40,
        retrieval_weight: float = 0.20,
        answer_weight: float = 0.25,
        coverage_weight: float = 0.15,
    ) -> None:
        weights = (
            hallucination_weight,
            retrieval_weight,
            answer_weight,
            coverage_weight,
        )

        if any(weight < 0 for weight in weights):
            raise ValueError("Critic weights cannot be negative.")

        total = sum(weights)

        if total <= 0:
            raise ValueError("At least one critic weight must be positive.")

        self.hallucination_weight = hallucination_weight / total
        self.retrieval_weight = retrieval_weight / total
        self.answer_weight = answer_weight / total
        self.coverage_weight = coverage_weight / total

        self.acceptance_threshold = acceptance_threshold

    def evaluate(
        self,
        *,
        retrieval: RetrievalCheckResult,
        gaps: GapDetectionResult,
        answer: AnswerCheckResult,
        hallucination: HallucinationResult,
    ) -> CriticResult:
        hallucination_quality = (
            1.0 - hallucination.hallucination_score
        )

        retrieval_quality = (
            0.60 * retrieval.relevance_score
            + 0.40 * retrieval.diversity_score
        )

        answer_quality = (
            0.55 * answer.relevance_score
            + 0.45 * answer.completeness_score
        )

        coverage_quality = gaps.coverage_score

        score = (
            hallucination_quality * self.hallucination_weight
            + retrieval_quality * self.retrieval_weight
            + answer_quality * self.answer_weight
            + coverage_quality * self.coverage_weight
        )

        reasons: list[str] = []
        recommendations: list[str] = []

        if hallucination.has_hallucinations:
            reasons.append(
                "Potential hallucinated or unsupported claims were detected."
            )
            recommendations.append(
                "Regenerate the answer using only verified evidence."
            )

        if not retrieval.sufficient:
            reasons.extend(retrieval.reasons)
            recommendations.append(
                "Perform another retrieval pass."
            )

        if gaps.has_gaps:
            for gap in gaps.gaps:
                reasons.append(gap.description)

            recommendations.append(
                "Retrieve evidence targeting the identified information gaps."
            )

        if not answer.acceptable:
            reasons.extend(answer.reasons)
            recommendations.append(
                "Regenerate or revise the answer."
            )

        critical_gap = any(
            gap.severity == GapSeverity.CRITICAL
            for gap in gaps.gaps
        )

        accepted = (
            score >= self.acceptance_threshold
            and not hallucination.has_hallucinations
            and answer.acceptable
            and not critical_gap
        )

        if accepted:
            severity = CriticSeverity.PASS
            reasons.append("Answer passed self-reflection.")
        elif critical_gap:
            severity = CriticSeverity.CRITICAL
        elif hallucination.has_hallucinations:
            severity = CriticSeverity.HIGH
        elif score < 0.45:
            severity = CriticSeverity.HIGH
        elif score < 0.60:
            severity = CriticSeverity.MEDIUM
        else:
            severity = CriticSeverity.LOW

        requires_retrieval = (
            not retrieval.sufficient
            or gaps.has_gaps
        )

        requires_regeneration = (
            hallucination.has_hallucinations
            or not answer.acceptable
        )

        return CriticResult(
            accepted=accepted,
            severity=severity,
            score=max(0.0, min(1.0, score)),
            reasons=tuple(dict.fromkeys(reasons)),
            recommendations=tuple(dict.fromkeys(recommendations)),
            requires_retrieval=requires_retrieval,
            requires_regeneration=requires_regeneration,
            metadata={
                "hallucination_quality": hallucination_quality,
                "retrieval_quality": retrieval_quality,
                "answer_quality": answer_quality,
                "coverage_quality": coverage_quality,
            },
        )
