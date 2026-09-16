from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SectionType(str, Enum):
    """Canonical research-paper section types."""

    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    BACKGROUND = "background"
    RELATED_WORK = "related_work"
    METHODS = "methods"
    METHODOLOGY = "methodology"
    MATERIALS = "materials"
    EXPERIMENTS = "experiments"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    LIMITATIONS = "limitations"
    FUTURE_WORK = "future_work"
    REFERENCES = "references"
    ACKNOWLEDGMENTS = "acknowledgments"
    APPENDIX = "appendix"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Section:
    """
    Normalized document section.
    """

    title: str
    section_type: SectionType
    level: int = 1
    number: Optional[str] = None

    @property
    def canonical_name(self) -> str:
        """Return the canonical section name."""
        return self.section_type.value


class SectionNormalizer:
    """
    Identifies and normalizes common academic-paper sections.
    """

    _PATTERNS: dict[SectionType, tuple[str, ...]] = {
        SectionType.ABSTRACT: (
            r"abstract",
            r"summary",
        ),
        SectionType.INTRODUCTION: (
            r"introduction",
            r"intro",
        ),
        SectionType.BACKGROUND: (
            r"background",
            r"preliminaries",
        ),
        SectionType.RELATED_WORK: (
            r"related\s+work",
            r"literature\s+review",
            r"related\s+studies",
        ),
        SectionType.METHODS: (
            r"methods?",
            r"methodology",
            r"approach",
        ),
        SectionType.METHODOLOGY: (
            r"methodology",
        ),
        SectionType.MATERIALS: (
            r"materials?\s+and\s+methods?",
            r"materials",
        ),
        SectionType.EXPERIMENTS: (
            r"experiments?",
            r"experimental\s+setup",
            r"evaluation",
        ),
        SectionType.RESULTS: (
            r"results?",
            r"findings?",
        ),
        SectionType.DISCUSSION: (
            r"discussion",
            r"analysis\s+and\s+discussion",
        ),
        SectionType.CONCLUSION: (
            r"conclusions?",
            r"concluding\s+remarks",
        ),
        SectionType.LIMITATIONS: (
            r"limitations?",
        ),
        SectionType.FUTURE_WORK: (
            r"future\s+work",
            r"future\s+directions?",
        ),
        SectionType.REFERENCES: (
            r"references?",
            r"bibliography",
        ),
        SectionType.ACKNOWLEDGMENTS: (
            r"acknowledg(e)?ments?",
            r"acknowledgements?",
        ),
        SectionType.APPENDIX: (
            r"appendix",
            r"appendices",
        ),
    }

    _NUMBER_PATTERN = re.compile(
        r"^\s*"
        r"(?P<number>"
        r"(?:"
        r"[IVXLCDM]+"
        r"|"
        r"\d+(?:\.\d+)*"
        r"|"
        r"[A-Z]"
        r")"
        r")"
        r"[\s.)\-:]+"
        r"(?P<title>.+?)"
        r"\s*$",
        re.IGNORECASE,
    )

    def normalize(
        self,
        title: str,
        *,
        level: int = 1,
    ) -> Section:
        """
        Normalize a raw section heading.

        Examples:

            "1. Introduction"
            "I. INTRODUCTION"
            "INTRODUCTION"

        all become an Introduction section.
        """

        cleaned = self.clean_title(title)

        number: Optional[str] = None
        section_title = cleaned

        match = self._NUMBER_PATTERN.match(cleaned)

        if match:
            number = match.group("number")
            section_title = match.group("title").strip()

        section_type = self.identify(section_title)

        return Section(
            title=section_title,
            section_type=section_type,
            level=level,
            number=number,
        )

    def identify(self, title: str) -> SectionType:
        """
        Identify the canonical section type from a heading.
        """

        normalized = self._normalize_for_matching(title)

        for section_type, patterns in self._PATTERNS.items():
            for pattern in patterns:
                if re.fullmatch(pattern, normalized, flags=re.IGNORECASE):
                    return section_type

        return SectionType.OTHER

    @staticmethod
    def clean_title(title: str) -> str:
        """
        Clean whitespace and common heading artifacts.
        """

        value = title.strip()

        value = re.sub(r"\s+", " ", value)

        value = value.strip(" \t\r\n.:;-")

        return value

    @staticmethod
    def _normalize_for_matching(title: str) -> str:
        """
        Normalize text used for section matching.
        """

        value = SectionNormalizer.clean_title(title)

        value = value.lower()

        value = re.sub(r"\s+", " ", value)

        return value


def normalize_section_title(
    title: str,
    *,
    level: int = 1,
) -> Section:
    """
    Convenience function for section normalization.
    """

    return SectionNormalizer().normalize(
        title,
        level=level,
    )