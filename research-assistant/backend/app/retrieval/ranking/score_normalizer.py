"""
Utilities for normalizing reranker scores.
"""

from __future__ import annotations

from typing import Sequence

from app.retrieval.ranking.models import RankedChunk


class ScoreNormalizer:
    """
    Utility class for normalizing reranker scores.
    """

    @staticmethod
    def min_max(chunks: Sequence[RankedChunk]) -> list[RankedChunk]:
        """
        Normalize scores into the range [0, 1].
        """

        if not chunks:
            return list(chunks)

        scores = [chunk.rerank_score for chunk in chunks]

        minimum = min(scores)
        maximum = max(scores)

        if maximum == minimum:
            for chunk in chunks:
                chunk.normalized_score = 1.0
            return list(chunks)

        for chunk in chunks:
            chunk.normalized_score = (
                chunk.rerank_score - minimum
            ) / (maximum - minimum)

        return list(chunks)

    @staticmethod
    def z_score(chunks: Sequence[RankedChunk]) -> list[RankedChunk]:
        """
        Standardize scores using Z-score normalization.
        """

        if not chunks:
            return list(chunks)

        scores = [chunk.rerank_score for chunk in chunks]

        mean = sum(scores) / len(scores)

        variance = sum(
            (score - mean) ** 2
            for score in scores
        ) / len(scores)

        std = variance ** 0.5

        if std == 0:
            for chunk in chunks:
                chunk.normalized_score = 0.0
            return list(chunks)

        for chunk in chunks:
            chunk.normalized_score = (
                chunk.rerank_score - mean
            ) / std

        return list(chunks)

    @staticmethod
    def percentage(chunks: Sequence[RankedChunk]) -> list[RankedChunk]:
        """
        Normalize scores into the range [0, 100].
        """

        ScoreNormalizer.min_max(chunks)

        for chunk in chunks:
            chunk.normalized_score *= 100.0

        return list(chunks)