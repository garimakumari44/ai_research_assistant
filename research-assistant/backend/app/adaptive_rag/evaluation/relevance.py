from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite


_TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True, slots=True)
class RelevanceResult:
    """
    Relevance assessment for a single retrieved chunk.
    """

    score: float
    matched_terms: int
    query_terms: int


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()

    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) > 1
    }


def calculate_relevance(
    query: str,
    content: str,
) -> RelevanceResult:
    """
    Calculate lexical relevance between query and retrieved content.

    This is intentionally a lightweight deterministic signal.

    It should NOT replace semantic retrieval or reranking. It acts as an
    evaluation feature used by Adaptive RAG to determine whether retrieved
    evidence appears useful.
    """
    query_terms = _tokenize(query)
    content_terms = _tokenize(content)

    if not query_terms or not content_terms:
        return RelevanceResult(
            score=0.0,
            matched_terms=0,
            query_terms=len(query_terms),
        )

    matched = query_terms & content_terms

    score = len(matched) / len(query_terms)

    return RelevanceResult(
        score=round(max(0.0, min(1.0, score)), 6),
        matched_terms=len(matched),
        query_terms=len(query_terms),
    )


def calculate_batch_relevance(
    query: str,
    contents: Iterable[str],
) -> list[RelevanceResult]:
    """
    Evaluate multiple retrieved chunks against one query.
    """
    return [
        calculate_relevance(query, content)
        for content in contents
    ]