from __future__ import annotations

import re
from dataclasses import dataclass


_TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True, slots=True)
class CoverageResult:
    """
    Measures how much of the query's information content is represented
    across retrieved evidence.
    """

    score: float
    covered_terms: int
    total_terms: int


def _tokens(text: str) -> set[str]:
    if not text:
        return set()

    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) > 1
    }


def calculate_coverage(
    query: str,
    documents: list[str],
) -> CoverageResult:
    """
    Calculate query-term coverage across all retrieved documents.

    Unlike relevance, coverage evaluates the complete evidence set rather
    than individual chunks.
    """
    query_terms = _tokens(query)

    if not query_terms:
        return CoverageResult(
            score=0.0,
            covered_terms=0,
            total_terms=0,
        )

    evidence_terms: set[str] = set()

    for document in documents:
        evidence_terms.update(_tokens(document))

    covered = query_terms & evidence_terms

    score = len(covered) / len(query_terms)

    return CoverageResult(
        score=round(max(0.0, min(1.0, score)), 6),
        covered_terms=len(covered),
        total_terms=len(query_terms),
    )