from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations


_TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True, slots=True)
class DiversityResult:
    """
    Diversity of retrieved evidence.

    High diversity means retrieved chunks are not merely duplicates or
    near-duplicates of one another.
    """

    score: float
    unique_documents: int
    total_documents: int
    duplicate_ratio: float


def _tokens(text: str) -> set[str]:
    if not text:
        return set()

    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) > 1
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0

    union = left | right

    if not union:
        return 0.0

    return len(left & right) / len(union)


def calculate_diversity(
    documents: list[str],
    *,
    duplicate_threshold: float = 0.90,
) -> DiversityResult:
    """
    Calculate evidence diversity using token-set similarity.

    A pair is considered a duplicate when Jaccard similarity exceeds
    duplicate_threshold.

    This is intentionally deterministic and database-independent.
    """
    if not documents:
        return DiversityResult(
            score=0.0,
            unique_documents=0,
            total_documents=0,
            duplicate_ratio=0.0,
        )

    token_sets = [_tokens(document) for document in documents]

    duplicate_pairs = 0
    total_pairs = 0

    for left, right in combinations(token_sets, 2):
        total_pairs += 1

        if _jaccard(left, right) >= duplicate_threshold:
            duplicate_pairs += 1

    duplicate_ratio = (
        duplicate_pairs / total_pairs
        if total_pairs
        else 0.0
    )

    unique_documents = len(documents)

    score = max(0.0, min(1.0, 1.0 - duplicate_ratio))

    return DiversityResult(
        score=round(score, 6),
        unique_documents=unique_documents,
        total_documents=len(documents),
        duplicate_ratio=round(duplicate_ratio, 6),
    )