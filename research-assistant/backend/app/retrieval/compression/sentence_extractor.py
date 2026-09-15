from __future__ import annotations

from collections import Counter
from typing import List

from app.retrieval.compression.base import BaseCompressor
from app.retrieval.compression.models import (
    CompressionChunk,
    CompressionRequest,
    CompressionResult,
)
from app.retrieval.compression.utils import (
    estimate_token_count,
    normalize_whitespace,
    split_sentences,
)


class SentenceExtractor(BaseCompressor):
    """
    Extracts the most relevant sentences from each chunk.
    """

    def __init__(
        self,
        max_sentences: int = 3,
    ) -> None:
        self.max_sentences = max_sentences

    @property
    def name(self) -> str:
        return "sentence_extractor"

    def compress(
        self,
        request: CompressionRequest,
    ) -> CompressionResult:
        """
        Compress chunks by selecting the highest scoring sentences.
        """

        compressed_chunks: List[CompressionChunk] = []

        for chunk in request.chunks:

            sentences = split_sentences(chunk.text)

            if len(sentences) <= self.max_sentences:
                compressed_text = normalize_whitespace(chunk.text)
            else:
                ranked = sorted(
                    sentences,
                    key=self._sentence_score,
                    reverse=True,
                )

                selected = ranked[: self.max_sentences]

                # Preserve original order
                selected.sort(key=sentences.index)

                compressed_text = " ".join(selected)

            chunk.compressed_text = compressed_text
            chunk.token_count = estimate_token_count(compressed_text)

            compressed_chunks.append(chunk)

        total_tokens = sum(
            chunk.token_count
            for chunk in compressed_chunks
        )

        return CompressionResult(
            chunks=compressed_chunks,
            total_tokens=total_tokens,
            removed_duplicates=0,
            removed_for_budget=0,
            compression_ratio=(
                total_tokens
                / max(
                    sum(
                        estimate_token_count(c.text)
                        for c in request.chunks
                    ),
                    1,
                )
            ),
            metadata={
                "compressor": self.name,
                "max_sentences": self.max_sentences,
            },
        )

    @staticmethod
    def _sentence_score(
        sentence: str,
    ) -> float:
        """
        Simple importance score based on term frequency.
        """

        words = sentence.lower().split()

        if not words:
            return 0.0

        counts = Counter(words)

        score = sum(counts.values())

        score += len(words) * 0.1

        return score