from __future__ import annotations

import re
from typing import Any, Mapping
from uuid import UUID

from app.knowledge.chunking.base import (
    BaseChunker,
    Chunk,
    ChunkingResult,
)


class SemanticChunker(BaseChunker):
    """
    Sentence-aware chunking strategy.

    The implementation is intentionally lightweight and deterministic.

    It groups sentences until the configured token budget is reached,
    while attempting to preserve sentence boundaries.
    """

    strategy_name = "semantic"

    SENTENCE_PATTERN = re.compile(
        r"""
        (?<=[.!?])
        ["'”’)]*
        \s+
        |
        (?<=\n)
        """,
        re.VERBOSE,
    )

    def chunk(
        self,
        text: str,
        *,
        document_id: UUID | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ChunkingResult:

        normalized = self.normalize_text(text)

        if not normalized:
            return self.finalize(
                [],
                document_id=document_id,
                metadata=metadata,
            )

        sentences = self._split_sentences(normalized)

        chunks: list[Chunk] = []

        current_sentences: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)

            # A single sentence can be larger than the configured
            # chunk size. Split it further.
            if sentence_tokens > self.config.max_tokens:
                if current_sentences:
                    chunks.append(
                        self._create_chunk(
                            current_sentences,
                            len(chunks),
                            document_id,
                        )
                    )

                    current_sentences = []
                    current_tokens = 0

                long_chunks = self._split_large_sentence(
                    sentence,
                    document_id=document_id,
                    start_index=len(chunks),
                )

                chunks.extend(long_chunks)
                continue

            would_exceed = (
                current_tokens + sentence_tokens
                > self.config.max_tokens
            )

            if current_sentences and would_exceed:
                chunks.append(
                    self._create_chunk(
                        current_sentences,
                        len(chunks),
                        document_id,
                    )
                )

                overlap = self._build_overlap(current_sentences)

                current_sentences = overlap
                current_tokens = sum(
                    self.estimate_tokens(item)
                    for item in current_sentences
                )

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        if current_sentences:
            chunks.append(
                self._create_chunk(
                    current_sentences,
                    len(chunks),
                    document_id,
                )
            )

        chunks = self._merge_tiny_chunks(chunks)

        return self.finalize(
            chunks,
            document_id=document_id,
            metadata={
                **dict(metadata or {}),
                "sentence_count": len(sentences),
            },
        )

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences while preserving meaningful content.
        """

        paragraphs = re.split(r"\n\s*\n", text)

        sentences: list[str] = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if not paragraph:
                continue

            parts = self.SENTENCE_PATTERN.split(paragraph)

            for part in parts:
                cleaned = re.sub(r"\s+", " ", part).strip()

                if cleaned:
                    sentences.append(cleaned)

        return sentences

    def _create_chunk(
        self,
        sentences: list[str],
        index: int,
        document_id: UUID | str | None,
    ) -> Chunk:
        text = " ".join(sentences)

        return self.build_chunk(
            text,
            chunk_index=index,
            document_id=document_id,
            chunk_type="semantic",
            metadata={
                "sentence_count": len(sentences),
            },
        )

    def _build_overlap(
        self,
        sentences: list[str],
    ) -> list[str]:
        """
        Keep the last few sentences as overlap.
        """

        if self.config.overlap_tokens <= 0:
            return []

        overlap: list[str] = []
        tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = self.estimate_tokens(sentence)

            if (
                overlap
                and tokens + sentence_tokens
                > self.config.overlap_tokens
            ):
                break

            overlap.insert(0, sentence)
            tokens += sentence_tokens

            if tokens >= self.config.overlap_tokens:
                break

        return overlap

    def _split_large_sentence(
        self,
        sentence: str,
        *,
        document_id: UUID | str | None,
        start_index: int,
    ) -> list[Chunk]:
        """
        Split an oversized sentence using word boundaries.
        """

        words = sentence.split()

        chunks: list[Chunk] = []

        current_words: list[str] = []
        current_tokens = 0

        for word in words:
            word_tokens = self.estimate_tokens(word)

            if (
                current_words
                and current_tokens + word_tokens
                > self.config.max_tokens
            ):
                chunks.append(
                    self.build_chunk(
                        " ".join(current_words),
                        chunk_index=start_index + len(chunks),
                        document_id=document_id,
                        chunk_type="semantic_overflow",
                        metadata={
                            "source": "oversized_sentence",
                        },
                    )
                )

                current_words = []
                current_tokens = 0

            current_words.append(word)
            current_tokens += word_tokens

        if current_words:
            chunks.append(
                self.build_chunk(
                    " ".join(current_words),
                    chunk_index=start_index + len(chunks),
                    document_id=document_id,
                    chunk_type="semantic_overflow",
                    metadata={
                        "source": "oversized_sentence",
                    },
                )
            )

        return chunks

    def _merge_tiny_chunks(
        self,
        chunks: list[Chunk],
    ) -> list[Chunk]:
        """
        Merge very small trailing chunks into their predecessor.
        """

        if len(chunks) <= 1:
            return chunks

        result: list[Chunk] = []

        for chunk in chunks:
            if (
                result
                and chunk.token_count < self.config.min_tokens
            ):
                previous = result[-1]

                combined = f"{previous.text} {chunk.text}"

                if (
                    self.estimate_tokens(combined)
                    <= self.config.max_tokens
                ):
                    previous.text = combined
                    previous.token_count = self.estimate_tokens(combined)
                    previous.character_count = len(combined)

                    previous.metadata["merged_chunks"] = (
                        previous.metadata.get("merged_chunks", 0) + 1
                    )

                    continue

            result.append(chunk)

        return result