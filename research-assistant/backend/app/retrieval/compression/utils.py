from __future__ import annotations

import math
import re
from typing import Iterable, List

from app.retrieval.compression.models import CompressionChunk


_WORD_PATTERN = re.compile(r"\w+")
_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


def estimate_token_count(text: str) -> int:
    """
    Rough token estimate.

    A simple approximation is 1 token ≈ 0.75 words,
    or approximately words / 0.75.
    """

    if not text:
        return 0

    words = len(_WORD_PATTERN.findall(text))

    return max(1, math.ceil(words / 0.75))


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    """

    if not text.strip():
        return []

    return [
        sentence.strip()
        for sentence in _SENTENCE_PATTERN.split(text)
        if sentence.strip()
    ]


def normalize_whitespace(text: str) -> str:
    """
    Remove repeated whitespace.
    """

    return " ".join(text.split())


def truncate_text(
    text: str,
    max_tokens: int,
) -> str:
    """
    Truncate text to approximately the given token budget.
    """

    if estimate_token_count(text) <= max_tokens:
        return text

    words = text.split()

    estimated_words = max(1, int(max_tokens * 0.75))

    return " ".join(words[:estimated_words])


def total_token_count(
    chunks: Iterable[CompressionChunk],
) -> int:
    """
    Total estimated tokens across all chunks.
    """

    return sum(chunk.token_count for chunk in chunks)


def sort_by_score(
    chunks: List[CompressionChunk],
    descending: bool = True,
) -> List[CompressionChunk]:
    """
    Sort chunks by retrieval/reranker score.
    """

    return sorted(
        chunks,
        key=lambda chunk: chunk.score,
        reverse=descending,
    )


def unique_texts(
    chunks: List[CompressionChunk],
) -> List[CompressionChunk]:
    """
    Remove exact duplicate texts.
    """

    seen = set()
    unique = []

    for chunk in chunks:
        normalized = normalize_whitespace(chunk.text.lower())

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(chunk)

    return unique