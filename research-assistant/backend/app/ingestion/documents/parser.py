from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.ingestion.documents.extractor import (
    DocumentExtraction,
    DocumentPage,
)


@dataclass(slots=True)
class ParsedSection:
    """
    A logical section extracted from a document.

    This is an ingestion-layer object.

    The database Section model should be created later by
    DocumentService/SectionRepository.
    """

    title: str
    content: str
    level: int
    order: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None


@dataclass(slots=True)
class DocumentParseResult:
    """
    Result of parsing a document.
    """

    sections: list[ParsedSection]
    full_text: str
    page_count: int


class DocumentParser:
    """
    Convert extracted PDF text into logical sections.

    This is intentionally heuristic.

    Research papers commonly contain headings such as:

        Abstract
        1 Introduction
        2 Related Work
        3 Method
        4 Experiments
        Conclusion
        References

    More advanced structure detection can be added later.
    """

    SECTION_PATTERN = re.compile(
        r"""
        ^
        (?:
            (?P<number>
                \d+(?:\.\d+)*
            )
            [\.\:\-\s]+
        )?
        (?P<title>
            [A-Z][A-Za-z0-9][A-Za-z0-9\s,\-:&'()/]{1,150}
        )
        $
        """,
        re.VERBOSE,
    )

    KNOWN_HEADINGS = {
        "abstract",
        "introduction",
        "background",
        "related work",
        "related works",
        "method",
        "methods",
        "methodology",
        "approach",
        "model",
        "experiments",
        "experiment",
        "evaluation",
        "results",
        "discussion",
        "limitations",
        "conclusion",
        "conclusions",
        "future work",
        "references",
        "acknowledgements",
        "acknowledgments",
    }

    def parse(
        self,
        extraction: DocumentExtraction,
    ) -> DocumentParseResult:
        """
        Parse extracted document content into sections.
        """

        if extraction is None:
            raise ValueError("Document extraction is required.")

        sections = self._parse_pages(
            extraction.pages
        )

        # If no structural headings are detected, preserve the
        # entire document as one section.
        if not sections and extraction.text.strip():
            sections = [
                ParsedSection(
                    title="Document",
                    content=extraction.text.strip(),
                    level=1,
                    order=1,
                    page_start=1 if extraction.page_count else None,
                    page_end=(
                        extraction.page_count
                        if extraction.page_count
                        else None
                    ),
                )
            ]

        return DocumentParseResult(
            sections=sections,
            full_text=extraction.text,
            page_count=extraction.page_count,
        )

    def _parse_pages(
        self,
        pages: list[DocumentPage],
    ) -> list[ParsedSection]:
        sections: list[ParsedSection] = []

        current_title: Optional[str] = None
        current_content: list[str] = []
        current_level = 1
        current_order = 0
        current_page_start: Optional[int] = None
        current_page_end: Optional[int] = None

        for page in pages:
            lines = page.text.splitlines()

            for line in lines:
                normalized = line.strip()

                if not normalized:
                    continue

                heading = self._detect_heading(
                    normalized
                )

                if heading is not None:
                    # Flush previous section.
                    if current_title is not None:
                        sections.append(
                            ParsedSection(
                                title=current_title,
                                content="\n".join(
                                    current_content
                                ).strip(),
                                level=current_level,
                                order=current_order,
                                page_start=current_page_start,
                                page_end=current_page_end,
                            )
                        )

                    current_order += 1

                    current_title = heading["title"]
                    current_level = heading["level"]
                    current_content = []
                    current_page_start = page.page_number
                    current_page_end = page.page_number

                else:
                    if current_title is None:
                        # Content appearing before the first heading.
                        current_title = "Document"
                        current_level = 1
                        current_order += 1
                        current_page_start = page.page_number

                    current_content.append(normalized)

                    current_page_end = page.page_number

        # Flush final section.
        if current_title is not None:
            sections.append(
                ParsedSection(
                    title=current_title,
                    content="\n".join(
                        current_content
                    ).strip(),
                    level=current_level,
                    order=current_order,
                    page_start=current_page_start,
                    page_end=current_page_end,
                )
            )

        # Remove empty sections.
        return [
            section
            for section in sections
            if section.content.strip()
        ]

    def _detect_heading(
        self,
        line: str,
    ) -> Optional[dict[str, object]]:
        """
        Detect whether a line looks like a section heading.
        """

        if len(line) > 180:
            return None

        normalized = line.strip()

        # Known academic headings.
        if normalized.lower() in self.KNOWN_HEADINGS:
            return {
                "title": normalized,
                "level": 1,
            }

        match = self.SECTION_PATTERN.match(normalized)

        if not match:
            return None

        title = match.group("title")

        if not title:
            return None

        title = title.strip()

        # Avoid interpreting ordinary sentences as headings.
        if title.endswith((".", "?", "!")):
            return None

        number = match.group("number")

        if number:
            level = number.count(".") + 1
        else:
            level = 1

        # Avoid very long sentence-like lines.
        if len(title.split()) > 15:
            return None

        # Headings are generally title-like rather than fully
        # lowercase prose.
        if title.islower():
            return None

        return {
            "title": normalized,
            "level": level,
        }