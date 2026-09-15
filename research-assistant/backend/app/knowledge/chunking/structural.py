from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID

from app.knowledge.chunking.base import (
    BaseChunker,
    Chunk,
    ChunkingResult,
)


@dataclass(slots=True)
class StructuralBlock:
    """
    Represents one structural unit of a document.
    """

    text: str

    section_title: str | None = None

    section_level: int = 0

    block_type: str = "paragraph"


class StructuralChunker(BaseChunker):
    """
    Structure-aware chunker for research documents.

    The chunker attempts to preserve:

    - headings
    - sections
    - paragraphs
    - subsection boundaries

    It falls back to paragraph-based chunking when no headings
    can be detected.
    """

    strategy_name = "structural"

    HEADING_PATTERN = re.compile(
        r"""
        ^
        (?:
            (?:\d+(?:\.\d+)*)\s+
        )?
        (
            abstract
            |introduction
            |background
            |related\s+work
            |literature\s+review
            |method
            |methods
            |methodology
            |approach
            |model
            |experiments?
            |experimental\s+setup
            |results?
            |evaluation
            |discussion
            |analysis
            |conclusion
            |future\s+work
            |limitations?
            |references
        )
        \s*$
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    NUMBERED_HEADING_PATTERN = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+?)\s*$"
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

        blocks = self._parse_structure(normalized)

        chunks: list[Chunk] = []

        for block in blocks:
            block_chunks = self._chunk_block(
                block,
                document_id=document_id,
                start_index=len(chunks),
            )

            chunks.extend(block_chunks)

        return self.finalize(
            chunks,
            document_id=document_id,
            metadata={
                **dict(metadata or {}),
                "structural_blocks": len(blocks),
            },
        )

    def _parse_structure(
        self,
        text: str,
    ) -> list[StructuralBlock]:
        """
        Parse document into sections and paragraphs.
        """

        lines = text.splitlines()

        blocks: list[StructuralBlock] = []

        current_section: str | None = None
        current_level = 0

        paragraph_lines: list[str] = []

        def flush_paragraph() -> None:
            if not paragraph_lines:
                return

            paragraph = " ".join(
                line.strip()
                for line in paragraph_lines
                if line.strip()
            ).strip()

            if paragraph:
                blocks.append(
                    StructuralBlock(
                        text=paragraph,
                        section_title=current_section,
                        section_level=current_level,
                        block_type="paragraph",
                    )
                )

            paragraph_lines.clear()

        for line in lines:
            stripped = line.strip()

            if not stripped:
                flush_paragraph()
                continue

            heading = self._detect_heading(stripped)

            if heading is not None:
                flush_paragraph()

                current_section, current_level = heading

                blocks.append(
                    StructuralBlock(
                        text=current_section,
                        section_title=current_section,
                        section_level=current_level,
                        block_type="heading",
                    )
                )

                continue

            paragraph_lines.append(stripped)

        flush_paragraph()

        return blocks

    def _detect_heading(
        self,
        line: str,
    ) -> tuple[str, int] | None:
        """
        Detect common research-paper headings.
        """

        if len(line) > 120:
            return None

        match = self.HEADING_PATTERN.match(line)

        if match:
            title = match.group(1).strip()

            numbered = self.NUMBERED_HEADING_PATTERN.match(line)

            if numbered:
                number = numbered.group(1)
                level = number.count(".") + 1
            else:
                level = 1

            return title, level

        numbered = self.NUMBERED_HEADING_PATTERN.match(line)

        if numbered:
            number = numbered.group(1)
            title = numbered.group(2).strip()

            # Avoid treating normal sentences as headings.
            if len(title.split()) <= 12:
                level = number.count(".") + 1
                return title, level

        return None

    def _chunk_block(
        self,
        block: StructuralBlock,
        *,
        document_id: UUID | str | None,
        start_index: int,
    ) -> list[Chunk]:

        if block.block_type == "heading":
            return [
                self.build_chunk(
                    block.text,
                    chunk_index=start_index,
                    document_id=document_id,
                    chunk_type="heading",
                    metadata={
                        "section_title": block.section_title,
                        "section_level": block.section_level,
                    },
                )
            ]

        tokens = self.estimate_tokens(block.text)

        if tokens <= self.config.max_tokens:
            return [
                self.build_chunk(
                    block.text,
                    chunk_index=start_index,
                    document_id=document_id,
                    chunk_type="structural",
                    metadata={
                        "section_title": block.section_title,
                        "section_level": block.section_level,
                        "block_type": block.block_type,
                    },
                )
            ]

        return self._split_large_block(
            block,
            document_id=document_id,
            start_index=start_index,
        )

    def _split_large_block(
        self,
        block: StructuralBlock,
        *,
        document_id: UUID | str | None,
        start_index: int,
    ) -> list[Chunk]:
        """
        Split an oversized structural block while preserving
        its section metadata.
        """

        words = block.text.split()

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
                        chunk_type="structural_split",
                        metadata={
                            "section_title": block.section_title,
                            "section_level": block.section_level,
                            "block_type": block.block_type,
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
                    chunk_type="structural_split",
                    metadata={
                        "section_title": block.section_title,
                        "section_level": block.section_level,
                        "block_type": block.block_type,
                    },
                )
            )

        return chunks