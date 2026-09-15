
from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from app.research.models import (
    Citation,
    Evidence,
    ResearchQuery,
    ResearchReport,
    ResearchSection,
    ResearchSource,
    RetrievedDocument,
)
from app.research.retrieval.paper_retriever import PaperRetriever
from app.research.retrieval.github_retriever import GitHubRetriever

logger = logging.getLogger(__name__)


class ResearchService:
    """
    Application service for the research pipeline.

    Flow
    ----
        ResearchQuery
            ↓
        PaperRetriever
        GitHubRetriever
            ↓
        RetrievedDocument
            ↓
        Evidence collection / validation
            ↓
        Citations
            ↓
        LLM synthesis
            ↓
        ResearchReport

    The service does not know anything about FastAPI.

    Providers are injected into the retrievers, keeping the domain
    layer independent from arXiv, GitHub, HTTP clients, databases,
    vector stores, and specific LLM providers.
    """

    def __init__(
        self,
        *,
        paper_retriever: Optional[PaperRetriever] = None,
        github_retriever: Optional[GitHubRetriever] = None,
        evidence_collector: Optional[Any] = None,
        evidence_validator: Optional[Any] = None,
        citation_generator: Optional[Any] = None,
        report_generator: Optional[Any] = None,
        llm_manager: Optional[Any] = None,
    ) -> None:
        self.paper_retriever = paper_retriever
        self.github_retriever = github_retriever

        self.evidence_collector = evidence_collector
        self.evidence_validator = evidence_validator
        self.citation_generator = citation_generator
        self.report_generator = report_generator

        self.llm_manager = llm_manager

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    async def research(
        self,
        query: ResearchQuery | str,
        *,
        max_papers: Optional[int] = None,
        max_github_results: Optional[int] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ResearchReport:
        """
        Execute the complete research workflow.

        Parameters
        ----------
        query:
            ResearchQuery or plain string.

        max_papers:
            Optional override for paper retrieval limit.

        max_github_results:
            Optional override for GitHub retrieval limit.

        context:
            Optional context supplied by the Assistant / frontend.

        Returns
        -------
        ResearchReport
            Canonical research report model.
        """

        research_query = self._normalize_query(query)

        logger.info(
            "Starting research",
            extra={
                "query": research_query.query,
                "depth": research_query.depth,
                "include_papers": research_query.include_papers,
                "include_github": research_query.include_github,
                "include_docs": research_query.include_docs,
            },
        )

        documents: list[RetrievedDocument] = []
        errors: list[str] = []

        # --------------------------------------------------------------
        # 1. RETRIEVE PAPERS
        # --------------------------------------------------------------

        if research_query.include_papers:
            if self.paper_retriever is None:
                logger.warning("No paper retriever configured")
            else:
                try:
                    papers = await self._retrieve_papers(
                        research_query,
                        max_results=max_papers,
                    )

                    documents.extend(papers)

                    logger.info(
                        "Paper retrieval completed",
                        extra={
                            "query": research_query.query,
                            "count": len(papers),
                        },
                    )

                except Exception as exc:
                    logger.exception("Paper retrieval failed")

                    errors.append(
                        f"Paper retrieval failed: {exc}"
                    )

        # --------------------------------------------------------------
        # 2. RETRIEVE GITHUB
        # --------------------------------------------------------------

        if research_query.include_github:
            if self.github_retriever is None:
                logger.warning("No GitHub retriever configured")
            else:
                try:
                    repositories = await self._retrieve_github(
                        research_query,
                        max_results=max_github_results,
                    )

                    documents.extend(repositories)

                    logger.info(
                        "GitHub retrieval completed",
                        extra={
                            "query": research_query.query,
                            "count": len(repositories),
                        },
                    )

                except Exception as exc:
                    logger.exception("GitHub retrieval failed")

                    errors.append(
                        f"GitHub retrieval failed: {exc}"
                    )

        # --------------------------------------------------------------
        # 3. DEDUPLICATE DOCUMENTS
        # --------------------------------------------------------------

        documents = self._deduplicate_documents(documents)

        # --------------------------------------------------------------
        # 4. EVIDENCE COLLECTION
        # --------------------------------------------------------------

        evidence: list[Evidence] = []

        if documents and self.evidence_collector is not None:
            try:
                evidence = await self._collect_evidence(
                    research_query,
                    documents,
                )
            except Exception as exc:
                logger.exception("Evidence collection failed")

                errors.append(
                    f"Evidence collection failed: {exc}"
                )

        # --------------------------------------------------------------
        # 5. EVIDENCE VALIDATION
        # --------------------------------------------------------------

        if evidence and self.evidence_validator is not None:
            try:
                evidence = await self._validate_evidence(
                    research_query,
                    evidence,
                    documents,
                )
            except Exception as exc:
                logger.exception("Evidence validation failed")

                errors.append(
                    f"Evidence validation failed: {exc}"
                )

        # --------------------------------------------------------------
        # 6. CITATIONS
        # --------------------------------------------------------------

        citations: list[Citation] = []

        if documents:
            try:
                citations = await self._generate_citations(
                    research_query,
                    documents,
                    evidence,
                )
            except Exception as exc:
                logger.exception("Citation generation failed")

                errors.append(
                    f"Citation generation failed: {exc}"
                )

        # --------------------------------------------------------------
        # 7. LLM SYNTHESIS
        # --------------------------------------------------------------

        if self.llm_manager is not None and documents:
            try:
                report = await self._generate_with_llm(
                    research_query,
                    documents,
                    evidence,
                    citations,
                    context=context,
                )

                if report is not None:
                    report.metadata.update(
                        self._build_metadata(
                            research_query,
                            documents,
                            evidence,
                            errors,
                            execution_mode="llm_research",
                        )
                    )

                    logger.info(
                        "Research completed using LLM",
                        extra={
                            "query": research_query.query,
                            "source_count": len(documents),
                        },
                    )

                    return report

            except Exception as exc:
                logger.exception(
                    "LLM research synthesis failed"
                )

                errors.append(
                    f"LLM synthesis failed: {exc}"
                )

        # --------------------------------------------------------------
        # 8. REPORT GENERATOR
        # --------------------------------------------------------------

        if self.report_generator is not None:
            try:
                report = await self._generate_report(
                    research_query,
                    documents,
                    evidence,
                    citations,
                    errors,
                )

                if report is not None:
                    report.metadata.update(
                        self._build_metadata(
                            research_query,
                            documents,
                            evidence,
                            errors,
                            execution_mode="report_generator",
                        )
                    )

                    return report

            except Exception as exc:
                logger.exception("Report generation failed")

                errors.append(
                    f"Report generation failed: {exc}"
                )

        # --------------------------------------------------------------
        # 9. SAFE FALLBACK
        # --------------------------------------------------------------

        return self._fallback_report(
            research_query,
            documents,
            evidence,
            citations,
            errors,
        )

    # ==================================================================
    # QUERY NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_query(
        query: ResearchQuery | str,
    ) -> ResearchQuery:

        if isinstance(query, ResearchQuery):
            return query

        if not isinstance(query, str):
            raise TypeError(
                "query must be ResearchQuery or str"
            )

        value = query.strip()

        if not value:
            raise ValueError(
                "research query cannot be empty"
            )

        return ResearchQuery(
            query=value,
        )

    # ==================================================================
    # PAPER RETRIEVAL
    # ==================================================================

    async def _retrieve_papers(
        self,
        query: ResearchQuery,
        *,
        max_results: Optional[int],
    ) -> list[RetrievedDocument]:

        retriever = self.paper_retriever

        if retriever is None:
            return []

        if max_results is None:
            result = retriever.retrieve(query)

        else:
            # The current PaperRetriever.retrieve() uses its configured
            # top_k. We therefore temporarily respect the existing
            # retriever configuration rather than changing its contract.
            result = retriever.retrieve(query)

            if max_results > 0:
                result = result[:max_results]

        if inspect.isawaitable(result):
            result = await result

        return list(result or [])

    # ==================================================================
    # GITHUB RETRIEVAL
    # ==================================================================

    async def _retrieve_github(
        self,
        query: ResearchQuery,
        *,
        max_results: Optional[int],
    ) -> list[RetrievedDocument]:

        retriever = self.github_retriever

        if retriever is None:
            return []

        result = retriever.retrieve(query)

        if inspect.isawaitable(result):
            result = await result

        documents = list(result or [])

        if max_results is not None and max_results > 0:
            documents = documents[:max_results]

        return documents

    # ==================================================================
    # DEDUPLICATION
    # ==================================================================

    @staticmethod
    def _deduplicate_documents(
        documents: Sequence[RetrievedDocument],
    ) -> list[RetrievedDocument]:

        result: list[RetrievedDocument] = []
        seen: set[str] = set()

        for document in documents:
            source = document.source

            if source.url:
                key = (
                    "url:"
                    + source.url.strip().lower()
                )
            else:
                key = (
                    f"{source.source_type}:"
                    + " ".join(
                        source.title.strip().lower().split()
                    )
                )

            if key in seen:
                continue

            seen.add(key)
            result.append(document)

        return result

    # ==================================================================
    # EVIDENCE COLLECTION
    # ==================================================================

    async def _collect_evidence(
        self,
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
    ) -> list[Evidence]:

        collector = self.evidence_collector

        if collector is None:
            return []

        if not hasattr(collector, "collect"):
            raise AttributeError(
                "EvidenceCollector must implement collect()"
            )

        method = collector.collect

        try:
            result = method(
                query=query,
                documents=documents,
            )
        except TypeError:
            result = method(
                query,
                documents,
            )

        if inspect.isawaitable(result):
            result = await result

        return self._coerce_list(
            result,
            Evidence,
        )

    # ==================================================================
    # EVIDENCE VALIDATION
    # ==================================================================

    async def _validate_evidence(
        self,
        query: ResearchQuery,
        evidence: Sequence[Evidence],
        documents: Sequence[RetrievedDocument],
    ) -> list[Evidence]:

        validator = self.evidence_validator

        if validator is None:
            return list(evidence)

        if not hasattr(validator, "validate"):
            raise AttributeError(
                "EvidenceValidator must implement validate()"
            )

        method = validator.validate

        try:
            result = method(
                query=query,
                evidence=evidence,
                documents=documents,
            )
        except TypeError:
            try:
                result = method(
                    query=query,
                    evidence=evidence,
                )
            except TypeError:
                result = method(evidence)

        if inspect.isawaitable(result):
            result = await result

        return self._coerce_list(
            result,
            Evidence,
        )

    # ==================================================================
    # CITATION GENERATION
    # ==================================================================

    async def _generate_citations(
        self,
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
    ) -> list[Citation]:

        generator = self.citation_generator

        if generator is None:
            return self._build_basic_citations(documents)

        if not hasattr(generator, "generate"):
            raise AttributeError(
                "CitationGenerator must implement generate()"
            )

        method = generator.generate

        try:
            result = method(
                query=query,
                documents=documents,
                evidence=evidence,
            )
        except TypeError:
            try:
                result = method(
                    documents=documents,
                )
            except TypeError:
                result = method(documents)

        if inspect.isawaitable(result):
            result = await result

        return self._coerce_list(
            result,
            Citation,
        )

    # ==================================================================
    # LLM SYNTHESIS
    # ==================================================================

    async def _generate_with_llm(
        self,
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
        citations: Sequence[Citation],
        *,
        context: Optional[Mapping[str, Any]],
    ) -> Optional[ResearchReport]:

        if self.llm_manager is None:
            return None

        prompt = self._build_research_prompt(
            query=query,
            documents=documents,
            evidence=evidence,
            citations=citations,
            context=context,
        )

        response = await self._call_llm(
            prompt,
        )

        if response is None:
            return None

        text = self._extract_llm_text(response)

        if not text:
            return None

        return self._convert_llm_response_to_report(
            query=query,
            text=text,
            documents=documents,
            evidence=evidence,
            citations=citations,
        )

    async def _call_llm(
        self,
        prompt: str,
    ) -> Any:

        manager = self.llm_manager

        if manager is None:
            return None

        # Existing project convention:
        # LLMManager.chat(...)
        if hasattr(manager, "chat"):
            method = manager.chat

        elif hasattr(manager, "generate"):
            method = manager.generate

        elif hasattr(manager, "complete"):
            method = manager.complete

        else:
            raise AttributeError(
                "LLM manager must implement chat(), generate(), "
                "or complete()"
            )

        # First try the simplest contract.
        try:
            result = method(prompt)
        except TypeError:
            # Some managers use messages=...
            result = method(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            )

        if inspect.isawaitable(result):
            result = await result

        return result

    # ==================================================================
    # PROMPT
    # ==================================================================

    @staticmethod
    def _build_research_prompt(
        *,
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
        citations: Sequence[Citation],
        context: Optional[Mapping[str, Any]],
    ) -> str:

        source_blocks: list[str] = []

        for index, document in enumerate(
            documents,
            start=1,
        ):
            source = document.source

            source_blocks.append(
                "\n".join(
                    [
                        f"[SOURCE {index}]",
                        f"Title: {source.title}",
                        f"Type: {source.source_type}",
                        f"URL: {source.url or 'N/A'}",
                        f"Authors: {', '.join(source.authors) or 'N/A'}",
                        f"Score: {document.score}",
                        f"Content:\n{document.text}",
                    ]
                )
            )

        evidence_blocks: list[str] = []

        for item in evidence:
            evidence_blocks.append(
                "\n".join(
                    [
                        f"[EVIDENCE {item.id}]",
                        f"Claim: {item.claim}",
                        f"Supporting text: {item.supporting_text}",
                        f"Source ID: {item.source_id}",
                        f"Confidence: {item.confidence}",
                        f"Relevance: {item.relevance_score}",
                    ]
                )
            )

        citation_blocks = [
            (
                f"[{citation.id}] "
                f"{citation.citation_text}"
            )
            for citation in citations
        ]

        return f"""
You are the research synthesis engine for an AI Research Assistant.

Research question:
{query.query}

Research depth:
{query.depth}

Additional context:
{dict(context or {})}

SOURCE MATERIAL
===============

{chr(10).join(source_blocks) or "No source material available."}

VALIDATED EVIDENCE
==================

{chr(10).join(evidence_blocks) or "No validated evidence available."}

CITATIONS
=========

{chr(10).join(citation_blocks) or "No citations available."}

INSTRUCTIONS
============

Produce a rigorous research report answering the research question.

Rules:

1. Use only the supplied source material and validated evidence.
2. Do not invent papers, repositories, authors, statistics, or claims.
3. Clearly distinguish established findings from interpretation.
4. Mention uncertainty when evidence is weak or conflicting.
5. Prefer primary academic sources when available.
6. Use GitHub sources primarily for implementation evidence.
7. Do not treat GitHub popularity as scientific evidence.
8. Include citations for source-supported claims.
9. Do not claim that a source says something unless its supplied
   content supports that claim.
10. Keep the answer focused on the research question.

Return the report using this structure:

## Executive Summary

A concise synthesis of the most important findings.

## Key Findings

The major evidence-supported findings.

## Research Analysis

Detailed analysis and comparison of the evidence.

## Limitations

Important limitations, uncertainty, missing evidence, or conflicts.

## Sources

List the supplied sources used in the analysis.
""".strip()

    # ==================================================================
    # LLM RESPONSE NORMALIZATION
    # ==================================================================

    @staticmethod
    def _extract_llm_text(
        response: Any,
    ) -> str:

        if response is None:
            return ""

        if isinstance(response, str):
            return response.strip()

        if isinstance(response, Mapping):

            for key in (
                "content",
                "text",
                "response",
                "answer",
                "message",
                "output",
            ):
                value = response.get(key)

                if isinstance(value, str):
                    return value.strip()

                if isinstance(value, Mapping):
                    nested = value.get("content")

                    if isinstance(nested, str):
                        return nested.strip()

        for attribute in (
            "content",
            "text",
            "response",
            "answer",
            "output",
        ):
            value = getattr(
                response,
                attribute,
                None,
            )

            if isinstance(value, str):
                return value.strip()

        return str(response).strip()

    # ==================================================================
    # LLM → RESEARCH REPORT
    # ==================================================================

    @staticmethod
    def _convert_llm_response_to_report(
        *,
        query: ResearchQuery,
        text: str,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
        citations: Sequence[Citation],
    ) -> ResearchReport:

        summary = ResearchService._extract_section(
            text,
            "Executive Summary",
        )

        findings = ResearchService._extract_section(
            text,
            "Key Findings",
        )

        analysis = ResearchService._extract_section(
            text,
            "Research Analysis",
        )

        limitations = ResearchService._extract_section(
            text,
            "Limitations",
        )

        sections: list[ResearchSection] = []

        if findings:
            sections.append(
                ResearchSection(
                    title="Key Findings",
                    content=findings,
                    evidence_ids=[
                        item.id
                        for item in evidence
                    ],
                )
            )

        if analysis:
            sections.append(
                ResearchSection(
                    title="Research Analysis",
                    content=analysis,
                    evidence_ids=[
                        item.id
                        for item in evidence
                    ],
                )
            )

        if limitations:
            sections.append(
                ResearchSection(
                    title="Limitations",
                    content=limitations,
                    evidence_ids=[
                        item.id
                        for item in evidence
                    ],
                )
            )

        if not summary:
            summary = text[:2000]

        sources = [
            document.source
            for document in documents
        ]

        return ResearchReport(
            title=f"Research Report: {query.query}",
            summary=summary,
            sections=sections,
            citations=list(citations),
            evidence=list(evidence),
            sources=sources,
            metadata={
                "query": query.query,
                "depth": query.depth,
                "source_count": len(documents),
                "paper_count": sum(
                    1
                    for document in documents
                    if document.source.source_type
                    == "paper"
                ),
                "github_result_count": sum(
                    1
                    for document in documents
                    if document.source.source_type
                    == "github"
                ),
                "execution_mode": "llm_research",
            },
            status=(
                "completed"
                if documents
                else "partial"
            ),
        )

    @staticmethod
    def _extract_section(
        text: str,
        heading: str,
    ) -> str:

        lines = text.splitlines()

        start: Optional[int] = None

        for index, line in enumerate(lines):
            normalized = line.strip().lower()

            if normalized in {
                f"## {heading}".lower(),
                f"### {heading}".lower(),
                heading.lower(),
            }:
                start = index + 1
                break

        if start is None:
            return ""

        content: list[str] = []

        for line in lines[start:]:
            stripped = line.strip()

            if stripped.startswith("#"):
                break

            content.append(line)

        return "\n".join(content).strip()

    # ==================================================================
    # REPORT GENERATOR
    # ==================================================================

    async def _generate_report(
        self,
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
        citations: Sequence[Citation],
        errors: Sequence[str],
    ) -> Optional[ResearchReport]:

        generator = self.report_generator

        if generator is None:
            return None

        if not hasattr(generator, "generate"):
            raise AttributeError(
                "ReportGenerator must implement generate()"
            )

        method = generator.generate

        try:
            result = method(
                query=query,
                documents=documents,
                evidence=evidence,
                citations=citations,
            )
        except TypeError:
            result = method(
                query,
                documents,
                evidence,
                citations,
            )

        if inspect.isawaitable(result):
            result = await result

        if isinstance(result, ResearchReport):
            return result

        if isinstance(result, Mapping):
            return ResearchReport.model_validate(
                result
            )

        return None

    # ==================================================================
    # FALLBACK
    # ==================================================================

    @staticmethod
    def _fallback_report(
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
        citations: Sequence[Citation],
        errors: Sequence[str],
    ) -> ResearchReport:

        if documents:
            summary = (
                "Research sources were retrieved, but no "
                "research synthesis engine was available."
            )

            status = "partial"

        else:
            summary = (
                "No external sources were retrieved for the "
                f"research question: {query.query}. "
                "Configure paper/GitHub search providers and "
                "an LLM research execution engine."
            )

            status = "partial"

        return ResearchReport(
            title=f"Research Report: {query.query}",
            summary=summary,
            sections=[],
            citations=list(citations),
            evidence=list(evidence),
            sources=[
                document.source
                for document in documents
            ],
            metadata={
                "query": query.query,
                "depth": query.depth,
                "source_count": len(documents),
                "paper_count": sum(
                    1
                    for document in documents
                    if document.source.source_type
                    == "paper"
                ),
                "github_result_count": sum(
                    1
                    for document in documents
                    if document.source.source_type
                    == "github"
                ),
                "execution_mode": "retrieval_only",
                "errors": list(errors),
            },
            status=status,
        )

    # ==================================================================
    # BASIC CITATIONS
    # ==================================================================

    @staticmethod
    def _build_basic_citations(
        documents: Sequence[RetrievedDocument],
    ) -> list[Citation]:

        citations: list[Citation] = []

        for index, document in enumerate(
            documents,
            start=1,
        ):
            source = document.source

            year = source.metadata.get("year")

            try:
                year = int(year) if year is not None else None
            except (TypeError, ValueError):
                year = None

            authors = list(source.authors)

            if authors:
                author_text = ", ".join(authors)
            else:
                author_text = "Unknown author"

            citation_text = (
                f"{author_text}. "
                f"{source.title}."
            )

            if year:
                citation_text += f" ({year})."

            if source.url:
                citation_text += f" {source.url}"

            citations.append(
                Citation(
                    id=f"citation-{index}",
                    source_id=source.id,
                    title=source.title,
                    authors=authors,
                    year=year,
                    citation_text=citation_text,
                    url=source.url,
                )
            )

        return citations

    # ==================================================================
    # METADATA
    # ==================================================================

    @staticmethod
    def _build_metadata(
        query: ResearchQuery,
        documents: Sequence[RetrievedDocument],
        evidence: Sequence[Evidence],
        errors: Sequence[str],
        *,
        execution_mode: str,
    ) -> dict[str, Any]:

        return {
            "query": query.query,
            "depth": query.depth,
            "source_count": len(documents),
            "paper_count": sum(
                1
                for document in documents
                if document.source.source_type
                == "paper"
            ),
            "github_result_count": sum(
                1
                for document in documents
                if document.source.source_type
                == "github"
            ),
            "evidence_count": len(evidence),
            "execution_mode": execution_mode,
            "errors": list(errors),
        }

    # ==================================================================
    # GENERIC MODEL COERCION
    # ==================================================================

    @staticmethod
    def _coerce_list(
        value: Any,
        model_type: type,
    ) -> list[Any]:

        if value is None:
            return []

        if isinstance(value, model_type):
            return [value]

        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes),
        ):
            values = value
        else:
            values = [value]

        result: list[Any] = []

        for item in values:
            if isinstance(item, model_type):
                result.append(item)

            elif isinstance(item, Mapping):
                try:
                    result.append(
                        model_type.model_validate(item)
                    )
                except Exception:
                    logger.warning(
                        "Skipping invalid %s result",
                        model_type.__name__,
                        exc_info=True,
                    )

        return result

