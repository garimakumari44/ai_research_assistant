from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(slots=True)
class DocumentPage:
    """
    Extracted content from one PDF page.
    """

    page_number: int
    text: str


@dataclass(slots=True)
class DocumentExtraction:
    """
    Result of PDF text extraction.
    """

    text: str
    pages: list[DocumentPage]
    page_count: int
    source_path: Path


class DocumentExtractor:
    """
    Extract textual content from PDF documents.

    This extractor expects PDFs with an existing text layer.

    OCR for scanned PDFs should be implemented as a separate
    extraction strategy later.
    """

    def __init__(
        self,
        *,
        min_text_length: int = 50,
    ) -> None:
        self.min_text_length = min_text_length

    def extract(
        self,
        file_path: str | Path,
    ) -> DocumentExtraction:
        """
        Extract text from a PDF.

        Raises:
            FileNotFoundError:
                File does not exist.

            ValueError:
                File is invalid/unreadable.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Document path is not a file: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Unsupported document format: {path.suffix}"
            )

        try:
            reader = PdfReader(str(path))
        except Exception as exc:
            raise ValueError(
                f"Unable to read PDF document: {path}"
            ) from exc

        pages: list[DocumentPage] = []
        text_parts: list[str] = []

        for index, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text = self._clean_text(text)

            page_result = DocumentPage(
                page_number=index + 1,
                text=text,
            )

            pages.append(page_result)

            if text:
                text_parts.append(text)

        full_text = "\n\n".join(text_parts)

        return DocumentExtraction(
            text=full_text,
            pages=pages,
            page_count=len(reader.pages),
            source_path=path,
        )

    def has_extractable_text(
        self,
        extraction: DocumentExtraction,
    ) -> bool:
        """
        Determine whether the PDF contains enough extracted text
        to be considered successfully text-extracted.
        """

        return (
            len(extraction.text.strip())
            >= self.min_text_length
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalize whitespace while preserving paragraph-like
        line boundaries.
        """

        lines: list[str] = []

        for line in text.splitlines():
            normalized = " ".join(line.split())

            if normalized:
                lines.append(normalized)

        # IMPORTANT:
        # No trailing comma here. A trailing comma would return
        # a tuple instead of a string.
        return "\n".join(lines)