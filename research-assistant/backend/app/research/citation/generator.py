
from __future__ import annotations

import logging
from typing import Iterable
from uuid import uuid4

from app.research.models import (
    Citation,
    Evidence,
    ResearchSource,
)

logger = logging.getLogger(__name__)


class CitationGenerator:
    """
    Generates citations from research sources.

    Responsibilities:
        - create stable citation records
        - preserve source identifiers
        - format bibliography entries
        - generate citations only for evidence-backed sources

    This implementation provides a deterministic basic citation format.
    """

    def generate(
        self,
        sources: Iterable[ResearchSource],
    ) -> list[Citation]:
        """
        Generate citations for unique sources.
        """

        if sources is None:
            return []

        citations: list[Citation] = []
        seen_source_ids: set[str] = set()

        for source in sources:
            if source is None:
                continue

            source_id = getattr(
                source,
                "id",
                None,
            )

            if not source_id:
                logger.warning(
                    "Skipping source without identifier"
                )
                continue

            source_id = str(source_id)

            if source_id in seen_source_ids:
                continue

            seen_source_ids.add(source_id)

            try:
                citation = Citation(
                    id=str(uuid4()),
                    source_id=source_id,
                    title=self._safe_title(source),
                    authors=self._safe_authors(source),
                    year=self.extract_year(source),
                    citation_text=self.format_basic(source),
                    url=self._safe_url(source),
                )
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Unable to generate citation",
                    extra={
                        "source_id": source_id,
                        "error": str(exc),
                    },
                )
                continue

            citations.append(citation)

        return citations

    def generate_from_evidence(
        self,
        evidence: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> list[Citation]:
        """
        Generate citations only for sources referenced by evidence.
        """

        if evidence is None or sources is None:
            return []

        source_ids = {
            str(item.source_id)
            for item in evidence
            if getattr(item, "source_id", None)
        }

        if not source_ids:
            return []

        used_sources = [
            source
            for source in sources
            if getattr(source, "id", None)
            and str(source.id) in source_ids
        ]

        return self.generate(
            used_sources
        )

    def extract_year(
        self,
        source: ResearchSource,
    ) -> int | None:
        """
        Extract a valid publication year from source metadata.
        """

        metadata = getattr(
            source,
            "metadata",
            {},
        )

        if not isinstance(metadata, dict):
            try:
                metadata = dict(metadata)
            except (TypeError, ValueError):
                metadata = {}

        value = metadata.get("year")

        if value is None:
            value = metadata.get(
                "publication_year"
            )

        if value is None:
            return None

        try:
            year = int(value)

            if 1 <= year <= 9999:
                return year

        except (TypeError, ValueError):
            pass

        return None

    def format_basic(
        self,
        source: ResearchSource,
    ) -> str:
        """
        Produce a deterministic basic bibliography entry.

        Example:

            Smith, Jane, Doe, John. A Research Paper. 2025.
        """

        authors = self._safe_authors(source)
        title = self._safe_title(source)
        year = self.extract_year(source)

        author_text = (
            ", ".join(authors)
            if authors
            else "Unknown author"
        )

        year_text = (
            str(year)
            if year is not None
            else "n.d."
        )

        citation = (
            f"{author_text}. "
            f"{title}. "
            f"{year_text}."
        )

        url = self._safe_url(source)

        if url:
            citation = f"{citation} {url}"

        return citation

    @staticmethod
    def _safe_title(
        source: ResearchSource,
    ) -> str:
        title = str(
            getattr(
                source,
                "title",
                "",
            )
            or ""
        ).strip()

        return title or "Untitled source"

    @staticmethod
    def _safe_authors(
        source: ResearchSource,
    ) -> list[str]:
        authors = getattr(
            source,
            "authors",
            [],
        )

        if authors is None:
            return []

        if isinstance(authors, str):
            return (
                [authors.strip()]
                if authors.strip()
                else []
            )

        try:
            return [
                str(author).strip()
                for author in authors
                if str(author).strip()
            ]
        except TypeError:
            return []

    @staticmethod
    def _safe_url(
        source: ResearchSource,
    ) -> str | None:
        url = getattr(
            source,
            "url",
            None,
        )

        if url is None:
            return None

        value = str(url).strip()

        return value or None

