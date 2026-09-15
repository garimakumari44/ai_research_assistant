"""
Citation handling for the generation layer.

Responsibilities:
- Extract citation markers from generated answers.
- Validate citations against available evidence.
- Identify missing/invalid citations.
- Normalize citation formatting.
- Provide citation metadata for downstream verification.

The module does not perform retrieval and does not invent citations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .synthesizer import EvidenceItem


# Supported citation formats:
#
# [E1]
# [E2]
# [E10]
#
# Multiple citations:
#
# [E1][E2]
# [E1, E2]
# [E1, E2, E3]
#
_CITATION_PATTERN = re.compile(
    r"\[E\d+(?:\s*,\s*E\d+)*\]",
    re.IGNORECASE,
)


_SINGLE_CITATION_PATTERN = re.compile(
    r"E(\d+)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class Citation:
    """
    Represents a single citation reference.
    """

    evidence_id: str

    position: int

    raw_text: str


@dataclass(slots=True)
class CitationValidation:
    """
    Result of validating citations in a generated answer.
    """

    valid: bool

    citations: list[Citation] = field(
        default_factory=list
    )

    valid_ids: list[str] = field(
        default_factory=list
    )

    invalid_ids: list[str] = field(
        default_factory=list
    )

    missing_ids: list[str] = field(
        default_factory=list
    )

    duplicate_ids: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )


class CitationManager:
    """
    Citation extraction and validation utility.
    """

    @staticmethod
    def extract(
        answer: str,
    ) -> list[Citation]:
        """
        Extract citation markers from an answer.

        Example:

            "RAG combines retrieval and generation [E1][E2]."

        returns citations for E1 and E2.
        """

        citations: list[Citation] = []

        for match in _CITATION_PATTERN.finditer(answer):
            raw_text = match.group(0)

            ids = _SINGLE_CITATION_PATTERN.findall(
                raw_text
            )

            for evidence_number in ids:
                evidence_id = (
                    f"E{evidence_number}"
                )

                citations.append(
                    Citation(
                        evidence_id=evidence_id,
                        position=match.start(),
                        raw_text=raw_text,
                    )
                )

        return citations

    @staticmethod
    def normalize_id(
        evidence_id: str,
    ) -> str:
        """
        Normalize an evidence ID.

        Examples:

            e1  -> E1
            E01 -> E1
            E10 -> E10
        """

        value = evidence_id.strip().upper()

        match = re.fullmatch(
            r"E0*(\d+)",
            value,
        )

        if not match:
            return value

        return f"E{int(match.group(1))}"

    @classmethod
    def validate(
        cls,
        answer: str,
        evidence: Iterable[EvidenceItem],
        *,
        require_citations: bool = True,
    ) -> CitationValidation:
        """
        Validate citations against available evidence.
        """

        evidence_list = list(evidence)

        available_ids = {
            cls.normalize_id(item.id)
            for item in evidence_list
        }

        citations = cls.extract(answer)

        cited_ids = [
            cls.normalize_id(
                citation.evidence_id
            )
            for citation in citations
        ]

        unique_cited_ids = list(
            dict.fromkeys(cited_ids)
        )

        valid_ids = [
            evidence_id
            for evidence_id in unique_cited_ids
            if evidence_id in available_ids
        ]

        invalid_ids = [
            evidence_id
            for evidence_id in unique_cited_ids
            if evidence_id not in available_ids
        ]

        duplicate_ids = [
            evidence_id
            for evidence_id in unique_cited_ids
            if cited_ids.count(evidence_id) > 1
        ]

        missing_ids = [
            evidence_id
            for evidence_id in available_ids
            if evidence_id not in unique_cited_ids
        ]

        warnings: list[str] = []

        if invalid_ids:
            warnings.append(
                "The answer contains citations that do not "
                "correspond to available evidence."
            )

        if require_citations and not citations:
            warnings.append(
                "The generated answer contains no citations."
            )

        if duplicate_ids:
            warnings.append(
                "Some evidence items are cited multiple times."
            )

        is_valid = (
            not invalid_ids
            and (
                bool(citations)
                if require_citations
                else True
            )
        )

        return CitationValidation(
            valid=is_valid,
            citations=citations,
            valid_ids=valid_ids,
            invalid_ids=invalid_ids,
            missing_ids=missing_ids,
            duplicate_ids=list(
                dict.fromkeys(duplicate_ids)
            ),
            warnings=warnings,
        )

    @classmethod
    def normalize(
        cls,
        answer: str,
    ) -> str:
        """
        Normalize citation formatting.

        Examples:

            [e1]        -> [E1]
            [E1, e2]    -> [E1, E2]
        """

        def replace(match: re.Match[str]) -> str:
            raw = match.group(0)

            ids = _SINGLE_CITATION_PATTERN.findall(
                raw
            )

            normalized = [
                cls.normalize_id(
                    f"E{number}"
                )
                for number in ids
            ]

            return "[" + ", ".join(normalized) + "]"

        return _CITATION_PATTERN.sub(
            replace,
            answer,
        )

    @classmethod
    def remove_invalid(
        cls,
        answer: str,
        evidence: Iterable[EvidenceItem],
    ) -> str:
        """
        Remove citations that do not map to available evidence.

        This is intentionally conservative: only invalid citation
        markers are removed. No new citations are generated.
        """

        available_ids = {
            cls.normalize_id(item.id)
            for item in evidence
        }

        def replace(match: re.Match[str]) -> str:
            raw = match.group(0)

            ids = _SINGLE_CITATION_PATTERN.findall(
                raw
            )

            valid = [
                cls.normalize_id(
                    f"E{number}"
                )
                for number in ids
                if cls.normalize_id(
                    f"E{number}"
                )
                in available_ids
            ]

            if not valid:
                return ""

            return "[" + ", ".join(
                dict.fromkeys(valid)
            ) + "]"

        return _CITATION_PATTERN.sub(
            replace,
            answer,
        )

    @classmethod
    def build_evidence_index(
        cls,
        evidence: Sequence[EvidenceItem],
    ) -> dict[str, EvidenceItem]:
        """
        Build an index for fast citation resolution.
        """

        return {
            cls.normalize_id(item.id): item
            for item in evidence
        }

    @classmethod
    def cited_evidence(
        cls,
        answer: str,
        evidence: Sequence[EvidenceItem],
    ) -> list[EvidenceItem]:
        """
        Return evidence items actually cited by the answer.
        """

        index = cls.build_evidence_index(
            evidence
        )

        citations = cls.extract(answer)

        result: list[EvidenceItem] = []

        seen: set[str] = set()

        for citation in citations:
            evidence_id = cls.normalize_id(
                citation.evidence_id
            )

            if evidence_id in seen:
                continue

            item = index.get(evidence_id)

            if item is not None:
                result.append(item)
                seen.add(evidence_id)

        return result


def extract_citations(
    answer: str,
) -> list[Citation]:
    """
    Convenience wrapper around CitationManager.extract().
    """

    return CitationManager.extract(answer)


def validate_citations(
    answer: str,
    evidence: Iterable[EvidenceItem],
    *,
    require_citations: bool = True,
) -> CitationValidation:
    """
    Convenience wrapper around CitationManager.validate().
    """

    return CitationManager.validate(
        answer,
        evidence,
        require_citations=require_citations,
    )