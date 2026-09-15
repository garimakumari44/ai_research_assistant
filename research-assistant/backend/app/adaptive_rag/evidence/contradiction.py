from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

from .collector import EvidenceItem


@dataclass(frozen=True, slots=True)
class ContradictionPair:
    """
    Potentially contradictory evidence pair.

    This is a deterministic heuristic, not a semantic truth claim.
    """

    left_id: str
    right_id: str

    similarity: float
    contradiction_score: float


@dataclass(frozen=True, slots=True)
class ContradictionResult:
    """
    Aggregate contradiction assessment.
    """

    score: float

    contradiction_count: int
    checked_pairs: int

    pairs: tuple[ContradictionPair, ...]

    has_contradiction: bool


class ContradictionDetector:
    """
    Detects likely contradictions using lexical overlap and opposing
    assertion markers.

    Production systems should treat this as a signal for adaptive
    retrieval / deeper evaluation, not as proof that two sources disagree.
    """

    NEGATION_TERMS = frozenset(
        {
            "not",
            "no",
            "never",
            "none",
            "without",
            "cannot",
            "can't",
            "doesn't",
            "isn't",
            "wasn't",
            "won't",
            "false",
        }
    )

    POSITIVE_TERMS = frozenset(
        {
            "yes",
            "true",
            "does",
            "is",
            "was",
            "will",
            "can",
            "supports",
            "confirmed",
        }
    )

    def __init__(
        self,
        *,
        min_similarity: float = 0.35,
        contradiction_threshold: float = 0.65,
        max_pairs: int = 100,
    ) -> None:
        self.min_similarity = min_similarity
        self.contradiction_threshold = contradiction_threshold
        self.max_pairs = max_pairs

    def evaluate(
        self,
        evidence: Sequence[EvidenceItem],
    ) -> ContradictionResult:
        pairs: list[ContradictionPair] = []

        checked_pairs = 0

        for left, right in combinations(evidence, 2):
            if checked_pairs >= self.max_pairs:
                break

            checked_pairs += 1

            similarity = self._similarity(
                left.content,
                right.content,
            )

            if similarity < self.min_similarity:
                continue

            contradiction_score = (
                self._contradiction_score(
                    left.content,
                    right.content,
                )
            )

            if contradiction_score >= self.contradiction_threshold:
                pairs.append(
                    ContradictionPair(
                        left_id=left.evidence_id,
                        right_id=right.evidence_id,
                        similarity=similarity,
                        contradiction_score=contradiction_score,
                    )
                )

        contradiction_count = len(pairs)

        if not evidence:
            score = 0.0
        else:
            score = max(
                0.0,
                1.0
                - (
                    contradiction_count
                    / max(1, len(evidence))
                ),
            )

        return ContradictionResult(
            score=score,
            contradiction_count=contradiction_count,
            checked_pairs=checked_pairs,
            pairs=tuple(pairs),
            has_contradiction=bool(pairs),
        )

    def _contradiction_score(
        self,
        left: str,
        right: str,
    ) -> float:
        left_tokens = self._tokens(left)
        right_tokens = self._tokens(right)

        if not left_tokens or not right_tokens:
            return 0.0

        left_negated = bool(
            left_tokens & self.NEGATION_TERMS
        )

        right_negated = bool(
            right_tokens & self.NEGATION_TERMS
        )

        left_positive = bool(
            left_tokens & self.POSITIVE_TERMS
        )

        right_positive = bool(
            right_tokens & self.POSITIVE_TERMS
        )

        score = 0.0

        if left_negated != right_negated:
            score += 0.7

        if left_positive != right_positive:
            score += 0.2

        return min(1.0, score)

    def _similarity(
        self,
        left: str,
        right: str,
    ) -> float:
        left_tokens = self._tokens(left)
        right_tokens = self._tokens(right)

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = left_tokens & right_tokens
        union = left_tokens | right_tokens

        return len(intersection) / len(union)

    @staticmethod
    def _tokens(
        text: str,
    ) -> set[str]:
        return set(
            re.findall(
                r"\b[a-zA-Z0-9']+\b",
                text.lower(),
            )
        )