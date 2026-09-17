from __future__ import annotations

import inspect
import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.llm.pipeline import LLMPipeline, get_llm_pipeline
from app.retrieval.service import RetrievalService

from app.research.models import (
    Citation,
    ComparisonResult,
    Evidence,
    ResearchQuery,
    ResearchReport,
    ResearchSection,
    ResearchSource,
)
from app.research.planner import ResearchPlanner
from app.research.retrieval.github_retriever import GitHubRetriever
from app.research.retrieval.paper_retriever import PaperRetriever


logger = logging.getLogger(__name__)


# ============================================================================
# RESEARCH PIPELINE
# ============================================================================


class ResearchPipeline:
    """
    Main orchestration layer for the research system.

    The pipeline is responsible for:

        ResearchQuery
            |
            v
        ResearchPlanner
            |
            v
        RetrievalService
            |
            v
        Relevance filtering
            |
            +---- Knowledge-base evidence
            +---- PostgreSQL papers
            +---- GitHub
            |
            v
        LLMPipeline
            |
            v
        ResearchReport

    IMPORTANT:

    RetrievalService is a generic retrieval layer. It intentionally does not
    know whether a query belongs to the Research experience, Explore, or
    another application feature.

    Therefore research-specific relevance validation happens HERE.

    This prevents a semantically-near but actually unrelated document from
    becoming research evidence merely because it was the best available
    document in the index.

    Example:

        Query:
            "what you know about bert"

        Indexed paper:
            "Attention Is All You Need"

    If the retrieved Attention paper contains no meaningful BERT evidence,
    the result is rejected and is NOT sent to the LLM.

    This is critical for research grounding.

    RERANKING:

    CrossEncoder reranking is optional and environment-controlled.

    The application may run with:

        ENABLE_CROSS_ENCODER_RERANKING=false

    on constrained infrastructure such as a 512 MB Render instance.

    In that mode the research pipeline still performs:

        Dense retrieval
        BM25 retrieval
        Hybrid/RRF ranking
        Research-specific relevance filtering
        Paper retrieval
        GitHub retrieval
        LLM synthesis

    The CrossEncoder remains available and can be enabled explicitly in an
    environment with sufficient memory.
    """

    # ------------------------------------------------------------------------
    # Retrieval configuration
    # ------------------------------------------------------------------------

    TOP_K_BY_DEPTH: Dict[str, int] = {
        "basic": 8,
        "medium": 12,
        "deep": 20,
    }

    MIN_CANDIDATE_POOL = 50
    MAX_CANDIDATE_POOL = 100

    # ------------------------------------------------------------------------
    # Research-query stop words.
    #
    # These are intentionally broader than normal English stop words because
    # conversational query terms such as "what", "know", "tell", "explain"
    # are not useful evidence anchors.
    #
    # Technical terms are NOT included here.
    # ------------------------------------------------------------------------

    QUERY_STOP_WORDS: Set[str] = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "can",
        "could",
        "do",
        "does",
        "did",
        "for",
        "from",
        "give",
        "has",
        "have",
        "how",
        "i",
        "in",
        "information",
        "is",
        "it",
        "its",
        "me",
        "of",
        "on",
        "or",
        "please",
        "tell",
        "that",
        "the",
        "their",
        "them",
        "there",
        "these",
        "this",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "would",
        "you",
        "your",
        "about",
        "know",
        "explain",
        "describe",
        "discuss",
        "something",
        "anything",
    }

    QUERY_TOKEN_PATTERN = re.compile(
        r"[A-Za-z0-9][A-Za-z0-9_.+\-/#]*"
    )

    def __init__(
        self,
        planner: Optional[ResearchPlanner] = None,
        paper_retriever: Optional[PaperRetriever] = None,
        github_retriever: Optional[GitHubRetriever] = None,
        retrieval_service: Optional[RetrievalService] = None,
        llm_pipeline: Optional[LLMPipeline] = None,
        execution_engine: Optional[Any] = None,
    ) -> None:

        self.planner = planner or ResearchPlanner()

        self.paper_retriever = paper_retriever or PaperRetriever(
            session_factory=AsyncSessionLocal,
        )

        self.github_retriever = github_retriever or GitHubRetriever()

        self.retrieval_service = retrieval_service

        self.llm_pipeline = llm_pipeline or get_llm_pipeline()

        self.execution_engine = execution_engine

        self.enable_reranking = bool(
            getattr(
                settings,
                "ENABLE_CROSS_ENCODER_RERANKING",
                False,
            )
        )

        logger.info(
            "ResearchPipeline initialized: "
            "retrieval_service=%s "
            "llm_pipeline=%s "
            "execution_engine=%s "
            "cross_encoder_reranking=%s",
            self.retrieval_service is not None,
            self.llm_pipeline is not None,
            self.execution_engine is not None,
            self.enable_reranking,
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def run(
        self,
        query: ResearchQuery,
        *,
        execution_engine: Optional[Any] = None,
        allowed_document_ids: Optional[List[str]] = None,
    ) -> ResearchReport:

        started_at = datetime.now(timezone.utc)

        logger.info(
            "Starting research pipeline for question=%r",
            getattr(query, "question", None),
        )

        try:
            self._validate_query(query)

            logger.info(
                "Creating research plan for question: %s",
                query.question,
            )

            execution_plan = await self._create_plan(query)

            logger.info("Research plan created successfully")

            retrieval_context = await self._retrieve_context(
                query=query,
                allowed_document_ids=allowed_document_ids,
            )

            logger.info(
                "Research retrieval completed: "
                "documentation=%s papers=%s github=%s",
                len(retrieval_context.get("documentation", []) or []),
                len(retrieval_context.get("papers", []) or []),
                len(retrieval_context.get("github", []) or []),
            )

            engine = (
                execution_engine
                if execution_engine is not None
                else self.execution_engine
            )

            execution_result = await self._execute_plan(
                query=query,
                execution_plan=execution_plan,
                retrieval_context=retrieval_context,
                execution_engine=engine,
            )

            report = self._build_report(
                query=query,
                execution_plan=execution_plan,
                execution_result=execution_result,
                retrieval_context=retrieval_context,
                started_at=started_at,
            )

            logger.info(
                "Research pipeline completed: "
                "status=%s sources=%s evidence=%s citations=%s",
                report.status,
                len(report.sources),
                len(report.evidence),
                len(report.citations),
            )

            return report

        except Exception:
            logger.exception("Research pipeline failed")
            raise

    # ========================================================================
    # PLANNING
    # ========================================================================

    async def _create_plan(
        self,
        query: ResearchQuery,
    ) -> Any:

        planner = self.planner

        if planner is None:
            raise RuntimeError(
                "Research planner is not configured."
            )

        if hasattr(planner, "create_plan"):
            result = planner.create_plan(query)
            return await self._resolve_awaitable(result)

        if hasattr(planner, "plan"):
            result = planner.plan(query)
            return await self._resolve_awaitable(result)

        if callable(planner):
            result = planner(query)
            return await self._resolve_awaitable(result)

        raise AttributeError(
            "ResearchPlanner must expose "
            "`create_plan()`, `plan()`, or be callable."
        )

    # ========================================================================
    # RETRIEVAL
    # ========================================================================

    async def _retrieve_context(
        self,
        query: ResearchQuery,
        *,
        allowed_document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        context: Dict[str, Any] = {
            "papers": [],
            "github": [],
            "documentation": [],
        }

        if allowed_document_ids:
            logger.info(
                "Research retrieval is collection-scoped: "
                "allowed_documents=%d",
                len(allowed_document_ids),
            )
        else:
            logger.info(
                "Research retrieval is not collection-scoped."
            )

        # ====================================================================
        # 1. KNOWLEDGE BASE
        # ====================================================================

        include_docs = getattr(
            query,
            "include_docs",
            True,
        )

        if include_docs:
            if self.retrieval_service is None:
                logger.warning(
                    "Knowledge-base retrieval was requested, but "
                    "RetrievalService is not configured."
                )
            else:
                try:
                    documentation = await self._retrieve_knowledge_base(
                        query,
                        allowed_document_ids=allowed_document_ids,
                    )

                    context["documentation"] = (
                        self._normalize_collection(
                            documentation
                        )
                    )

                    logger.info(
                        "Knowledge-base retrieval returned %d "
                        "RELEVANT result(s)",
                        len(context["documentation"]),
                    )

                except Exception as exc:
                    logger.warning(
                        "Knowledge-base retrieval failed: %s",
                        exc,
                        exc_info=True,
                    )

        # ====================================================================
        # 2. PAPERS
        # ====================================================================

        include_papers = getattr(
            query,
            "include_papers",
            True,
        )

        if include_papers:
            try:
                if self.paper_retriever is not None:
                    papers = await self._run_retriever(
                        self.paper_retriever,
                        query,
                    )

                    context["papers"] = self._normalize_collection(
                        papers
                    )

                    logger.info(
                        "Paper retrieval returned %d result(s)",
                        len(context["papers"]),
                    )

            except Exception as exc:
                logger.warning(
                    "Paper retrieval failed: %s",
                    exc,
                    exc_info=True,
                )

        # ====================================================================
        # 3. GITHUB
        # ====================================================================

        include_github = getattr(
            query,
            "include_github",
            True,
        )

        if include_github:
            try:
                if self.github_retriever is not None:
                    github_results = await self._run_retriever(
                        self.github_retriever,
                        query,
                    )

                    context["github"] = self._normalize_collection(
                        github_results
                    )

                    logger.info(
                        "GitHub retrieval returned %d result(s)",
                        len(context["github"]),
                    )

            except Exception as exc:
                logger.warning(
                    "GitHub retrieval failed: %s",
                    exc,
                    exc_info=True,
                )

        return context

    # ========================================================================
    # KNOWLEDGE-BASE RETRIEVAL + RELEVANCE GATE
    # ========================================================================

    async def _retrieve_knowledge_base(
        self,
        query: ResearchQuery,
        *,
        allowed_document_ids: Optional[List[str]] = None,
    ) -> List[Any]:

        if self.retrieval_service is None:
            return []

        depth = getattr(
            query,
            "depth",
            "medium",
        )

        depth_name = str(depth).lower()

        top_k = self.TOP_K_BY_DEPTH.get(
            depth_name,
            self.TOP_K_BY_DEPTH["medium"],
        )

        # Always retrieve a larger candidate pool.
        #
        # Candidate pool -> document filtering -> relevance filtering
        # -> final top_k.
        #
        # This remains useful even when CrossEncoder reranking is disabled,
        # because the research-specific lexical relevance gate provides an
        # additional grounding layer.

        candidate_top_k = min(
            max(top_k * 5, self.MIN_CANDIDATE_POOL),
            self.MAX_CANDIDATE_POOL,
        )

        logger.info(
            "Retrieving knowledge-base candidates: "
            "question=%r top_k=%s candidate_top_k=%s depth=%s scoped=%s "
            "cross_encoder_reranking=%s",
            query.question,
            top_k,
            candidate_top_k,
            depth,
            bool(allowed_document_ids),
            self.enable_reranking,
        )

        result = await self._retrieve_with_reranking(
            query=query.question,
            top_k=candidate_top_k,
        )

        results = self._extract_retrieval_results(
            result
        )

        logger.info(
            "Knowledge-base candidate retrieval returned %d result(s)",
            len(results),
        )

        # --------------------------------------------------------------------
        # Collection restriction
        # --------------------------------------------------------------------

        if allowed_document_ids:
            allowed_ids = {
                str(document_id).strip()
                for document_id in allowed_document_ids
                if document_id is not None
                and str(document_id).strip()
            }

            if not allowed_ids:
                logger.warning(
                    "Collection scope was provided but contained no "
                    "usable document IDs."
                )
                return []

            results = self._filter_by_document_ids(
                results,
                allowed_ids,
            )

            logger.info(
                "Collection filtering left %d candidate(s)",
                len(results),
            )

        # --------------------------------------------------------------------
        # Research relevance gate
        # --------------------------------------------------------------------

        relevant_results = self._filter_relevant_results(
            query=query.question,
            results=results,
        )

        logger.info(
            "Research relevance filtering: "
            "candidates=%d relevant=%d rejected=%d final_top_k=%d",
            len(results),
            len(relevant_results),
            max(0, len(results) - len(relevant_results)),
            top_k,
        )

        return relevant_results[:top_k]

    async def _retrieve_with_reranking(
        self,
        *,
        query: str,
        top_k: int,
    ) -> Any:
        """
        Call RetrievalService while remaining compatible with versions of the
        service that expose slightly different signatures.

        CrossEncoder reranking is controlled by:

            settings.ENABLE_CROSS_ENCODER_RERANKING

        On memory-constrained infrastructure this should be false.

        This means the retrieval pipeline still performs its normal hybrid
        retrieval, while avoiding loading the CrossEncoder/PyTorch model.

        Explicit reranking can still be enabled in a larger environment.
        """

        if self.retrieval_service is None:
            return []

        retrieve_method = self.retrieval_service.retrieve

        enable_reranking = self.enable_reranking

        logger.info(
            "Research retrieval request: "
            "top_k=%d mode=hybrid enable_reranking=%s",
            top_k,
            enable_reranking,
        )

        # --------------------------------------------------------------------
        # Canonical modern signature.
        #
        # IMPORTANT:
        #
        # Do NOT hard-code True here.
        #
        # Previously this was:
        #
        #     enable_reranking=True
        #
        # which forced the BAAI/bge-reranker-base CrossEncoder onto Render
        # even when the deployment was supposed to be memory-safe.
        # --------------------------------------------------------------------

        try:
            return await self._resolve_awaitable(
                retrieve_method(
                    query,
                    top_k=top_k,
                    enable_reranking=enable_reranking,
                    mode="hybrid",
                )
            )

        except TypeError:
            logger.debug(
                "RetrievalService does not accept all research retrieval "
                "options; falling back to compatible signature.",
                exc_info=True,
            )

        # --------------------------------------------------------------------
        # Second compatibility path.
        # --------------------------------------------------------------------

        try:
            return await self._resolve_awaitable(
                retrieve_method(
                    query,
                    top_k=top_k,
                    enable_reranking=enable_reranking,
                )
            )

        except TypeError:
            logger.debug(
                "RetrievalService does not accept enable_reranking; "
                "falling back to top_k-only retrieval.",
                exc_info=True,
            )

        # --------------------------------------------------------------------
        # Final compatibility path.
        #
        # This is intentionally only reached for older RetrievalService
        # implementations that do not accept the reranking argument.
        # --------------------------------------------------------------------

        return await self._resolve_awaitable(
            retrieve_method(
                query,
                top_k=top_k,
            )
        )

    def _filter_relevant_results(
        self,
        *,
        query: str,
        results: Sequence[Any],
    ) -> List[Any]:
        """
        Research-specific relevance gate.

        This is deliberately stricter than generic retrieval.

        A generic vector search always returns its nearest neighbours, even
        when the query is outside the indexed corpus.

        For research, that behaviour is unsafe because "nearest" does not
        mean "evidence".

        The gate therefore looks for meaningful query anchors in:

            - chunk content
            - title
            - metadata
            - paper metadata

        A reranker score is used as a supporting signal when available, but
        it is NOT required.

        This means research grounding continues to work when the CrossEncoder
        is disabled for memory-constrained deployments.

        Example:

            query = "what you know about bert"

        meaningful token:
            bert

        Attention Is All You Need chunk:
            no "bert"

        => rejected
        """

        if not results:
            return []

        query_tokens = self._research_query_tokens(
            query
        )

        if not query_tokens:
            logger.warning(
                "Research relevance gate found no meaningful query tokens "
                "for query=%r; preserving retrieval results.",
                query,
            )
            return list(results)

        accepted: List[Any] = []

        for index, item in enumerate(results):
            if item is None:
                continue

            relevance = self._calculate_research_relevance(
                query=query,
                query_tokens=query_tokens,
                item=item,
            )

            metadata = self._item_metadata(item)

            metadata["research_relevance_score"] = relevance

            self._attach_metadata(
                item,
                {
                    "research_relevance_score": relevance,
                },
            )

            if relevance > 0.0:
                accepted.append(item)

                logger.debug(
                    "Research relevance ACCEPTED: rank=%d score=%.4f "
                    "title=%r",
                    index + 1,
                    relevance,
                    self._item_title(
                        item,
                        fallback="Unknown source",
                    ),
                )

            else:
                logger.debug(
                    "Research relevance REJECTED: rank=%d title=%r "
                    "query=%r",
                    index + 1,
                    self._item_title(
                        item,
                        fallback="Unknown source",
                    ),
                    query,
                )

        return accepted

    @classmethod
    def _research_query_tokens(
        cls,
        query: str,
    ) -> Set[str]:

        raw_tokens = cls.QUERY_TOKEN_PATTERN.findall(
            str(query).lower()
        )

        tokens: Set[str] = set()

        for token in raw_tokens:
            normalized = token.strip(
                "._+-/#"
            )

            if not normalized:
                continue

            if normalized in cls.QUERY_STOP_WORDS:
                continue

            if len(normalized) < 2:
                continue

            tokens.add(normalized)

        return tokens

    def _calculate_research_relevance(
        self,
        *,
        query: str,
        query_tokens: Set[str],
        item: Any,
    ) -> float:

        content = self._item_content(item)

        title = self._item_title(
            item,
            fallback="",
        )

        metadata = self._item_metadata(item)

        metadata_text_parts: List[str] = []

        for key in (
            "title",
            "paper_title",
            "document_title",
            "name",
            "source",
            "repository",
            "arxiv_id",
            "doi",
            "authors",
        ):
            value = metadata.get(key)

            if value is None:
                continue

            if isinstance(value, (list, tuple, set)):
                metadata_text_parts.extend(
                    str(value_item)
                    for value_item in value
                )
            else:
                metadata_text_parts.append(
                    str(value)
                )

        searchable_text = " ".join(
            [
                str(title),
                str(content),
                *metadata_text_parts,
            ]
        ).lower()

        if not searchable_text.strip():
            return 0.0

        matched_tokens: Set[str] = set()

        for token in query_tokens:
            if self._token_present(
                token,
                searchable_text,
            ):
                matched_tokens.add(token)

        if not matched_tokens:
            return 0.0

        coverage = (
            len(matched_tokens)
            / max(1, len(query_tokens))
        )

        normalized_query = self._normalize_text(
            query
        )

        normalized_content = self._normalize_text(
            f"{title} {content}"
        )

        phrase_match = (
            1.0
            if normalized_query
            and normalized_query in normalized_content
            else 0.0
        )

        rerank_score = self._extract_score(
            item,
            "rerank_score",
        )

        if rerank_score is None:
            rerank_score = self._extract_score(
                item,
                "score",
            )

        normalized_rank_score = None

        if rerank_score is not None:
            if 0.0 <= rerank_score <= 1.0:
                normalized_rank_score = rerank_score

        if normalized_rank_score is None:
            normalized_rank_score = 0.0

        relevance = 0.75 * coverage

        if phrase_match:
            relevance += 0.15

        relevance += 0.10 * normalized_rank_score

        return self._clamp(
            relevance,
            0.0,
            1.0,
        )

    @staticmethod
    def _token_present(
        token: str,
        text: str,
    ) -> bool:

        escaped = re.escape(
            token.lower()
        )

        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"

        return re.search(
            pattern,
            text.lower(),
        ) is not None

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:

        text = str(
            value or ""
        ).lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _extract_score(
        item: Any,
        field: str,
    ) -> Optional[float]:

        if item is None:
            return None

        candidates: List[Any] = []

        if isinstance(item, dict):
            candidates.append(
                item.get(field)
            )

            metadata = item.get(
                "metadata",
                {},
            )

            if isinstance(metadata, dict):
                candidates.append(
                    metadata.get(field)
                )

            document = item.get(
                "document"
            )

            if isinstance(document, dict):
                candidates.append(
                    document.get(field)
                )

                document_metadata = document.get(
                    "metadata",
                    {},
                )

                if isinstance(
                    document_metadata,
                    dict,
                ):
                    candidates.append(
                        document_metadata.get(field)
                    )

        else:
            candidates.append(
                getattr(
                    item,
                    field,
                    None,
                )
            )

            metadata = getattr(
                item,
                "metadata",
                {},
            )

            if isinstance(metadata, dict):
                candidates.append(
                    metadata.get(field)
                )

            document = getattr(
                item,
                "document",
                None,
            )

            if document is not None:
                candidates.append(
                    getattr(
                        document,
                        field,
                        None,
                    )
                )

                document_metadata = getattr(
                    document,
                    "metadata",
                    {},
                )

                if isinstance(
                    document_metadata,
                    dict,
                ):
                    candidates.append(
                        document_metadata.get(field)
                    )

        for candidate in candidates:
            if candidate is None:
                continue

            try:
                value = float(candidate)

                if math.isfinite(value):
                    return value

            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

    @staticmethod
    def _attach_metadata(
        item: Any,
        values: Dict[str, Any],
    ) -> None:

        if item is None:
            return

        if isinstance(item, dict):
            metadata = item.get(
                "metadata"
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            metadata.update(values)
            item["metadata"] = metadata
            return

        metadata = getattr(
            item,
            "metadata",
            None,
        )

        if isinstance(
            metadata,
            dict,
        ):
            metadata.update(values)
            return

        try:
            setattr(
                item,
                "metadata",
                dict(values),
            )
        except Exception:
            logger.debug(
                "Could not attach research metadata to %s.",
                type(item).__name__,
                exc_info=True,
            )

    # ========================================================================
    # COLLECTION FILTERING
    # ========================================================================

    @staticmethod
    def _filter_by_document_ids(
        results: List[Any],
        allowed_document_ids: Set[str],
    ) -> List[Any]:

        filtered: List[Any] = []

        for item in results:
            if item is None:
                continue

            metadata = ResearchPipeline._item_metadata(
                item
            )

            document_id = metadata.get(
                "document_id"
            )

            if document_id is None:
                document = getattr(
                    item,
                    "document",
                    None,
                )

                if document is not None:
                    document_data = (
                        ResearchPipeline._normalize_execution_result(
                            document
                        )
                    )

                    document_id = (
                        document_data.get(
                            "document_id"
                        )
                        or document_data.get(
                            "id"
                        )
                    )

                    if document_id is None:
                        document_metadata = (
                            document_data.get(
                                "metadata",
                                {},
                            )
                        )

                        if isinstance(
                            document_metadata,
                            dict,
                        ):
                            document_id = (
                                document_metadata.get(
                                    "document_id"
                                )
                            )

            if document_id is None:
                continue

            if (
                str(document_id).strip()
                in allowed_document_ids
            ):
                filtered.append(item)

        return filtered

    @staticmethod
    def _extract_retrieval_results(
        result: Any,
    ) -> List[Any]:

        if result is None:
            return []

        if isinstance(
            result,
            (list, tuple, set),
        ):
            return list(result)

        if isinstance(
            result,
            dict,
        ):
            for key in (
                "results",
                "items",
                "documents",
                "sources",
                "data",
            ):
                nested = result.get(
                    key
                )

                if isinstance(
                    nested,
                    (list, tuple, set),
                ):
                    return list(nested)

            return [result]

        results = getattr(
            result,
            "results",
            None,
        )

        if results is not None:
            if isinstance(
                results,
                (list, tuple, set),
            ):
                return list(results)

        return [result]

    async def _run_retriever(
        self,
        retriever: Any,
        query: ResearchQuery,
    ) -> Any:

        if retriever is None:
            return []

        if hasattr(
            retriever,
            "search",
        ):
            result = retriever.search(query)
            return await self._resolve_awaitable(result)

        if hasattr(
            retriever,
            "retrieve",
        ):
            result = retriever.retrieve(query)
            return await self._resolve_awaitable(result)

        if hasattr(
            retriever,
            "run",
        ):
            result = retriever.run(query)
            return await self._resolve_awaitable(result)

        if callable(retriever):
            result = retriever(query)
            return await self._resolve_awaitable(result)

        raise AttributeError(
            f"{retriever.__class__.__name__} does not expose "
            "`search()`, `retrieve()`, `run()`, or callable interface."
        )

    # ========================================================================
    # EXECUTION / LLM SYNTHESIS
    # ========================================================================

    async def _execute_plan(
        self,
        *,
        query: ResearchQuery,
        execution_plan: Any,
        retrieval_context: Dict[str, Any],
        execution_engine: Optional[Any],
    ) -> Any:

        if execution_engine is not None:
            logger.info(
                "Using explicitly configured research execution engine."
            )

            return await self._execute_with_engine(
                query=query,
                execution_plan=execution_plan,
                retrieval_context=retrieval_context,
                execution_engine=execution_engine,
            )

        if self.llm_pipeline is not None:
            try:
                context_text = self._build_llm_context(
                    retrieval_context
                )

                if context_text.strip():
                    logger.info(
                        "Generating research synthesis with LLMPipeline: "
                        "sources=%s",
                        self._count_sources(
                            retrieval_context
                        ),
                    )

                    return await self._generate_llm_report(
                        query=query,
                        execution_plan=execution_plan,
                        retrieval_context=retrieval_context,
                        context_text=context_text,
                    )

                logger.warning(
                    "No relevant retrieval context was available for "
                    "LLM synthesis."
                )

                return {
                    "mode": "no_relevant_evidence",
                    "results": retrieval_context,
                    "metadata": {
                        "reason": (
                            "No retrieved source passed the research "
                            "relevance gate."
                        ),
                    },
                }

            except Exception as exc:
                logger.error(
                    "LLM research synthesis failed: %s",
                    exc,
                    exc_info=True,
                )

                return {
                    "mode": "llm_failed",
                    "results": retrieval_context,
                    "metadata": {
                        "llm_error": str(exc),
                    },
                }

        logger.warning(
            "No research execution engine or usable LLM pipeline configured. "
            "Using retrieval-only report generation."
        )

        return {
            "mode": "retrieval_only",
            "results": retrieval_context,
        }

    async def _execute_with_engine(
        self,
        *,
        query: ResearchQuery,
        execution_plan: Any,
        retrieval_context: Dict[str, Any],
        execution_engine: Any,
    ) -> Any:

        if hasattr(
            execution_engine,
            "execute",
        ):
            return await self._call_execute(
                execution_engine.execute,
                query=query,
                execution_plan=execution_plan,
                retrieval_context=retrieval_context,
            )

        if hasattr(
            execution_engine,
            "run",
        ):
            return await self._call_execute(
                execution_engine.run,
                query=query,
                execution_plan=execution_plan,
                retrieval_context=retrieval_context,
            )

        if hasattr(
            execution_engine,
            "execute_plan",
        ):
            return await self._call_execute(
                execution_engine.execute_plan,
                query=query,
                execution_plan=execution_plan,
                retrieval_context=retrieval_context,
            )

        raise AttributeError(
            f"{execution_engine.__class__.__name__} does not expose "
            "`execute()`, `run()`, or `execute_plan()`."
        )

    async def _generate_llm_report(
        self,
        *,
        query: ResearchQuery,
        execution_plan: Any,
        retrieval_context: Dict[str, Any],
        context_text: str,
    ) -> Dict[str, Any]:

        system_prompt = self._build_llm_system_prompt(
            query=query,
            execution_plan=execution_plan,
        )

        result = await self.llm_pipeline.research(
            question=query.question,
            context=context_text,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=self._llm_max_tokens(
                query
            ),
        )

        content = str(
            result.content
        ).strip()

        if not content:
            raise RuntimeError(
                "LLMPipeline returned an empty research response."
            )

        logger.info(
            "LLM research synthesis completed: provider=%s model=%s",
            result.provider,
            result.model,
        )

        return {
            "mode": "llm_synthesis",
            "content": content,
            "summary": self._extract_llm_summary(
                content
            ),
            "findings": content,
            "metadata": {
                "llm_provider": result.provider,
                "llm_model": result.model,
                "llm_usage": result.usage,
                "llm_metadata": result.metadata,
                "retrieved_source_count": self._count_sources(
                    retrieval_context
                ),
                "cross_encoder_reranking": self.enable_reranking,
            },
        }

    @staticmethod
    def _llm_max_tokens(
        query: ResearchQuery,
    ) -> int:

        depth = str(
            getattr(
                query,
                "depth",
                "medium",
            )
        ).lower()

        if depth == "basic":
            return 1200

        if depth == "deep":
            return 3000

        return 2000

    @staticmethod
    def _build_llm_system_prompt(
        *,
        query: ResearchQuery,
        execution_plan: Any,
    ) -> str:

        depth = getattr(
            query,
            "depth",
            "medium",
        )

        return (
            "You are the research synthesis engine for an AI research "
            "assistant.\n\n"

            "Your task is to answer the research question using ONLY the "
            "retrieved research context provided to you.\n\n"

            "GROUNDING RULES:\n"

            "1. Ground every factual claim in the supplied research "
            "context.\n"

            "2. Do not invent papers, findings, statistics, authors, "
            "experiments, dates, benchmarks, or technical details.\n"

            "3. A source appearing in the context does NOT automatically "
            "mean that it contains evidence for the user's question.\n"

            "4. Only use a source when its content actually supports the "
            "claim being made.\n"

            "5. If the retrieved context does not establish the answer, "
            "explicitly say that the available knowledge base does not "
            "establish the claim.\n"

            "6. Never infer that two concepts are the same merely because "
            "they are related.\n"

            "7. Distinguish established findings from interpretation.\n"

            "8. If the question asks about a specific entity, paper, model, "
            "method, dataset, or person, do not substitute a related entity "
            "unless the context explicitly establishes the relationship.\n"

            "9. Do not fabricate citations or URLs.\n"

            "10. Do not mention internal implementation details such as "
            "FAISS, BM25, RetrievalService, IndexRegistry, database tables, "
            "or retrieval internals.\n"

            "11. Produce a clear research-oriented answer rather than a "
            "generic conversational response.\n"

            "12. If evidence is missing, be explicit about the limitation "
            "instead of filling the gap from general model knowledge.\n"

            "13. For conflicting evidence, explain the conflict instead of "
            "choosing a side without support.\n"

            "14. Use concise headings and paragraphs suitable for a research "
            "report.\n\n"

            f"Requested research depth: {depth}.\n\n"

            "The execution plan is planning metadata only. The retrieved "
            "evidence is the authoritative context for factual claims."
        )

    # ========================================================================
    # LLM CONTEXT
    # ========================================================================

    @staticmethod
    def _build_llm_context(
        retrieval_context: Dict[str, Any],
    ) -> str:

        sections: List[str] = []

        documentation = retrieval_context.get(
            "documentation",
            [],
        ) or []

        papers = retrieval_context.get(
            "papers",
            [],
        ) or []

        github_results = retrieval_context.get(
            "github",
            [],
        ) or []

        source_counter = 0

        for item in documentation:
            text = ResearchPipeline._item_content(
                item
            )

            if not text:
                continue

            source_counter += 1

            title = ResearchPipeline._item_title(
                item,
                fallback=f"Knowledge-base source {source_counter}",
            )

            metadata = ResearchPipeline._item_metadata(
                item
            )

            sections.append(
                ResearchPipeline._format_context_source(
                    source_number=source_counter,
                    source_type="knowledge_base",
                    title=title,
                    content=text,
                    metadata=metadata,
                )
            )

        for item in papers:
            text = ResearchPipeline._item_content(
                item
            )

            if not text:
                continue

            source_counter += 1

            title = ResearchPipeline._item_title(
                item,
                fallback=f"Paper source {source_counter}",
            )

            metadata = ResearchPipeline._item_metadata(
                item
            )

            sections.append(
                ResearchPipeline._format_context_source(
                    source_number=source_counter,
                    source_type="paper",
                    title=title,
                    content=text,
                    metadata=metadata,
                )
            )

        for item in github_results:
            text = ResearchPipeline._item_content(
                item
            )

            if not text:
                continue

            source_counter += 1

            title = ResearchPipeline._item_title(
                item,
                fallback=f"GitHub source {source_counter}",
            )

            metadata = ResearchPipeline._item_metadata(
                item
            )

            sections.append(
                ResearchPipeline._format_context_source(
                    source_number=source_counter,
                    source_type="github",
                    title=title,
                    content=text,
                    metadata=metadata,
                )
            )

        return "\n\n".join(
            section
            for section in sections
            if section.strip()
        )

    @staticmethod
    def _format_context_source(
        *,
        source_number: int,
        source_type: str,
        title: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> str:

        metadata_lines: List[str] = []

        for key in (
            "paper_id",
            "document_id",
            "section_id",
            "chunk_index",
            "page_number",
            "year",
            "publication_year",
            "doi",
            "arxiv_id",
        ):
            value = metadata.get(
                key
            )

            if value is not None:
                metadata_lines.append(
                    f"{key}: {value}"
                )

        metadata_text = ""

        if metadata_lines:
            metadata_text = (
                "\nMetadata:\n"
                + "\n".join(
                    metadata_lines
                )
            )

        return (
            f"[SOURCE {source_number}]\n"
            f"TYPE: {source_type}\n"
            f"TITLE: {title}"
            f"{metadata_text}\n"
            "CONTENT:\n"
            f"{content.strip()}"
        )

    # ========================================================================
    # ITEM HELPERS
    # ========================================================================

    @staticmethod
    def _item_content(
        item: Any,
    ) -> str:

        if item is None:
            return ""

        if isinstance(
            item,
            str,
        ):
            return item.strip()

        data = ResearchPipeline._normalize_execution_result(
            item
        )

        document = getattr(
            item,
            "document",
            None,
        )

        if document is not None:
            document_data = (
                ResearchPipeline._normalize_execution_result(
                    document
                )
            )

            for key in (
                "content",
                "text",
                "chunk_content",
                "page_content",
                "abstract",
                "description",
            ):
                value = document_data.get(
                    key
                )

                if value:
                    return str(
                        value
                    ).strip()

        for key in (
            "content",
            "text",
            "chunk_content",
            "page_content",
            "abstract",
            "description",
        ):
            value = data.get(
                key
            )

            if value:
                return str(
                    value
                ).strip()

        return ""

    @staticmethod
    def _item_title(
        item: Any,
        *,
        fallback: str,
    ) -> str:

        data = ResearchPipeline._normalize_execution_result(
            item
        )

        document = getattr(
            item,
            "document",
            None,
        )

        if document is not None:
            document_data = (
                ResearchPipeline._normalize_execution_result(
                    document
                )
            )

            for key in (
                "title",
                "name",
                "display_name",
            ):
                value = document_data.get(
                    key
                )

                if value:
                    return str(value)

        metadata = data.get(
            "metadata",
            {},
        )

        if isinstance(
            metadata,
            dict,
        ):
            for key in (
                "title",
                "paper_title",
                "document_title",
                "name",
            ):
                value = metadata.get(
                    key
                )

                if value:
                    return str(value)

        for key in (
            "title",
            "name",
            "display_name",
        ):
            value = data.get(
                key
            )

            if value:
                return str(value)

        return fallback

    @staticmethod
    def _item_metadata(
        item: Any,
    ) -> Dict[str, Any]:

        data = ResearchPipeline._normalize_execution_result(
            item
        )

        metadata: Dict[str, Any] = {}

        raw_metadata = data.get(
            "metadata",
            {},
        )

        if isinstance(
            raw_metadata,
            dict,
        ):
            metadata.update(
                raw_metadata
            )

        document = getattr(
            item,
            "document",
            None,
        )

        if document is not None:
            document_data = (
                ResearchPipeline._normalize_execution_result(
                    document
                )
            )

            document_metadata = document_data.get(
                "metadata",
                {},
            )

            if isinstance(
                document_metadata,
                dict,
            ):
                metadata = {
                    **document_metadata,
                    **metadata,
                }

            for key in (
                "document_id",
                "section_id",
                "chunk_index",
                "page_number",
                "paper_id",
                "score",
                "rerank_score",
                "vector_score",
                "keyword_score",
            ):
                if (
                    key in document_data
                    and key not in metadata
                ):
                    metadata[key] = document_data[key]

        for key in (
            "document_id",
            "section_id",
            "chunk_index",
            "page_number",
            "paper_id",
            "score",
            "rerank_score",
            "vector_score",
            "keyword_score",
        ):
            if (
                key in data
                and key not in metadata
            ):
                metadata[key] = data[key]

        for key in (
            "score",
            "rerank_score",
            "vector_score",
            "keyword_score",
        ):
            value = getattr(
                item,
                key,
                None,
            )

            if (
                value is not None
                and key not in metadata
            ):
                metadata[key] = value

        return metadata

    # ========================================================================
    # SOURCE COUNT
    # ========================================================================

    @staticmethod
    def _count_sources(
        retrieval_context: Dict[str, Any],
    ) -> int:

        return sum(
            len(
                retrieval_context.get(
                    key,
                    [],
                )
                or []
            )
            for key in (
                "documentation",
                "papers",
                "github",
            )
        )

    # ========================================================================
    # LLM SUMMARY
    # ========================================================================

    @staticmethod
    def _extract_llm_summary(
        content: str,
    ) -> str:

        cleaned = content.strip()

        if not cleaned:
            return ""

        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(
                r"\n\s*\n",
                cleaned,
            )
            if paragraph.strip()
        ]

        for paragraph in paragraphs:
            if paragraph.startswith("#"):
                continue

            if len(paragraph) >= 80:
                if len(paragraph) > 1200:
                    return (
                        paragraph[:1197]
                        + "..."
                    )

                return paragraph

        if len(cleaned) > 1200:
            return (
                cleaned[:1197]
                + "..."
            )

        return cleaned

    # ========================================================================
    # EXECUTION ENGINE COMPATIBILITY
    # ========================================================================

    async def _call_execute(
        self,
        method: Any,
        *,
        query: ResearchQuery,
        execution_plan: Any,
        retrieval_context: Dict[str, Any],
    ) -> Any:

        if method is None:
            raise ValueError(
                "Execution method cannot be None."
            )

        try:
            signature = inspect.signature(
                method
            )

            parameters = signature.parameters

            accepts_kwargs = any(
                parameter.kind
                == inspect.Parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )

            keyword_arguments = {
                "query": query,
                "execution_plan": execution_plan,
                "retrieval_context": retrieval_context,
            }

            if accepts_kwargs:
                result = method(
                    **keyword_arguments
                )

                return await self._resolve_awaitable(
                    result
                )

            supported_kwargs: Dict[str, Any] = {}

            for name, value in keyword_arguments.items():
                if name in parameters:
                    supported_kwargs[name] = value

            if supported_kwargs:
                result = method(
                    **supported_kwargs
                )

                return await self._resolve_awaitable(
                    result
                )

        except (
            ValueError,
            TypeError,
        ):
            logger.debug(
                "Could not inspect execution method signature; "
                "using compatibility fallbacks.",
                exc_info=True,
            )

        try:
            result = method(
                query=query,
                execution_plan=execution_plan,
                retrieval_context=retrieval_context,
            )

            return await self._resolve_awaitable(
                result
            )

        except TypeError:
            logger.debug(
                "Execution method does not support full keyword signature.",
                exc_info=True,
            )

        try:
            result = method(
                execution_plan
            )

            return await self._resolve_awaitable(
                result
            )

        except TypeError:
            logger.debug(
                "Execution method does not support plan-only signature.",
                exc_info=True,
            )

        try:
            result = method(
                query,
                execution_plan,
            )

            return await self._resolve_awaitable(
                result
            )

        except TypeError:
            logger.debug(
                "Execution method does not support query + plan signature.",
                exc_info=True,
            )

        result = method(
            query
        )

        return await self._resolve_awaitable(
            result
        )

    # ========================================================================
    # REPORT CONSTRUCTION
    # ========================================================================

    def _build_report(
        self,
        *,
        query: ResearchQuery,
        execution_plan: Any,
        execution_result: Any,
        retrieval_context: Dict[str, Any],
        started_at: datetime,
    ) -> ResearchReport:

        completed_at = datetime.now(
            timezone.utc
        )

        if isinstance(
            execution_result,
            ResearchReport,
        ):
            return execution_result

        result_data = self._normalize_execution_result(
            execution_result
        )

        report_candidate = result_data.get(
            "report"
        )

        if isinstance(
            report_candidate,
            dict,
        ):
            result_data = {
                **result_data,
                **report_candidate,
            }

        elif isinstance(
            report_candidate,
            ResearchReport,
        ):
            return report_candidate

        sources = self._build_sources(
            retrieval_context
        )

        evidence = self._build_evidence(
            sources
        )

        citations = self._build_citations(
            sources
        )

        sections = self._build_sections(
            query=query,
            execution_result=result_data,
            sources=sources,
            evidence=evidence,
        )

        summary = self._extract_summary(
            result_data
        )

        if not summary:
            summary = self._build_default_summary(
                query=query,
                sources=sources,
            )

        title = self._extract_title(
            result_data
        )

        if not title:
            title = self._build_title(
                query.question
            )

        comparison = self._build_comparison(
            query=query,
            result_data=result_data,
        )

        metadata: Dict[str, Any] = {
            "pipeline": "research",
            "question": query.question,
            "depth": getattr(
                query,
                "depth",
                None,
            ),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": (
                completed_at - started_at
            ).total_seconds(),
            "paper_count": len(
                retrieval_context.get(
                    "papers",
                    [],
                )
                or []
            ),
            "github_result_count": len(
                retrieval_context.get(
                    "github",
                    [],
                )
                or []
            ),
            "documentation_count": len(
                retrieval_context.get(
                    "documentation",
                    [],
                )
                or []
            ),
            "source_count": len(
                sources
            ),
            "execution_mode": result_data.get(
                "mode",
                "execution_engine",
            ),
            "research_relevance_filter": True,
            "cross_encoder_reranking": self.enable_reranking,
        }

        engine_metadata = result_data.get(
            "metadata"
        )

        if isinstance(
            engine_metadata,
            dict,
        ):
            metadata.update(
                engine_metadata
            )

        result_metadata: Dict[str, Any] = {}

        raw_metadata = result_data.get(
            "metadata"
        )

        if isinstance(
            raw_metadata,
            dict,
        ):
            result_metadata = raw_metadata

        llm_error = result_metadata.get(
            "llm_error"
        )

        execution_mode = result_data.get(
            "mode"
        )

        if (
            execution_mode == "llm_synthesis"
            and not llm_error
        ):
            report_status = "completed"

        elif sources:
            report_status = "partial"

        else:
            report_status = "failed"

        return ResearchReport(
            title=title,
            summary=summary,
            sections=sections,
            citations=citations,
            evidence=evidence,
            sources=sources,
            comparison=comparison,
            metadata=metadata,
            status=report_status,
        )

    # ========================================================================
    # SOURCE CONVERSION
    # ========================================================================

    def _build_sources(
        self,
        retrieval_context: Dict[str, Any],
    ) -> List[ResearchSource]:

        sources: List[ResearchSource] = []

        documentation = retrieval_context.get(
            "documentation",
            [],
        ) or []

        for index, item in enumerate(
            documentation
        ):
            source = self._source_from_item(
                item=item,
                source_type="documentation",
                index=index,
            )

            if source is not None:
                sources.append(
                    source
                )

        papers = retrieval_context.get(
            "papers",
            [],
        ) or []

        paper_offset = len(
            sources
        )

        for index, item in enumerate(
            papers
        ):
            source = self._source_from_item(
                item=item,
                source_type="paper",
                index=paper_offset + index,
            )

            if source is not None:
                sources.append(
                    source
                )

        github_results = retrieval_context.get(
            "github",
            [],
        ) or []

        github_offset = len(
            sources
        )

        for index, item in enumerate(
            github_results
        ):
            source = self._source_from_item(
                item=item,
                source_type="github",
                index=github_offset + index,
            )

            if source is not None:
                sources.append(
                    source
                )

        return sources

    def _source_from_item(
        self,
        *,
        item: Any,
        source_type: str,
        index: int,
    ) -> Optional[ResearchSource]:

        if item is None:
            return None

        if isinstance(
            item,
            ResearchSource,
        ):
            return item

        data = self._normalize_execution_result(
            item
        )

        document = getattr(
            item,
            "document",
            None,
        )

        if document is not None:
            document_data = (
                self._normalize_execution_result(
                    document
                )
            )

            merged_data = {
                **document_data,
                **data,
            }

            document_metadata = document_data.get(
                "metadata",
                {},
            )

            result_metadata = data.get(
                "metadata",
                {},
            )

            if isinstance(
                document_metadata,
                dict,
            ) or isinstance(
                result_metadata,
                dict,
            ):
                merged_data["metadata"] = {
                    **(
                        document_metadata
                        if isinstance(
                            document_metadata,
                            dict,
                        )
                        else {}
                    ),
                    **(
                        result_metadata
                        if isinstance(
                            result_metadata,
                            dict,
                        )
                        else {}
                    ),
                }

            data = merged_data

        source_id = (
            data.get("id")
            or data.get("source_id")
            or data.get("document_id")
            or data.get("paper_id")
            or data.get("doi")
            or data.get("arxiv_id")
            or data.get("url")
            or data.get("html_url")
            or f"{source_type}-{index + 1}"
        )

        title = (
            data.get("title")
            or data.get("name")
            or data.get("display_name")
        )

        metadata = data.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}
        else:
            metadata = dict(
                metadata
            )

        if not title:
            title = (
                metadata.get("title")
                or metadata.get("paper_title")
                or metadata.get("document_title")
                or f"{source_type.title()} source {index + 1}"
            )

        url = (
            data.get("url")
            or data.get("link")
            or data.get("html_url")
            or data.get("landing_page_url")
            or data.get("pdf_url")
            or metadata.get("url")
        )

        authors = data.get(
            "authors",
            [],
        )

        if authors is None:
            authors = []

        if isinstance(
            authors,
            str,
        ):
            authors = [authors]

        if not isinstance(
            authors,
            (list, tuple),
        ):
            authors = []

        normalized_authors: List[str] = []

        for author in authors:
            if isinstance(
                author,
                dict,
            ):
                author_name = (
                    author.get("name")
                    or author.get("display_name")
                    or author.get("author_name")
                )

                if author_name:
                    normalized_authors.append(
                        str(author_name)
                    )

            else:
                normalized_authors.append(
                    str(author)
                )

        content = (
            data.get("content")
            or data.get("text")
            or data.get("chunk_content")
            or data.get("page_content")
            or data.get("abstract")
            or data.get("description")
            or ""
        )

        for key in (
            "year",
            "publication_year",
            "published_year",
            "publication_date",
            "published",
            "authors",
            "doi",
            "arxiv_id",
            "paper_id",
            "document_id",
            "section_id",
            "chunk_index",
            "page_number",
            "provider",
            "provider_paper_id",
            "landing_page_url",
            "pdf_url",
            "source",
            "repository",
            "stars",
            "language",
            "score",
            "rerank_score",
            "vector_score",
            "keyword_score",
            "research_relevance_score",
        ):
            if (
                key in data
                and key not in metadata
            ):
                metadata[key] = data[key]

        for key in (
            "score",
            "rerank_score",
            "vector_score",
            "keyword_score",
        ):
            value = getattr(
                item,
                key,
                None,
            )

            if (
                value is not None
                and key not in metadata
            ):
                metadata[key] = value

        return ResearchSource(
            id=str(
                source_id
            ),
            title=str(
                title
            ),
            source_type=source_type,
            url=(
                str(url)
                if url
                else None
            ),
            authors=normalized_authors,
            content=str(
                content
            ),
            metadata=metadata,
        )

    # ========================================================================
    # EVIDENCE
    # ========================================================================

    def _build_evidence(
        self,
        sources: List[ResearchSource],
    ) -> List[Evidence]:

        evidence: List[Evidence] = []

        for index, source in enumerate(
            sources
        ):
            content = str(
                getattr(
                    source,
                    "content",
                    "",
                )
                or ""
            ).strip()

            if not content:
                continue

            supporting_text = content

            if len(
                supporting_text
            ) > 1500:
                supporting_text = (
                    supporting_text[:1500]
                    + "..."
                )

            relevance_score = self._source_relevance_score(
                source
            )

            confidence = self._evidence_confidence(
                source=source,
                relevance_score=relevance_score,
            )

            evidence.append(
                Evidence(
                    id=f"evidence-{index + 1}",
                    claim=(
                        "Retrieved evidence from "
                        f"{source.title} was selected as relevant "
                        "to the research question."
                    ),
                    supporting_text=supporting_text,
                    source_id=source.id,
                    confidence=confidence,
                    relevance_score=relevance_score,
                )
            )

        return evidence

    @staticmethod
    def _source_relevance_score(
        source: ResearchSource,
    ) -> float:

        metadata = getattr(
            source,
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            return 0.0

        for key in (
            "research_relevance_score",
            "rerank_score",
            "score",
        ):
            value = metadata.get(
                key
            )

            if value is None:
                continue

            try:
                numeric = float(value)

                if math.isfinite(numeric):
                    return ResearchPipeline._clamp(
                        numeric,
                        0.0,
                        1.0,
                    )

            except (
                TypeError,
                ValueError,
            ):
                continue

        return 0.0

    @staticmethod
    def _evidence_confidence(
        *,
        source: ResearchSource,
        relevance_score: float,
    ) -> float:

        metadata = getattr(
            source,
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        rerank_score = metadata.get(
            "rerank_score"
        )

        if rerank_score is not None:
            try:
                rerank_score = float(
                    rerank_score
                )

                if not math.isfinite(
                    rerank_score
                ):
                    rerank_score = None

            except (
                TypeError,
                ValueError,
            ):
                rerank_score = None

        if (
            rerank_score is not None
            and 0.0 <= rerank_score <= 1.0
        ):
            confidence = (
                0.60 * relevance_score
                + 0.40 * rerank_score
            )

        else:
            confidence = relevance_score

        return ResearchPipeline._clamp(
            confidence,
            0.0,
            1.0,
        )

    # ========================================================================
    # CITATIONS
    # ========================================================================

    def _build_citations(
        self,
        sources: List[ResearchSource],
    ) -> List[Citation]:

        citations: List[Citation] = []

        for index, source in enumerate(
            sources
        ):
            year = self._extract_year(
                source
            )

            citation_text = source.title

            if source.authors:
                citation_text = (
                    ", ".join(
                        source.authors
                    )
                    + ". "
                    + source.title
                )

            if year:
                citation_text += (
                    f" ({year})"
                )

            citations.append(
                Citation(
                    id=f"citation-{index + 1}",
                    source_id=source.id,
                    title=source.title,
                    authors=source.authors,
                    year=year,
                    citation_text=citation_text,
                    url=source.url,
                )
            )

        return citations

    # ========================================================================
    # SECTIONS
    # ========================================================================

    def _build_sections(
        self,
        *,
        query: ResearchQuery,
        execution_result: Dict[str, Any],
        sources: List[ResearchSource],
        evidence: List[Evidence],
    ) -> List[ResearchSection]:

        sections: List[ResearchSection] = []

        sections.append(
            ResearchSection(
                title="Research Question",
                content=query.question,
                evidence_ids=[],
            )
        )

        findings = self._extract_findings(
            execution_result
        )

        if not findings:
            findings = self._build_source_findings(
                sources
            )

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

        source_content = self._build_source_section(
            sources
        )

        sections.append(
            ResearchSection(
                title="Research Sources",
                content=source_content,
                evidence_ids=[
                    item.id
                    for item in evidence
                ],
            )
        )

        depth = getattr(
            query,
            "depth",
            None,
        )

        if depth == "deep":
            sections.append(
                ResearchSection(
                    title="Limitations and Research Gaps",
                    content=(
                        "The retrieved evidence should be evaluated for "
                        "conflicting findings, methodological limitations, "
                        "unresolved questions, and gaps in the available "
                        "literature."
                    ),
                    evidence_ids=[],
                )
            )

        return sections

    # ========================================================================
    # COMPARISON
    # ========================================================================

    def _build_comparison(
        self,
        *,
        query: ResearchQuery,
        result_data: Dict[str, Any],
    ) -> Optional[ComparisonResult]:

        try:
            requires_comparison = (
                ResearchPlanner.requires_comparison(
                    query.question
                )
            )

        except Exception:
            requires_comparison = False

        if not requires_comparison:
            return None

        existing = result_data.get(
            "comparison"
        )

        if isinstance(
            existing,
            ComparisonResult,
        ):
            return existing

        if isinstance(
            existing,
            dict,
        ):
            try:
                return ComparisonResult(
                    **existing
                )

            except Exception:
                logger.debug(
                    "Could not normalize existing comparison result.",
                    exc_info=True,
                )

        return ComparisonResult(
            topic=query.question,
            criteria=[
                "Approach",
                "Advantages",
                "Limitations",
                "Use cases",
                "Evidence",
            ],
            comparison_table=[],
        )

    # ========================================================================
    # SUMMARY / TITLE
    # ========================================================================

    @staticmethod
    def _build_title(
        query: str,
    ) -> str:

        cleaned = str(
            query
        ).strip()

        if len(
            cleaned
        ) > 120:
            cleaned = (
                cleaned[:117]
                + "..."
            )

        return (
            f"Research Report: {cleaned}"
        )

    @staticmethod
    def _build_default_summary(
        *,
        query: ResearchQuery,
        sources: List[ResearchSource],
    ) -> str:

        if not sources:
            return (
                "No relevant sources were retrieved from the current "
                "research knowledge base for the question: "
                f"{query.question}. "
                "The research pipeline could not produce a substantive "
                "evidence-backed answer."
            )

        source_types = sorted(
            {
                source.source_type
                for source in sources
            }
        )

        return (
            "The research pipeline analyzed the question "
            f'"{query.question}" using '
            f"{len(sources)} relevant retrieved source(s). "
            "Available source types include "
            f"{', '.join(source_types)}."
        )

    @staticmethod
    def _extract_title(
        data: Dict[str, Any],
    ) -> Optional[str]:

        value = (
            data.get("title")
            or data.get("report_title")
        )

        if value is None:
            return None

        return str(
            value
        )

    @staticmethod
    def _extract_summary(
        data: Dict[str, Any],
    ) -> Optional[str]:

        value = (
            data.get("summary")
            or data.get("executive_summary")
            or data.get("abstract")
        )

        if value is None:
            return None

        if isinstance(
            value,
            dict,
        ):
            return str(
                value.get(
                    "text",
                    value,
                )
            )

        if isinstance(
            value,
            list,
        ):
            return "\n".join(
                str(item)
                for item in value
            )

        return str(
            value
        )

    @staticmethod
    def _extract_findings(
        data: Dict[str, Any],
    ) -> Optional[str]:

        value = (
            data.get("findings")
            or data.get("key_findings")
            or data.get("analysis")
            or data.get("content")
        )

        if value is None:
            return None

        if isinstance(
            value,
            list,
        ):
            return "\n".join(
                f"- {item}"
                for item in value
            )

        if isinstance(
            value,
            dict,
        ):
            return str(
                value
            )

        return str(
            value
        )

    # ========================================================================
    # SOURCE FALLBACK CONTENT
    # ========================================================================

    @staticmethod
    def _build_source_findings(
        sources: List[ResearchSource],
    ) -> str:

        if not sources:
            return (
                "No retrieved source content is currently available."
            )

        lines: List[str] = []

        for source in sources[:10]:
            content = str(
                getattr(
                    source,
                    "content",
                    "",
                )
                or ""
            ).strip()

            if not content:
                content = (
                    "The source was retrieved but no extracted content "
                    "is currently available."
                )

            if len(
                content
            ) > 500:
                content = (
                    content[:500]
                    + "..."
                )

            lines.append(
                f"- {source.title}: {content}"
            )

        return "\n".join(
            lines
        )

    @staticmethod
    def _build_source_section(
        sources: List[ResearchSource],
    ) -> str:

        if not sources:
            return (
                "No relevant research sources were retrieved."
            )

        lines: List[str] = []

        for source in sources:
            line = (
                f"- {source.title} "
                f"({source.source_type})"
            )

            if source.url:
                line += (
                    f": {source.url}"
                )

            lines.append(
                line
            )

        return "\n".join(
            lines
        )

    # ========================================================================
    # NORMALIZATION HELPERS
    # ========================================================================

    @staticmethod
    async def _resolve_awaitable(
        value: Any,
    ) -> Any:

        if inspect.isawaitable(
            value
        ):
            return await value

        return value

    @staticmethod
    def _normalize_execution_result(
        execution_result: Any,
    ) -> Dict[str, Any]:

        if execution_result is None:
            return {}

        if isinstance(
            execution_result,
            dict,
        ):
            return dict(
                execution_result
            )

        if hasattr(
            execution_result,
            "model_dump",
        ):
            try:
                result = execution_result.model_dump()

                if isinstance(
                    result,
                    dict,
                ):
                    return result

            except Exception:
                logger.debug(
                    "model_dump() failed during result normalization.",
                    exc_info=True,
                )

        if hasattr(
            execution_result,
            "dict",
        ):
            try:
                result = execution_result.dict()

                if isinstance(
                    result,
                    dict,
                ):
                    return result

            except Exception:
                logger.debug(
                    "dict() failed during result normalization.",
                    exc_info=True,
                )

        if hasattr(
            execution_result,
            "__dict__",
        ):
            try:
                return dict(
                    execution_result.__dict__
                )

            except Exception:
                logger.debug(
                    "__dict__ normalization failed.",
                    exc_info=True,
                )

        return {
            "output": execution_result
        }

    @staticmethod
    def _normalize_collection(
        value: Any,
    ) -> List[Any]:

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            tuple,
        ):
            return list(value)

        if isinstance(
            value,
            set,
        ):
            return list(value)

        if isinstance(
            value,
            dict,
        ):
            for key in (
                "results",
                "items",
                "papers",
                "repositories",
                "sources",
                "documents",
                "data",
            ):
                nested = value.get(
                    key
                )

                if isinstance(
                    nested,
                    (list, tuple, set),
                ):
                    return list(
                        nested
                    )

        return [
            value
        ]

    @staticmethod
    def _extract_year(
        source: ResearchSource,
    ) -> Optional[int]:

        metadata = getattr(
            source,
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            return None

        for key in (
            "year",
            "publication_year",
            "published_year",
            "publication_date",
            "published",
        ):
            value = metadata.get(
                key
            )

            if value is None:
                continue

            try:
                if isinstance(
                    value,
                    int,
                ):
                    return value

                match = re.search(
                    r"(19|20)\d{2}",
                    str(value),
                )

                if match:
                    return int(
                        match.group(0)
                    )

            except Exception:
                continue

        return None

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        try:
            value = float(value)

        except (
            TypeError,
            ValueError,
        ):
            return minimum

        if not math.isfinite(value):
            return minimum

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_query(
        query: ResearchQuery,
    ) -> None:

        if query is None:
            raise ValueError(
                "ResearchQuery cannot be None."
            )

        if not isinstance(
            query,
            ResearchQuery,
        ):
            raise ValueError(
                "ResearchPipeline requires a ResearchQuery instance."
            )

        research_question = getattr(
            query,
            "question",
            None,
        )

        if not isinstance(
            research_question,
            str,
        ):
            raise ValueError(
                "ResearchQuery.question must be a string."
            )

        research_question = (
            research_question.strip()
        )

        if len(
            research_question
        ) < 3:
            raise ValueError(
                "Research query must contain at least 3 characters."
            )

        if len(
            research_question
        ) > 5000:
            raise ValueError(
                "Research query cannot exceed 5000 characters."
            )


# ============================================================================
# APPLICATION-LEVEL PIPELINE
# ============================================================================


_default_pipeline: Optional[ResearchPipeline] = None


def get_research_pipeline(
    *,
    planner: Optional[ResearchPlanner] = None,
    paper_retriever: Optional[PaperRetriever] = None,
    github_retriever: Optional[GitHubRetriever] = None,
    retrieval_service: Optional[RetrievalService] = None,
    llm_pipeline: Optional[LLMPipeline] = None,
    execution_engine: Optional[Any] = None,
) -> ResearchPipeline:

    global _default_pipeline

    explicit_dependencies = any(
        dependency is not None
        for dependency in (
            planner,
            paper_retriever,
            github_retriever,
            retrieval_service,
            llm_pipeline,
            execution_engine,
        )
    )

    if explicit_dependencies:
        return ResearchPipeline(
            planner=planner,
            paper_retriever=paper_retriever,
            github_retriever=github_retriever,
            retrieval_service=retrieval_service,
            llm_pipeline=llm_pipeline,
            execution_engine=execution_engine,
        )

    if _default_pipeline is None:
        _default_pipeline = ResearchPipeline()

    return _default_pipeline


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


async def run_research(
    query: ResearchQuery,
    *,
    planner: Optional[ResearchPlanner] = None,
    paper_retriever: Optional[PaperRetriever] = None,
    github_retriever: Optional[GitHubRetriever] = None,
    retrieval_service: Optional[RetrievalService] = None,
    llm_pipeline: Optional[LLMPipeline] = None,
    execution_engine: Optional[Any] = None,
    allowed_document_ids: Optional[List[str]] = None,
) -> ResearchReport:

    pipeline = get_research_pipeline(
        planner=planner,
        paper_retriever=paper_retriever,
        github_retriever=github_retriever,
        retrieval_service=retrieval_service,
        llm_pipeline=llm_pipeline,
        execution_engine=execution_engine,
    )

    return await pipeline.run(
        query,
        execution_engine=execution_engine,
        allowed_document_ids=allowed_document_ids,
    )