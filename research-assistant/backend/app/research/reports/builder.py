
from __future__ import annotations

from typing import Iterable

from app.research.models import (
    ResearchReport,
    ResearchSection,
    Citation,
    Evidence,
    ResearchSource,
    ComparisonResult,
)


class ResearchReportBuilder:
    """
    Builds final research reports.

    Combines:

        - research sections
        - evidence
        - citations
        - sources
        - optional comparisons

    The builder does not perform research or LLM generation.
    """

    def build(
        self,
        title: str,
        summary: str,
        sections: Iterable[ResearchSection],
        citations: Iterable[Citation],
        evidence: Iterable[Evidence],
        sources: Iterable[ResearchSource],
        comparison: ComparisonResult | None = None,
    ) -> ResearchReport:
        """
        Create a validated research report.
        """

        normalized_title = self._required_text(
            title,
            "title",
        )

        normalized_summary = self._required_text(
            summary,
            "summary",
        )

        normalized_sections = list(
            sections or []
        )

        normalized_citations = list(
            citations or []
        )

        normalized_evidence = list(
            evidence or []
        )

        normalized_sources = list(
            sources or []
        )

        self._validate_references(
            normalized_sections,
            normalized_evidence,
            normalized_citations,
            normalized_sources,
        )

        return ResearchReport(
            title=normalized_title,
            summary=normalized_summary,
            sections=normalized_sections,
            citations=normalized_citations,
            evidence=normalized_evidence,
            sources=normalized_sources,
            comparison=comparison,
        )

    def build_markdown(
        self,
        report: ResearchReport,
    ) -> str:
        """
        Render a ResearchReport as readable Markdown.
        """

        lines: list[str] = []

        title = self._clean_text(
            getattr(report, "title", "")
        )

        summary = self._clean_text(
            getattr(report, "summary", "")
        )

        lines.append(
            f"# {title}"
        )

        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(
            summary or "No summary available."
        )

        sections = getattr(
            report,
            "sections",
            [],
        ) or []

        if sections:
            lines.append("")
            lines.append("## Research Findings")
            lines.append("")

            for index, section in enumerate(
                sections,
                start=1,
            ):
                self._append_section(
                    lines,
                    section,
                    index,
                )

        comparison = getattr(
            report,
            "comparison",
            None,
        )

        if comparison is not None:
            self._append_comparison(
                lines,
                comparison,
            )

        citations = getattr(
            report,
            "citations",
            [],
        ) or []

        if citations:
            self._append_references(
                lines,
                citations,
            )

        return "\n".join(lines).strip() + "\n"

    def _append_section(
        self,
        lines: list[str],
        section: ResearchSection,
        index: int,
    ) -> None:
        title = self._clean_text(
            getattr(section, "title", "")
        )

        content = self._clean_text(
            getattr(section, "content", "")
        )

        lines.append(
            f"### {index}. {title or 'Research Finding'}"
        )
        lines.append("")

        if content:
            lines.append(content)
        else:
            lines.append(
                "_No content available._"
            )

        evidence_ids = getattr(
            section,
            "evidence_ids",
            [],
        ) or []

        if evidence_ids:
            lines.append("")
            lines.append(
                "**Evidence:** "
                + ", ".join(
                    f"`{str(evidence_id)}`"
                    for evidence_id in evidence_ids
                )
            )

        lines.append("")

    def _append_comparison(
        self,
        lines: list[str],
        comparison: ComparisonResult,
    ) -> None:
        lines.append("## Comparison")
        lines.append("")

        table = getattr(
            comparison,
            "comparison_table",
            None,
        )

        if not table:
            lines.append(
                "_No comparison data available._"
            )
            return

        if self._looks_like_table_rows(table):
            self._append_markdown_table(
                lines,
                table,
            )
            return

        for row in table:
            lines.append(
                f"- {self._format_value(row)}"
            )

    def _append_references(
        self,
        lines: list[str],
        citations: Iterable[Citation],
    ) -> None:
        lines.append("## References")
        lines.append("")

        for index, citation in enumerate(
            citations,
            start=1,
        ):
            citation_text = self._clean_text(
                getattr(
                    citation,
                    "citation_text",
                    "",
                )
            )

            if not citation_text:
                citation_text = self._fallback_citation(
                    citation
                )

            lines.append(
                f"{index}. {citation_text}"
            )

    def _append_markdown_table(
        self,
        lines: list[str],
        rows: Iterable[object],
    ) -> None:
        rows = list(rows)

        if not rows:
            return

        normalized_rows = [
            self._row_to_values(row)
            for row in rows
        ]

        normalized_rows = [
            row
            for row in normalized_rows
            if row
        ]

        if not normalized_rows:
            return

        width = max(
            len(row)
            for row in normalized_rows
        )

        normalized_rows = [
            row + [""] * (width - len(row))
            for row in normalized_rows
        ]

        headers = normalized_rows[0]
        body = normalized_rows[1:]

        lines.append(
            "| "
            + " | ".join(
                self._escape_table_value(value)
                for value in headers
            )
            + " |"
        )

        lines.append(
            "| "
            + " | ".join(
                "---"
                for _ in headers
            )
            + " |"
        )

        for row in body:
            lines.append(
                "| "
                + " | ".join(
                    self._escape_table_value(value)
                    for value in row
                )
                + " |"
            )

    @staticmethod
    def _row_to_values(
        row: object,
    ) -> list[str]:
        if isinstance(row, dict):
            return [
                str(value)
                for value in row.values()
            ]

        if isinstance(row, (list, tuple)):
            return [
                str(value)
                for value in row
            ]

        return [str(row)]

    @staticmethod
    def _looks_like_table_rows(
        value: object,
    ) -> bool:
        if not isinstance(
            value,
            (list, tuple),
        ):
            return False

        if not value:
            return False

        first = value[0]

        return isinstance(
            first,
            (dict, list, tuple),
        )

    @staticmethod
    def _fallback_citation(
        citation: Citation,
    ) -> str:
        title = str(
            getattr(
                citation,
                "title",
                "Untitled source",
            )
            or "Untitled source"
        ).strip()

        authors = getattr(
            citation,
            "authors",
            [],
        ) or []

        author_text = (
            ", ".join(
                str(author)
                for author in authors
                if str(author).strip()
            )
            or "Unknown author"
        )

        year = getattr(
            citation,
            "year",
            None,
        )

        year_text = (
            str(year)
            if year is not None
            else "n.d."
        )

        url = getattr(
            citation,
            "url",
            None,
        )

        result = (
            f"{author_text}. "
            f"{title}. "
            f"{year_text}."
        )

        if url:
            result += f" {url}"

        return result

    def _validate_references(
        self,
        sections: list[ResearchSection],
        evidence: list[Evidence],
        citations: list[Citation],
        sources: list[ResearchSource],
    ) -> None:
        evidence_ids = {
            str(item.id)
            for item in evidence
            if getattr(item, "id", None)
        }

        source_ids = {
            str(source.id)
            for source in sources
            if getattr(source, "id", None)
        }

        citation_source_ids = {
            str(citation.source_id)
            for citation in citations
            if getattr(citation, "source_id", None)
        }

        for section in sections:
            evidence_refs = getattr(
                section,
                "evidence_ids",
                [],
            ) or []

            for evidence_id in evidence_refs:
                if str(evidence_id) not in evidence_ids:
                    raise ValueError(
                        "Research section references "
                        f"unknown evidence id: {evidence_id}"
                    )

        for citation in citations:
            source_id = getattr(
                citation,
                "source_id",
                None,
            )

            if source_id and str(source_id) not in source_ids:
                raise ValueError(
                    "Citation references unknown source id: "
                    f"{source_id}"
                )

        for source_id in citation_source_ids:
            if source_id not in source_ids:
                raise ValueError(
                    "Citation source does not exist: "
                    f"{source_id}"
                )

    @staticmethod
    def _required_text(
        value: object,
        field_name: str,
    ) -> str:
        if value is None:
            raise ValueError(
                f"{field_name} cannot be None"
            )

        text = str(value).strip()

        if not text:
            raise ValueError(
                f"{field_name} cannot be empty"
            )

        return text

    @staticmethod
    def _clean_text(
        value: object,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _escape_table_value(
        value: object,
    ) -> str:
        return (
            str(value)
            .replace("|", "\\|")
            .replace("\n", " ")
            .strip()
        )

    @staticmethod
    def _format_value(
        value: object,
    ) -> str:
        if isinstance(value, dict):
            return "; ".join(
                f"{key}: {val}"
                for key, val in value.items()
            )

        return str(value)

