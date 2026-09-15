from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence


@dataclass
class ProcessingResult:
    """
    Result produced by the document processing pipeline.

    The pipeline operates on document content and produces
    normalized text and chunks that can later be embedded
    and indexed.
    """

    text: str
    chunks: list[str]
    metadata: dict[str, Any]


class DocumentProcessingPipeline:
    """
    Basic document content processing pipeline.

    Flow:

        Document
            ↓
        extract
            ↓
        clean
            ↓
        chunk
            ↓
        ProcessingResult

    The individual operations are injected so that the pipeline
    remains independent from specific extraction, cleaning, and
    chunking implementations.
    """

    def __init__(
        self,
        extractor: Callable[[Any], str] | None = None,
        cleaner: Callable[[str], str] | None = None,
        chunker: Callable[[str], Sequence[str]] | None = None,
    ) -> None:
        self.extractor = extractor or self._default_extract
        self.cleaner = cleaner or self._default_clean
        self.chunker = chunker or self._default_chunk

    def process(
        self,
        document: Any,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessingResult:
        """
        Process a document through extraction, cleaning,
        and chunking.
        """

        # 1. Extract
        text = self.extractor(document)

        if not isinstance(text, str):
            raise TypeError(
                "Document extractor must return a string."
            )

        # 2. Clean / normalize
        cleaned_text = self.cleaner(text)

        if not isinstance(cleaned_text, str):
            raise TypeError(
                "Document cleaner must return a string."
            )

        # 3. Chunk
        chunks = list(self.chunker(cleaned_text))

        return ProcessingResult(
            text=cleaned_text,
            chunks=chunks,
            metadata=metadata or {},
        )

    @staticmethod
    def _default_extract(document: Any) -> str:
        """
        Default extraction implementation.

        Supports common Document representations:

        - document.text
        - document.content
        - document.raw_text

        This is intentionally lightweight. Actual PDF/DOCX/OCR
        extraction should be provided through an extractor
        implementation later.
        """

        for attribute in (
            "text",
            "content",
            "raw_text",
        ):
            value = getattr(document, attribute, None)

            if isinstance(value, str) and value.strip():
                return value

        if isinstance(document, str):
            return document

        raise ValueError(
            "Unable to extract text from document. "
            "Provide an extractor or a document containing "
            "text, content, or raw_text."
        )

    @staticmethod
    def _default_clean(text: str) -> str:
        """
        Basic text normalization.

        More advanced cleaning can later be injected without
        changing the pipeline itself.
        """

        lines = (
            line.strip()
            for line in text.splitlines()
        )

        cleaned_lines = [
            line
            for line in lines
            if line
        ]

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def _default_chunk(
        text: str,
        chunk_size: int = 1000,
    ) -> list[str]:
        """
        Basic character-based chunking.

        This is a temporary default implementation.

        A production chunker should eventually support
        paragraph/sentence boundaries, overlap, headings,
        page information, and token-aware sizing.
        """

        if not text:
            return []

        return [
            text[index : index + chunk_size]
            for index in range(
                0,
                len(text),
                chunk_size,
            )
        ]