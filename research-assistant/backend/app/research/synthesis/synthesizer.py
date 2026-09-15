
from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, Optional

from app.research.models import (
    Evidence,
    ResearchSection,
)


class ResearchSynthesizer:
    """
    Deterministically combines validated evidence into structured
    research sections.

    Responsibilities
    ----------------
    - Filter invalid evidence.
    - Preserve evidence claims without inventing information.
    - Remove duplicate evidence.
    - Group evidence by topic.
    - Generate deterministic section content.
    - Preserve evidence IDs for traceability.

    This component does NOT call an LLM.

    LLM-powered interpretation, summarization, thesis generation,
    and reasoning should happen in ResearchSummarizer or the
    appropriate research agent.
    """

    DEFAULT_SECTION_TITLE = "Research Findings"

    def __init__(
        self,
        default_section_title: str = DEFAULT_SECTION_TITLE,
    ) -> None:
        """
        Initialize the synthesizer.

        Parameters
        ----------
        default_section_title:
            Title used when evidence does not contain an explicit topic.
        """

        self.default_section_title = (
            default_section_title.strip()
            if default_section_title
            else self.DEFAULT_SECTION_TITLE
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def synthesize(
        self,
        evidence_items: list[Evidence],
    ) -> list[ResearchSection]:
        """
        Generate structured research sections from evidence.

        The operation is deterministic:

            Evidence
                ↓
            Validate
                ↓
            Deduplicate
                ↓
            Group
                ↓
            Generate content
                ↓
            ResearchSection

        No new factual claims are introduced.
        """

        if not evidence_items:
            return []

        valid_evidence = self.filter_valid_evidence(
            evidence_items
        )

        if not valid_evidence:
            return []

        deduplicated_evidence = self.deduplicate_evidence(
            valid_evidence
        )

        if not deduplicated_evidence:
            return []

        grouped = self.group_evidence(
            deduplicated_evidence
        )

        sections: list[ResearchSection] = []

        for topic, evidence_group in grouped.items():

            if not evidence_group:
                continue

            content = self.generate_content(
                evidence_group
            )

            if not content:
                continue

            section = self._build_section(
                title=topic,
                evidence_group=evidence_group,
                content=content,
            )

            sections.append(section)

        return sections

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def filter_valid_evidence(
        self,
        evidence_items: Iterable[Evidence],
    ) -> list[Evidence]:
        """
        Filter evidence items that cannot contribute to a section.

        Evidence is considered usable when it contains a non-empty claim.

        The original Evidence objects are preserved.
        """

        valid: list[Evidence] = []

        for evidence in evidence_items:

            if evidence is None:
                continue

            claim = self._get_value(
                evidence,
                "claim",
            )

            if claim is None:
                continue

            if not isinstance(claim, str):
                claim = str(claim)

            if not claim.strip():
                continue

            valid.append(evidence)

        return valid

    # ========================================================================
    # DEDUPLICATION
    # ========================================================================

    def deduplicate_evidence(
        self,
        evidence_items: list[Evidence],
    ) -> list[Evidence]:
        """
        Remove duplicate evidence while preserving input order.

        Deduplication prefers evidence IDs when available.

        If an ID is not available, the normalized claim is used.
        """

        seen_ids: set[str] = set()
        seen_claims: set[str] = set()

        result: list[Evidence] = []

        for evidence in evidence_items:

            evidence_id = self._get_value(
                evidence,
                "id",
            )

            claim = self._get_value(
                evidence,
                "claim",
            )

            normalized_claim = (
                self.normalize_claim(
                    str(claim)
                )
                if claim is not None
                else ""
            )

            # ------------------------------------------------------------
            # Prefer stable evidence ID.
            # ------------------------------------------------------------

            if evidence_id is not None:

                key = str(evidence_id).strip()

                if key:

                    if key in seen_ids:
                        continue

                    seen_ids.add(key)

                    result.append(evidence)

                    continue

            # ------------------------------------------------------------
            # Fall back to normalized claim.
            # ------------------------------------------------------------

            if normalized_claim:

                if normalized_claim in seen_claims:
                    continue

                seen_claims.add(
                    normalized_claim
                )

            result.append(evidence)

        return result

    @staticmethod
    def normalize_claim(
        claim: str,
    ) -> str:
        """
        Normalize a claim for deterministic duplicate detection.

        This does not alter the actual claim stored in the final report.
        """

        return " ".join(
            claim.strip().lower().split()
        )

    # ========================================================================
    # EVIDENCE GROUPING
    # ========================================================================

    def group_evidence(
        self,
        evidence_items: list[Evidence],
    ) -> dict[str, list[Evidence]]:
        """
        Group evidence into research topics.

        If Evidence contains a topic/category/section field, that value
        is used.

        Otherwise evidence is placed into the default section.

        Group ordering follows the first occurrence of each topic.
        """

        groups: OrderedDict[
            str,
            list[Evidence]
        ] = OrderedDict()

        for evidence in evidence_items:

            topic = self.extract_topic(
                evidence
            )

            if not topic:
                topic = self.default_section_title

            if topic not in groups:
                groups[topic] = []

            groups[topic].append(
                evidence
            )

        return dict(groups)

    def extract_topic(
        self,
        evidence: Evidence,
    ) -> Optional[str]:
        """
        Extract a topic from an Evidence object when available.

        Supported fields:

        - topic
        - category
        - section
        - research_topic
        - type

        If none exist, None is returned.
        """

        topic_fields = (
            "topic",
            "category",
            "section",
            "research_topic",
            "type",
        )

        for field_name in topic_fields:

            value = self._get_value(
                evidence,
                field_name,
            )

            if value is None:
                continue

            if not isinstance(value, str):
                value = str(value)

            value = value.strip()

            if value:
                return value

        return None

    # ========================================================================
    # CONTENT GENERATION
    # ========================================================================

    def generate_content(
        self,
        evidence_group: list[Evidence],
    ) -> str:
        """
        Create deterministic content from evidence claims.

        Claims are preserved as supplied and joined into a readable
        paragraph.

        No interpretation, inference, or new information is added.
        """

        if not evidence_group:
            return ""

        statements: list[str] = []

        for evidence in evidence_group:

            claim = self._get_value(
                evidence,
                "claim",
            )

            if claim is None:
                continue

            if not isinstance(claim, str):
                claim = str(claim)

            claim = claim.strip()

            if not claim:
                continue

            statements.append(
                claim
            )

        return self.join_statements(
            statements
        )

    @staticmethod
    def join_statements(
        statements: list[str],
    ) -> str:
        """
        Join evidence statements without modifying their factual content.
        """

        if not statements:
            return ""

        return " ".join(
            statement.strip()
            for statement in statements
            if statement and statement.strip()
        )

    # ========================================================================
    # SECTION CREATION
    # ========================================================================

    def _build_section(
        self,
        *,
        title: str,
        evidence_group: list[Evidence],
        content: str,
    ) -> ResearchSection:
        """
        Construct a ResearchSection while keeping model construction
        centralized.
        """

        evidence_ids = self.extract_evidence_ids(
            evidence_group
        )

        return ResearchSection(
            title=title,
            content=content,
            evidence_ids=evidence_ids,
        )

    def extract_evidence_ids(
        self,
        evidence_group: list[Evidence],
    ) -> list[str]:
        """
        Extract evidence IDs while preserving evidence order.

        Evidence without an ID is ignored because ResearchSection evidence_ids
        should only contain traceable identifiers.
        """

        evidence_ids: list[str] = []

        for evidence in evidence_group:

            evidence_id = self._get_value(
                evidence,
                "id",
            )

            if evidence_id is None:
                continue

            evidence_id = str(
                evidence_id
            ).strip()

            if not evidence_id:
                continue

            if evidence_id in evidence_ids:
                continue

            evidence_ids.append(
                evidence_id
            )

        return evidence_ids

    # ========================================================================
    # SECTION UTILITIES
    # ========================================================================

    def synthesize_single_section(
        self,
        evidence_items: list[Evidence],
        *,
        title: Optional[str] = None,
    ) -> Optional[ResearchSection]:
        """
        Create one section containing all supplied evidence.

        Useful when the caller explicitly wants a single section regardless
        of evidence topics.
        """

        valid_evidence = self.filter_valid_evidence(
            evidence_items
        )

        if not valid_evidence:
            return None

        deduplicated = self.deduplicate_evidence(
            valid_evidence
        )

        if not deduplicated:
            return None

        content = self.generate_content(
            deduplicated
        )

        if not content:
            return None

        return self._build_section(
            title=(
                title.strip()
                if title and title.strip()
                else self.default_section_title
            ),
            evidence_group=deduplicated,
            content=content,
        )

    def count_evidence(
        self,
        evidence_items: list[Evidence],
    ) -> int:
        """
        Return the number of usable evidence items.
        """

        return len(
            self.filter_valid_evidence(
                evidence_items
            )
        )

    def count_sections(
        self,
        sections: list[ResearchSection],
    ) -> int:
        """
        Return the number of generated research sections.
        """

        if not sections:
            return 0

        return len(sections)

    # ========================================================================
    # MODEL HELPERS
    # ========================================================================

    @staticmethod
    def _get_value(
        obj: Any,
        field_name: str,
    ) -> Any:
        """
        Safely read a field from:

        - Pydantic models
        - dataclasses
        - normal Python objects
        - dictionaries
        """

        if obj is None:
            return None

        if isinstance(obj, dict):
            return obj.get(field_name)

        return getattr(
            obj,
            field_name,
            None,
        )


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================


_default_synthesizer: Optional[
    ResearchSynthesizer
] = None


def get_research_synthesizer() -> ResearchSynthesizer:
    """
    Return the default ResearchSynthesizer instance.
    """

    global _default_synthesizer

    if _default_synthesizer is None:
        _default_synthesizer = ResearchSynthesizer()

    return _default_synthesizer


def synthesize_research(
    evidence_items: list[Evidence],
) -> list[ResearchSection]:
    """
    Convenience function for synthesizing evidence.
    """

    synthesizer = get_research_synthesizer()

    return synthesizer.synthesize(
        evidence_items
    )

