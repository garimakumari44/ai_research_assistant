from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from math import ceil
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report_repository import ReportRepository
from app.research.models import ResearchQuery, ResearchReport
from app.research.pipeline import ResearchPipeline
from app.schemas.reports import (
    ReportCreate,
    ReportListResponse,
    ReportResponse,
    ReportStatus,
    ReportUpdate,
)


logger = logging.getLogger(__name__)


class ReportService:
    """
    Business logic for research report management.

    Reports use the canonical ResearchPipeline for:

        - knowledge-base retrieval
        - paper retrieval
        - GitHub retrieval
        - adaptive/shared retrieval infrastructure
        - evidence construction
        - citation construction
        - LLM synthesis
        - research report generation

    Persistence remains handled by ReportRepository.

    IMPORTANT
    ---------
    The ResearchPipeline must be injected by the API dependency layer.

    The Reports service must NOT create its own IndexRegistry or
    RetrievalService because the application already owns the shared
    retrieval indexes through app.state.index_registry.
    """

    def __init__(
        self,
        db: AsyncSession,
        research_pipeline: ResearchPipeline | None = None,
    ):
        self.db = db
        self.repository = ReportRepository(db)
        self.research_pipeline = research_pipeline

    # ============================================================
    # CREATE
    # ============================================================

    async def create_report(
        self,
        *,
        user_id: int,
        data: ReportCreate,
    ) -> ReportResponse:
        """
        Create a draft report without running research.
        """

        metadata: dict[str, Any] = {
            **(data.metadata or {}),
            "paper_ids": list(data.paper_ids or []),
        }

        report = await self.repository.create(
            user_id=user_id,
            title=data.title,
            research_question=data.research_question,
            status=ReportStatus.DRAFT.value,
            metadata=metadata,
        )

        await self.db.commit()
        await self.db.refresh(report)

        return ReportResponse.model_validate(report)

    # ============================================================
    # GET
    # ============================================================

    async def get_report(
        self,
        *,
        user_id: int,
        report_id: int,
    ) -> ReportResponse | None:
        """
        Fetch one report belonging to the authenticated user.
        """

        report = await self.repository.get_by_id(
            report_id=report_id,
            user_id=user_id,
        )

        if report is None:
            return None

        return ReportResponse.model_validate(report)

    # ============================================================
    # LIST
    # ============================================================

    async def list_reports(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: ReportStatus | None = None,
    ) -> ReportListResponse:
        """
        Return paginated reports for the authenticated user.
        """

        reports, total = await self.repository.list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status.value if status else None,
        )

        pages = (
            ceil(total / page_size)
            if total > 0
            else 0
        )

        return ReportListResponse(
            items=reports,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ============================================================
    # UPDATE
    # ============================================================

    async def update_report(
        self,
        *,
        user_id: int,
        report_id: int,
        data: ReportUpdate,
    ) -> ReportResponse | None:
        """
        Update an existing report.
        """

        report = await self.repository.get_by_id(
            report_id=report_id,
            user_id=user_id,
        )

        if report is None:
            return None

        content: dict[str, Any] | None = None

        if data.content is not None:
            content = data.content.model_dump(
                mode="json",
                exclude_none=True,
            )

        evidence: list[dict[str, Any]] | None = None

        if data.evidence is not None:
            evidence = [
                item.model_dump(
                    mode="json",
                    exclude_none=True,
                )
                for item in data.evidence
            ]

        status_value = (
            data.status.value
            if data.status is not None
            else None
        )

        completed_at = None

        if (
            data.status is not None
            and data.status == ReportStatus.COMPLETED
        ):
            completed_at = datetime.now(
                timezone.utc,
            )

        report = await self.repository.update(
            report,
            title=data.title,
            research_question=data.research_question,
            status=status_value,
            summary=data.summary,
            content=content,
            evidence=evidence,
            metadata=data.metadata,
            completed_at=completed_at,
        )

        await self.db.commit()
        await self.db.refresh(report)

        return ReportResponse.model_validate(report)

    # ============================================================
    # DELETE
    # ============================================================

    async def delete_report(
        self,
        *,
        user_id: int,
        report_id: int,
    ) -> bool:
        """
        Delete a report belonging to the authenticated user.
        """

        deleted = await self.repository.delete(
            report_id=report_id,
            user_id=user_id,
        )

        if deleted:
            await self.db.commit()

        return deleted

    # ============================================================
    # GENERATE
    # ============================================================

    async def generate_report(
        self,
        *,
        user_id: int,
        data: ReportCreate,
    ) -> ReportResponse:
        """
        Generate a complete research report.

        Pipeline:

            ReportCreate
                |
                v
            ResearchQuery
                |
                v
            ResearchPipeline
                |
                +-----------------------+
                |                       |
                v                       v
        Shared RetrievalService     LLMPipeline
                |                       |
                v                       v
        Shared IndexRegistry        LLM synthesis
                |
                +-----------+-----------+
                            |
                            v
                     ResearchReport
                            |
                            v
                    Report normalization
                            |
                            v
                    Report database row
                            |
                            v
                     ReportResponse

        The ResearchPipeline dependency must be configured by the
        API layer using the application's shared IndexRegistry.
        """

        # --------------------------------------------------------
        # 1. Resolve research question
        # --------------------------------------------------------

        research_question = (
            data.research_question
            or data.title
            or ""
        ).strip()

        if len(research_question) < 3:
            raise ValueError(
                "Research question must contain at least 3 characters."
            )

        # --------------------------------------------------------
        # 2. Prepare generation metadata
        # --------------------------------------------------------

        requested_at = datetime.now(
            timezone.utc,
        )

        metadata: dict[str, Any] = {
            **(data.metadata or {}),
            "paper_ids": list(data.paper_ids or []),
            "generation": {
                "pipeline": "ResearchPipeline",
                "requested_at": requested_at.isoformat(),
                "requested_by_user_id": user_id,
            },
        }

        # --------------------------------------------------------
        # 3. Create report shell
        # --------------------------------------------------------

        report = await self.repository.create(
            user_id=user_id,
            title=data.title,
            research_question=research_question,
            status=ReportStatus.GENERATING.value,
            metadata=metadata,
        )

        await self.db.flush()

        logger.info(
            "Research report generation started: "
            "report_id=%s user_id=%s question=%r",
            report.id,
            user_id,
            research_question,
        )

        try:
            # ----------------------------------------------------
            # 4. Validate ResearchPipeline
            # ----------------------------------------------------

            if self.research_pipeline is None:
                raise RuntimeError(
                    "ResearchPipeline is not configured for report generation."
                )

            # ----------------------------------------------------
            # 5. Build canonical ResearchQuery
            # ----------------------------------------------------

            research_query = self._build_research_query(
                data=data,
                question=research_question,
            )

            logger.info(
                "Running ResearchPipeline for report_id=%s: "
                "depth=%s include_papers=%s "
                "include_github=%s include_docs=%s",
                report.id,
                research_query.depth,
                research_query.include_papers,
                research_query.include_github,
                research_query.include_docs,
            )

            # ----------------------------------------------------
            # 6. Execute canonical research pipeline
            # ----------------------------------------------------

            research_report = await self.research_pipeline.run(
                research_query,
            )

            # ----------------------------------------------------
            # 7. Defensive validation
            # ----------------------------------------------------

            if not isinstance(
                research_report,
                ResearchReport,
            ):
                raise TypeError(
                    "ResearchPipeline.run() must return "
                    "a ResearchReport instance."
                )

            logger.info(
                "ResearchPipeline completed: "
                "report_id=%s status=%s sources=%s "
                "evidence=%s citations=%s",
                report.id,
                research_report.status,
                len(research_report.sources or []),
                len(research_report.evidence or []),
                len(research_report.citations or []),
            )

            # ----------------------------------------------------
            # 8. Normalize report
            # ----------------------------------------------------

            content = self._build_report_content(
                research_report,
            )

            evidence = self._build_report_evidence(
                research_report,
            )

            generation_metadata = (
                self._build_report_metadata(
                    research_report=research_report,
                    original_metadata=metadata,
                    normalized_content=content,
                    normalized_evidence=evidence,
                )
            )

            # ----------------------------------------------------
            # 9. Determine final title
            # ----------------------------------------------------

            final_title = (
                data.title.strip()
                if data.title and data.title.strip()
                else research_report.title
            )

            if not final_title:
                final_title = (
                    f"Research Report: {research_question}"
                )

            # ----------------------------------------------------
            # 10. Determine final status
            # ----------------------------------------------------

            pipeline_status = str(
                research_report.status or ""
            ).lower()

            if pipeline_status == "failed":
                final_status = ReportStatus.FAILED.value

            elif pipeline_status == "partial":
                final_status = ReportStatus.COMPLETED.value
                generation_metadata["partial_result"] = True

            else:
                final_status = ReportStatus.COMPLETED.value

            # ----------------------------------------------------
            # 11. Mark report completed
            # ----------------------------------------------------

            completed_at = datetime.now(
                timezone.utc,
            )

            report = await self.repository.update(
                report,
                title=final_title,
                research_question=research_question,
                status=final_status,
                summary=research_report.summary,
                content=content,
                evidence=evidence,
                metadata=generation_metadata,
                completed_at=completed_at,
            )

            await self.db.commit()
            await self.db.refresh(report)

            logger.info(
                "Research report generated successfully: "
                "report_id=%s status=%s",
                report.id,
                report.status,
            )

            return ReportResponse.model_validate(report)

        except Exception as exc:
            logger.exception(
                "Research report generation failed: "
                "report_id=%s question=%r",
                report.id,
                research_question,
            )

            failure_metadata = {
                **metadata,
                "generation": {
                    **metadata.get(
                        "generation",
                        {},
                    ),
                    "failed_at": datetime.now(
                        timezone.utc,
                    ).isoformat(),
                    "error_type": exc.__class__.__name__,
                    "error": str(exc)[:5000],
                },
            }

            try:
                await self.repository.update(
                    report,
                    status=ReportStatus.FAILED.value,
                    metadata=failure_metadata,
                    completed_at=datetime.now(
                        timezone.utc,
                    ),
                )

                await self.db.commit()

            except Exception:
                logger.exception(
                    "Failed to persist failed report state: "
                    "report_id=%s",
                    report.id,
                )

                await self.db.rollback()

            raise

    # ============================================================
    # RESEARCH QUERY
    # ============================================================

    @staticmethod
    def _build_research_query(
        *,
        data: ReportCreate,
        question: str,
    ) -> ResearchQuery:
        """
        Convert the Reports API payload into the canonical
        ResearchQuery consumed by ResearchPipeline.
        """

        metadata = data.metadata or {}

        depth = metadata.get(
            "depth",
            "medium",
        )

        if depth not in {
            "basic",
            "medium",
            "deep",
        }:
            depth = "medium"

        include_papers = ReportService._coerce_bool(
            metadata.get(
                "include_papers",
                True,
            ),
            default=True,
        )

        include_github = ReportService._coerce_bool(
            metadata.get(
                "include_github",
                True,
            ),
            default=True,
        )

        include_docs = ReportService._coerce_bool(
            metadata.get(
                "include_docs",
                True,
            ),
            default=True,
        )

        # IMPORTANT:
        # ResearchQuery uses `question`, not `query`.
        return ResearchQuery(
            question=question,
            depth=depth,
            include_papers=include_papers,
            include_github=include_github,
            include_docs=include_docs,
        )

    # ============================================================
    # CONTENT MAPPING / NORMALIZATION
    # ============================================================

    @staticmethod
    def _build_report_content(
        research_report: ResearchReport,
    ) -> dict[str, Any]:
        """
        Normalize ResearchPipeline output into a clean report structure.

        The ResearchPipeline may currently return an LLM-generated
        Markdown synthesis inside a section such as "Key Findings".

        This method converts that Markdown into structured fields
        suitable for the Reports UI.
        """

        sections = list(
            research_report.sections or []
        )

        key_findings: list[str] = []
        limitations: list[str] = []
        research_gaps: list[str] = []
        future_directions: list[str] = []
        contradictions: list[str] = []
        emerging_trends: list[str] = []

        methodology: str | None = None
        evidence_synthesis: str | None = None
        conclusion: str | None = None

        synthesis_sections: list[str] = []

        for section in sections:
            title = ReportService._clean_text(
                getattr(
                    section,
                    "title",
                    "",
                )
                or ""
            )

            section_content = str(
                getattr(
                    section,
                    "content",
                    "",
                )
                or ""
            ).strip()

            if not section_content:
                continue

            normalized_title = (
                ReportService._normalize_heading(
                    title,
                )
            )

            if (
                "key finding" in normalized_title
                or normalized_title == "finding"
                or normalized_title == "findings"
            ):
                parsed = (
                    ReportService._parse_synthesis_markdown(
                        section_content,
                    )
                )

                key_findings.extend(
                    parsed["key_findings"]
                )

                limitations.extend(
                    parsed["limitations"]
                )

                research_gaps.extend(
                    parsed["research_gaps"]
                )

                future_directions.extend(
                    parsed["future_directions"]
                )

                contradictions.extend(
                    parsed["contradictions"]
                )

                emerging_trends.extend(
                    parsed["emerging_trends"]
                )

                if parsed["summary"]:
                    conclusion = parsed["summary"]

                synthesis_sections.append(
                    section_content
                )

                continue

            if (
                "method" in normalized_title
                or "methodology" in normalized_title
                or "approach" in normalized_title
            ):
                methodology = (
                    ReportService._clean_paragraph(
                        section_content,
                    )
                )

                continue

            if (
                "analysis" in normalized_title
                or "synthesis" in normalized_title
                or "evidence" in normalized_title
                or "discussion" in normalized_title
            ):
                evidence_synthesis = (
                    ReportService._clean_paragraph(
                        section_content,
                    )
                )

                continue

            if "conclusion" in normalized_title:
                conclusion = (
                    ReportService._clean_paragraph(
                        section_content,
                    )
                )

                continue

            if (
                "limitation" in normalized_title
                or "limitations" in normalized_title
            ):
                limitations.extend(
                    ReportService._split_list_content(
                        section_content,
                    )
                )

                continue

            if (
                "research gap" in normalized_title
                or "research gaps" in normalized_title
                or normalized_title == "gap"
                or normalized_title == "gaps"
            ):
                research_gaps.extend(
                    ReportService._split_list_content(
                        section_content,
                    )
                )

                continue

            if (
                "future" in normalized_title
                or "direction" in normalized_title
                or "directions" in normalized_title
            ):
                future_directions.extend(
                    ReportService._split_list_content(
                        section_content,
                    )
                )

                continue

            if (
                "contradiction" in normalized_title
                or "conflict" in normalized_title
            ):
                contradictions.extend(
                    ReportService._split_list_content(
                        section_content,
                    )
                )

                continue

            if (
                "emerging trend" in normalized_title
                or "emerging trends" in normalized_title
                or normalized_title == "trends"
            ):
                emerging_trends.extend(
                    ReportService._split_list_content(
                        section_content,
                    )
                )

                continue

        if not evidence_synthesis and synthesis_sections:
            evidence_synthesis = (
                ReportService._clean_paragraph(
                    synthesis_sections[0],
                )
            )

        summary = ReportService._clean_paragraph(
            research_report.summary or "",
        )

        if not conclusion:
            parsed_summary = (
                ReportService._extract_summary_from_sections(
                    sections,
                )
            )

            conclusion = (
                parsed_summary
                or summary
                or None
            )

        if not key_findings and summary:
            key_findings = [
                summary,
            ]

        key_findings = (
            ReportService._deduplicate_strings(
                key_findings,
            )
        )

        limitations = (
            ReportService._deduplicate_strings(
                limitations,
            )
        )

        research_gaps = (
            ReportService._deduplicate_strings(
                research_gaps,
            )
        )

        future_directions = (
            ReportService._deduplicate_strings(
                future_directions,
            )
        )

        contradictions = (
            ReportService._deduplicate_strings(
                contradictions,
            )
        )

        emerging_trends = (
            ReportService._deduplicate_strings(
                emerging_trends,
            )
        )

        if not methodology:
            methodology = (
                "Evidence was retrieved from the indexed research "
                "corpus using the configured retrieval pipeline and "
                "then synthesized into an evidence-grounded research "
                "report by the research language model."
            )

        if not evidence_synthesis:
            if key_findings:
                evidence_synthesis = (
                    "The retrieved evidence supports the following "
                    "findings:\n\n"
                    + "\n".join(
                        f"- {finding}"
                        for finding in key_findings
                    )
                )
            elif summary:
                evidence_synthesis = summary

        supporting_evidence: list[
            dict[str, Any]
        ] = []

        for item in (
            research_report.evidence or []
        ):
            supporting_evidence.append(
                ReportService._model_to_dict(
                    item,
                )
            )

        sources = (
            ReportService._build_unique_sources(
                research_report,
            )
        )

        references = (
            ReportService._build_unique_references(
                research_report,
            )
        )

        comparison = None

        if research_report.comparison is not None:
            comparison = (
                ReportService._model_to_dict(
                    research_report.comparison,
                )
            )

        return {
            "executive_summary": (
                summary or None
            ),
            "key_findings": key_findings,
            "methodology": methodology,
            "evidence_synthesis": evidence_synthesis,
            "supporting_evidence": supporting_evidence,
            "contradictions": contradictions,
            "limitations": limitations,
            "research_gaps": research_gaps,
            "emerging_trends": emerging_trends,
            "future_directions": future_directions,
            "conclusion": conclusion,
            "references": references,
            "sections": [
                ReportService._model_to_dict(
                    section,
                )
                for section in sections
            ],
            "sources": sources,
            "comparison": comparison,
            "normalization": {
                "version": "2.0",
                "key_findings_count": len(
                    key_findings
                ),
                "limitations_count": len(
                    limitations
                ),
                "research_gaps_count": len(
                    research_gaps
                ),
                "future_directions_count": len(
                    future_directions
                ),
                "supporting_evidence_count": len(
                    supporting_evidence
                ),
                "unique_reference_count": len(
                    references
                ),
                "unique_source_count": len(
                    sources
                ),
            },
        }

    # ============================================================
    # MARKDOWN PARSING
    # ============================================================

    @staticmethod
    def _parse_synthesis_markdown(
        content: str,
    ) -> dict[str, Any]:
        """
        Parse the common LLM report format.
        """

        result: dict[str, Any] = {
            "key_findings": [],
            "limitations": [],
            "research_gaps": [],
            "future_directions": [],
            "contradictions": [],
            "emerging_trends": [],
            "summary": None,
        }

        if not content or not content.strip():
            return result

        text = content.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        text = re.sub(
            r"```(?:markdown|md|text)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = text.replace(
            "```",
            "",
        )

        heading_pattern = re.compile(
            r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$"
        )

        matches = list(
            heading_pattern.finditer(text)
        )

        if not matches:
            result["key_findings"] = (
                ReportService._split_list_content(
                    text,
                )
            )

            return result

        for index, match in enumerate(matches):
            heading = (
                ReportService._normalize_heading(
                    match.group(1),
                )
            )

            start = match.end()

            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )

            body = text[start:end].strip()

            if not body:
                continue

            if ReportService._is_document_title(
                heading,
            ):
                continue

            if (
                "contribution" in heading
                or "main finding" in heading
                or heading == "findings"
                or heading == "key findings"
            ):
                result["key_findings"].extend(
                    ReportService._split_list_content(
                        body,
                    )
                )

                continue

            if "limitation" in heading:
                result["limitations"].extend(
                    ReportService._split_list_content(
                        body,
                    )
                )

                continue

            if (
                "research gap" in heading
                or heading == "gaps"
                or heading == "gap"
            ):
                result["research_gaps"].extend(
                    ReportService._split_list_content(
                        body,
                    )
                )

                continue

            if (
                "future" in heading
                or "direction" in heading
            ):
                result["future_directions"].extend(
                    ReportService._split_list_content(
                        body,
                    )
                )

                continue

            if (
                "contradiction" in heading
                or "conflict" in heading
            ):
                result["contradictions"].extend(
                    ReportService._split_list_content(
                        body,
                    )
                )

                continue

            if (
                "trend" in heading
                or "emerging" in heading
            ):
                result["emerging_trends"].extend(
                    ReportService._split_list_content(
                        body,
                    )
                )

                continue

            if (
                heading == "summary"
                or "conclusion" in heading
            ):
                result["summary"] = (
                    ReportService._clean_paragraph(
                        body,
                    )
                )

                continue

        if not result["key_findings"]:
            result["key_findings"] = (
                ReportService._extract_numbered_items(
                    text,
                )
            )

        result["key_findings"] = (
            ReportService._deduplicate_strings(
                result["key_findings"],
            )
        )

        result["limitations"] = (
            ReportService._deduplicate_strings(
                result["limitations"],
            )
        )

        result["research_gaps"] = (
            ReportService._deduplicate_strings(
                result["research_gaps"],
            )
        )

        result["future_directions"] = (
            ReportService._deduplicate_strings(
                result["future_directions"],
            )
        )

        result["contradictions"] = (
            ReportService._deduplicate_strings(
                result["contradictions"],
            )
        )

        result["emerging_trends"] = (
            ReportService._deduplicate_strings(
                result["emerging_trends"],
            )
        )

        return result

    # ============================================================
    # LIST / TEXT NORMALIZATION
    # ============================================================

    @staticmethod
    def _split_list_content(
        content: str,
    ) -> list[str]:
        """
        Convert Markdown list/numbered content into clean strings.
        """

        if not content or not content.strip():
            return []

        text = content.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        text = re.sub(
            r"```(?:markdown|md|text)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = text.replace(
            "```",
            "",
        )

        text = re.sub(
            r"(?m)^\s{0,3}#{1,6}\s+",
            "",
            text,
        )

        text = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            text,
        )

        text = re.sub(
            r"__(.*?)__",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?<!\*)\*([^*\n]+)\*(?!\*)",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?<!_)_([^_\n]+)_(?!_)",
            r"\1",
            text,
        )

        numbered_pattern = re.compile(
            r"(?m)^\s*(?:[-*]\s*)?"
            r"(?:\d+[\.\)]|[a-zA-Z][\.\)])\s+"
        )

        numbered_matches = list(
            numbered_pattern.finditer(text)
        )

        if numbered_matches:
            items: list[str] = []

            for index, match in enumerate(
                numbered_matches,
            ):
                start = match.end()

                end = (
                    numbered_matches[index + 1].start()
                    if index + 1 < len(numbered_matches)
                    else len(text)
                )

                item = text[start:end]

                item = ReportService._clean_text(
                    item,
                )

                if item:
                    items.append(item)

            if items:
                return ReportService._deduplicate_strings(
                    items,
                )

        bullet_pattern = re.compile(
            r"(?m)^\s*[-*+]\s+(.+?)(?=\n|$)"
        )

        bullet_matches = bullet_pattern.findall(
            text,
        )

        if bullet_matches:
            items = [
                ReportService._clean_text(
                    item,
                )
                for item in bullet_matches
            ]

            items = [
                item
                for item in items
                if item
            ]

            if items:
                return ReportService._deduplicate_strings(
                    items,
                )

        paragraphs = re.split(
            r"\n\s*\n+",
            text,
        )

        cleaned = [
            ReportService._clean_text(
                paragraph,
            )
            for paragraph in paragraphs
        ]

        cleaned = [
            item
            for item in cleaned
            if item
        ]

        return ReportService._deduplicate_strings(
            cleaned,
        )

    @staticmethod
    def _extract_numbered_items(
        text: str,
    ) -> list[str]:
        """
        Extract numbered items from arbitrary Markdown text.
        """

        return ReportService._split_list_content(
            text,
        )

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:
        """
        Remove Markdown formatting and normalize whitespace.
        """

        if not value:
            return ""

        text = str(value)

        text = re.sub(
            r"```(?:markdown|md|text)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = text.replace(
            "```",
            "",
        )

        text = re.sub(
            r"(?m)^\s{0,3}#{1,6}\s+",
            "",
            text,
        )

        text = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            text,
        )

        text = re.sub(
            r"__(.*?)__",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?<!\*)\*([^*\n]+)\*(?!\*)",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?<!_)_([^_\n]+)_(?!_)",
            r"\1",
            text,
        )

        text = re.sub(
            r"`([^`]+)`",
            r"\1",
            text,
        )

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?m)^\s*[-*+]\s+",
            "",
            text,
        )

        text = re.sub(
            r"(?m)^\s*\d+[\.\)]\s+",
            "",
            text,
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    @staticmethod
    def _clean_paragraph(
        value: str,
    ) -> str:
        """
        Normalize a section intended to be rendered as prose.
        """

        text = ReportService._clean_text(
            value,
        )

        paragraphs = re.split(
            r"\n\s*\n+",
            text,
        )

        paragraphs = [
            re.sub(
                r"\s*\n\s*",
                " ",
                paragraph,
            ).strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

        return "\n\n".join(
            paragraphs,
        ).strip()

    @staticmethod
    def _normalize_heading(
        value: str,
    ) -> str:
        """
        Normalize a heading for reliable matching.
        """

        text = ReportService._clean_text(
            value,
        )

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _is_document_title(
        heading: str,
    ) -> bool:
        """
        Identify headings that are document-level titles rather
        than actual report sections.
        """

        normalized = (
            ReportService._normalize_heading(
                heading,
            )
        )

        title_patterns = (
            "main contributions and limitations",
            "contributions and limitations",
            "transformer architecture contributions and limitations",
        )

        return normalized in title_patterns

    @staticmethod
    def _extract_summary_from_sections(
        sections: list[Any],
    ) -> str | None:
        """
        Look for a Summary/Conclusion section in the original
        ResearchPipeline sections.
        """

        for section in sections:
            title = ReportService._normalize_heading(
                str(
                    getattr(
                        section,
                        "title",
                        "",
                    )
                    or ""
                ),
            )

            if (
                title == "summary"
                or "conclusion" in title
            ):
                content = (
                    getattr(
                        section,
                        "content",
                        "",
                    )
                    or ""
                )

                cleaned = (
                    ReportService._clean_paragraph(
                        str(content),
                    )
                )

                if cleaned:
                    return cleaned

        return None

    @staticmethod
    def _deduplicate_strings(
        values: list[str],
    ) -> list[str]:
        """
        Stable, case-insensitive string deduplication.
        """

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = (
                ReportService._clean_text(
                    value,
                )
            )

            if not cleaned:
                continue

            key = re.sub(
                r"\s+",
                " ",
                cleaned,
            ).strip().lower()

            if key in seen:
                continue

            seen.add(key)
            result.append(cleaned)

        return result

    # ============================================================
    # EVIDENCE MAPPING
    # ============================================================

    @staticmethod
    def _build_report_evidence(
        research_report: ResearchReport,
    ) -> list[dict[str, Any]]:
        """
        Convert canonical ResearchReport evidence into the
        frontend ReportEvidence shape.
        """

        sources_by_id: dict[str, Any] = {
            str(source.id): source
            for source in (
                research_report.sources or []
            )
            if getattr(
                source,
                "id",
                None,
            ) is not None
        }

        result: list[dict[str, Any]] = []

        for item in (
            research_report.evidence or []
        ):
            evidence_id = str(
                getattr(
                    item,
                    "id",
                    "",
                )
                or ""
            )

            source_id = str(
                getattr(
                    item,
                    "source_id",
                    "",
                )
                or ""
            )

            source = sources_by_id.get(
                source_id
            )

            source_metadata: dict[str, Any] = {}

            if source is not None:
                raw_metadata = getattr(
                    source,
                    "metadata",
                    {},
                )

                if isinstance(
                    raw_metadata,
                    dict,
                ):
                    source_metadata = dict(
                        raw_metadata,
                    )

            chunk_id = (
                source_metadata.get(
                    "chunk_id",
                )
                or source_metadata.get(
                    "document_chunk_id",
                )
                or source_metadata.get(
                    "id",
                )
            )

            if chunk_id is None:
                chunk_id = getattr(
                    item,
                    "chunk_id",
                    None,
                )

            if chunk_id is not None:
                chunk_id = str(
                    chunk_id,
                )

            paper_id = source_metadata.get(
                "paper_id",
            )

            if paper_id is None:
                paper_id = getattr(
                    item,
                    "paper_id",
                    None,
                )

            if paper_id is not None:
                try:
                    paper_id = int(
                        paper_id,
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    paper_id = None

            citation_key = (
                source_metadata.get(
                    "citation_key",
                )
                or getattr(
                    item,
                    "citation_key",
                    None,
                )
                or evidence_id
                or source_id
            )

            source_type = None

            if source is not None:
                source_type = getattr(
                    source,
                    "source_type",
                    None,
                )

            evidence_record: dict[str, Any] = {
                "paper_id": paper_id,
                "chunk_id": chunk_id,
                "citation_key": (
                    str(citation_key)
                    if citation_key
                    else None
                ),
                "title": (
                    getattr(
                        source,
                        "title",
                        None,
                    )
                    if source is not None
                    else source_metadata.get(
                        "title",
                    )
                ),
                "authors": (
                    list(
                        getattr(
                            source,
                            "authors",
                            [],
                        )
                        or []
                    )
                    if source is not None
                    else list(
                        source_metadata.get(
                            "authors",
                            [],
                        )
                        or []
                    )
                ),
                "year": (
                    ReportService._extract_year(
                        source_metadata,
                    )
                ),
                "source": (
                    source_type
                    if source_type is not None
                    else source_metadata.get(
                        "source",
                    )
                ),
                "quote": getattr(
                    item,
                    "supporting_text",
                    None,
                ),
                "evidence": getattr(
                    item,
                    "claim",
                    None,
                ),
                "relevance_score": (
                    getattr(
                        item,
                        "relevance_score",
                        None,
                    )
                ),
            }

            evidence_record["source_id"] = (
                source_id or None
            )

            evidence_record["evidence_id"] = (
                evidence_id or None
            )

            confidence = getattr(
                item,
                "confidence",
                None,
            )

            if confidence is not None:
                evidence_record["confidence"] = (
                    confidence
                )

            if source_metadata:
                evidence_record[
                    "source_metadata"
                ] = dict(
                    source_metadata,
                )

            result.append(
                evidence_record,
            )

        return result

    # ============================================================
    # UNIQUE SOURCES
    # ============================================================

    @staticmethod
    def _build_unique_sources(
        research_report: ResearchReport,
    ) -> list[dict[str, Any]]:
        """
        Build a unique source list.
        """

        evidence_by_source: dict[str, int] = {}

        for item in (
            research_report.evidence or []
        ):
            source_id = str(
                getattr(
                    item,
                    "source_id",
                    "",
                )
                or ""
            )

            if source_id:
                evidence_by_source[source_id] = (
                    evidence_by_source.get(
                        source_id,
                        0,
                    )
                    + 1
                )

        unique: dict[str, dict[str, Any]] = {}

        for source in (
            research_report.sources or []
        ):
            source_dict = (
                ReportService._model_to_dict(
                    source,
                )
            )

            key = (
                ReportService._source_identity(
                    source_dict,
                )
            )

            if key in unique:
                existing = unique[key]

                existing["evidence_count"] = (
                    existing.get(
                        "evidence_count",
                        0,
                    )
                    + source_dict.get(
                        "evidence_count",
                        0,
                    )
                )

                continue

            source_id = source_dict.get(
                "id",
            )

            source_dict["evidence_count"] = (
                evidence_by_source.get(
                    str(source_id),
                    0,
                )
            )

            unique[key] = source_dict

        return list(
            unique.values(),
        )

    # ============================================================
    # UNIQUE REFERENCES
    # ============================================================

    @staticmethod
    def _build_unique_references(
        research_report: ResearchReport,
    ) -> list[dict[str, Any]]:
        """
        Convert citation records into bibliography-style references.
        """

        evidence_lookup: dict[str, dict[str, Any]] = {}

        for item in (
            research_report.evidence or []
        ):
            evidence_dict = (
                ReportService._model_to_dict(
                    item,
                )
            )

            evidence_id = str(
                evidence_dict.get(
                    "id",
                    "",
                )
                or ""
            )

            source_id = str(
                evidence_dict.get(
                    "source_id",
                    "",
                )
                or ""
            )

            if evidence_id:
                evidence_lookup[
                    evidence_id
                ] = evidence_dict

            if source_id:
                evidence_lookup[
                    source_id
                ] = evidence_dict

        source_lookup: dict[str, dict[str, Any]] = {}

        for source in (
            research_report.sources or []
        ):
            source_dict = (
                ReportService._model_to_dict(
                    source,
                )
            )

            source_id = str(
                source_dict.get(
                    "id",
                    "",
                )
                or ""
            )

            if source_id:
                source_lookup[
                    source_id
                ] = source_dict

        unique: dict[
            str,
            dict[str, Any],
        ] = {}

        for citation in (
            research_report.citations or []
        ):
            citation_dict = (
                ReportService._model_to_dict(
                    citation,
                )
            )

            raw_source_id = (
                citation_dict.get(
                    "source_id",
                )
                or citation_dict.get(
                    "sourceId",
                )
                or citation_dict.get(
                    "document_id",
                )
                or citation_dict.get(
                    "paper_id",
                )
            )

            source_id = (
                str(raw_source_id)
                if raw_source_id is not None
                else ""
            )

            evidence_dict = (
                evidence_lookup.get(
                    source_id,
                    {},
                )
            )

            source_dict = (
                source_lookup.get(
                    source_id,
                    {},
                )
            )

            merged: dict[str, Any] = {}

            merged.update(
                source_dict,
            )

            merged.update(
                citation_dict,
            )

            for key in (
                "paper_id",
                "document_id",
                "title",
                "authors",
                "year",
                "source",
            ):
                if (
                    not merged.get(key)
                    and evidence_dict.get(key)
                ):
                    merged[key] = (
                        evidence_dict[key]
                    )

            identity = (
                ReportService._reference_identity(
                    merged,
                )
            )

            if identity not in unique:
                unique[identity] = {
                    "id": (
                        f"reference-{len(unique) + 1}"
                    ),
                    "title": (
                        merged.get(
                            "title",
                        )
                        or "Untitled source"
                    ),
                    "authors": list(
                        merged.get(
                            "authors",
                            [],
                        )
                        or []
                    ),
                    "year": (
                        ReportService._safe_year(
                            merged,
                        )
                    ),
                    "source": (
                        merged.get(
                            "source",
                        )
                    ),
                    "paper_id": (
                        ReportService._safe_int(
                            merged.get(
                                "paper_id",
                            )
                        )
                    ),
                    "document_id": (
                        merged.get(
                            "document_id",
                        )
                    ),
                    "source_id": (
                        source_id
                        or merged.get(
                            "id",
                        )
                    ),
                    "citation_text": (
                        ReportService._build_citation_text(
                            merged,
                        )
                    ),
                    "evidence_count": 0,
                }

        if not unique:
            for source in (
                research_report.sources or []
            ):
                source_dict = (
                    ReportService._model_to_dict(
                        source,
                    )
                )

                identity = (
                    ReportService._reference_identity(
                        source_dict,
                    )
                )

                if identity in unique:
                    continue

                unique[identity] = {
                    "id": (
                        f"reference-{len(unique) + 1}"
                    ),
                    "title": (
                        source_dict.get(
                            "title",
                        )
                        or "Untitled source"
                    ),
                    "authors": list(
                        source_dict.get(
                            "authors",
                            [],
                        )
                        or []
                    ),
                    "year": (
                        ReportService._safe_year(
                            source_dict,
                        )
                    ),
                    "source": (
                        source_dict.get(
                            "source",
                        )
                        or source_dict.get(
                            "source_type",
                        )
                    ),
                    "paper_id": (
                        ReportService._safe_int(
                            source_dict.get(
                                "paper_id",
                            )
                        )
                    ),
                    "document_id": (
                        source_dict.get(
                            "document_id",
                        )
                    ),
                    "source_id": (
                        source_dict.get(
                            "id",
                        )
                    ),
                    "citation_text": (
                        ReportService._build_citation_text(
                            source_dict,
                        )
                    ),
                    "evidence_count": 0,
                }

        for reference in unique.values():
            identity = (
                ReportService._reference_identity(
                    reference,
                )
            )

            count = 0

            for item in (
                research_report.evidence or []
            ):
                evidence_dict = (
                    ReportService._model_to_dict(
                        item,
                    )
                )

                if (
                    ReportService._reference_identity(
                        evidence_dict,
                    )
                    == identity
                ):
                    count += 1

            reference["evidence_count"] = count

        return list(
            unique.values(),
        )

    # ============================================================
    # SOURCE / REFERENCE IDENTITY
    # ============================================================

    @staticmethod
    def _source_identity(
        source: dict[str, Any],
    ) -> str:
        """
        Determine stable identity for a source.
        """

        paper_id = source.get(
            "paper_id",
        )

        if paper_id is not None:
            return f"paper:{paper_id}"

        document_id = (
            source.get(
                "document_id",
            )
            or source.get(
                "documentId",
            )
        )

        if document_id:
            return (
                f"document:{str(document_id).lower()}"
            )

        source_id = source.get(
            "id",
        )

        if source_id:
            return (
                f"source:{str(source_id).lower()}"
            )

        title = ReportService._normalize_identity_text(
            source.get(
                "title",
            )
            or "",
        )

        source_type = ReportService._normalize_identity_text(
            source.get(
                "source",
            )
            or source.get(
                "source_type",
            )
            or "",
        )

        return (
            f"title:{title}|source:{source_type}"
        )

    @staticmethod
    def _reference_identity(
        source: dict[str, Any],
    ) -> str:
        """
        Determine stable bibliography identity.
        """

        paper_id = source.get(
            "paper_id",
        )

        if paper_id is not None:
            try:
                return f"paper:{int(paper_id)}"
            except (
                TypeError,
                ValueError,
            ):
                pass

        document_id = (
            source.get(
                "document_id",
            )
            or source.get(
                "documentId",
            )
        )

        if document_id:
            return (
                f"document:{str(document_id).lower()}"
            )

        title = ReportService._normalize_identity_text(
            source.get(
                "title",
            )
            or "",
        )

        authors = "|".join(
            ReportService._normalize_identity_text(
                str(author),
            )
            for author in (
                source.get(
                    "authors",
                    [],
                )
                or []
            )
        )

        year = (
            ReportService._safe_year(
                source,
            )
        )

        source_type = ReportService._normalize_identity_text(
            source.get(
                "source",
            )
            or source.get(
                "source_type",
            )
            or "",
        )

        if title:
            return (
                f"title:{title}"
                f"|authors:{authors}"
                f"|year:{year or ''}"
                f"|source:{source_type}"
            )

        source_id = source.get(
            "source_id",
        ) or source.get(
            "id",
        )

        return (
            f"source:{str(source_id).lower()}"
        )

    @staticmethod
    def _normalize_identity_text(
        value: str,
    ) -> str:
        """
        Normalize text used in source identity keys.
        """

        text = str(
            value or "",
        ).strip().lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    # ============================================================
    # CITATION FORMATTING
    # ============================================================

    @staticmethod
    def _build_citation_text(
        source: dict[str, Any],
    ) -> str:
        """
        Build a conservative citation label.
        """

        title = str(
            source.get(
                "title",
                "",
            )
            or ""
        ).strip()

        authors = [
            str(author).strip()
            for author in (
                source.get(
                    "authors",
                    [],
                )
                or []
            )
            if str(author).strip()
        ]

        year = ReportService._safe_year(
            source,
        )

        if authors:
            if len(authors) == 1:
                author_text = authors[0]
            elif len(authors) <= 3:
                author_text = ", ".join(
                    authors,
                )
            else:
                author_text = (
                    f"{authors[0]} et al."
                )

            if year:
                return (
                    f"{author_text} ({year}). "
                    f"{title}"
                )

            return (
                f"{author_text}. {title}"
            )

        if year:
            return (
                f"{title} ({year})"
            )

        return title

    # ============================================================
    # METADATA
    # ============================================================

    @staticmethod
    def _build_report_metadata(
        *,
        research_report: ResearchReport,
        original_metadata: dict[str, Any],
        normalized_content: dict[str, Any],
        normalized_evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Preserve request metadata while recording complete
        ResearchPipeline and normalization metadata.
        """

        pipeline_metadata = (
            research_report.metadata or {}
        )

        unique_sources = normalized_content.get(
            "sources",
            [],
        )

        unique_references = normalized_content.get(
            "references",
            [],
        )

        return {
            **original_metadata,
            "research_pipeline": (
                pipeline_metadata
            ),
            "source_count": len(
                research_report.sources or []
            ),
            "unique_source_count": len(
                unique_sources
            ),
            "evidence_count": len(
                normalized_evidence
            ),
            "citation_count": len(
                research_report.citations or []
            ),
            "unique_reference_count": len(
                unique_references
            ),
            "report_status": (
                research_report.status
            ),
            "normalization_version": "2.0",
            "generated_at": datetime.now(
                timezone.utc,
            ).isoformat(),
        }

    # ============================================================
    # SAFE VALUE HELPERS
    # ============================================================

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        """
        Safely convert a value to int.
        """

        if value is None:
            return None

        try:
            return int(
                value,
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _safe_year(
        source: dict[str, Any],
    ) -> int | None:
        """
        Resolve year from a source/citation dictionary.
        """

        year = source.get(
            "year",
        )

        if year is not None:
            try:
                year_int = int(
                    year,
                )

                if 1900 <= year_int <= 2100:
                    return year_int

            except (
                TypeError,
                ValueError,
            ):
                pass

        return ReportService._extract_year(
            source,
        )

    # ============================================================
    # BOOLEAN HELPER
    # ============================================================

    @staticmethod
    def _coerce_bool(
        value: Any,
        *,
        default: bool,
    ) -> bool:
        """
        Safely convert metadata values to bool.
        """

        if value is None:
            return default

        if isinstance(
            value,
            bool,
        ):
            return value

        if isinstance(
            value,
            int,
        ):
            return value != 0

        if isinstance(
            value,
            str,
        ):
            normalized = value.strip().lower()

            if normalized in {
                "true",
                "1",
                "yes",
                "y",
                "on",
            }:
                return True

            if normalized in {
                "false",
                "0",
                "no",
                "n",
                "off",
            }:
                return False

        return default

    # ============================================================
    # MODEL SERIALIZATION
    # ============================================================

    @staticmethod
    def _model_to_dict(
        value: Any,
    ) -> dict[str, Any]:
        """
        Convert a Pydantic model, dict, or simple object into
        JSON-compatible dictionary data.
        """

        if value is None:
            return {}

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                result = value.model_dump(
                    mode="json",
                )

                if isinstance(
                    result,
                    dict,
                ):
                    return result

            except Exception:
                logger.debug(
                    "Could not model_dump report value.",
                    exc_info=True,
                )

        if isinstance(
            value,
            dict,
        ):
            return dict(
                value,
            )

        if hasattr(
            value,
            "__dict__",
        ):
            return {
                key: val
                for key, val in vars(
                    value,
                ).items()
                if not key.startswith("_")
            }

        return {
            "value": str(
                value,
            ),
        }

    # ============================================================
    # YEAR EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_year(
        metadata: dict[str, Any],
    ) -> int | None:
        """
        Extract a publication year from heterogeneous source metadata.
        """

        for key in (
            "year",
            "publication_year",
            "published_year",
            "publication_date",
            "published",
        ):
            value = metadata.get(
                key,
            )

            if value is None:
                continue

            if isinstance(
                value,
                int,
            ):
                if 1900 <= value <= 2100:
                    return value

            try:
                text = str(
                    value,
                )

                match = re.search(
                    r"(19|20)\d{2}",
                    text,
                )

                if match:
                    return int(
                        match.group(0),
                    )

            except Exception:
                continue

        return None