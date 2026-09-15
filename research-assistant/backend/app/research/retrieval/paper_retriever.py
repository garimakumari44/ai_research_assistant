from __future__ import annotations

import inspect
import logging
import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    Mapping,
    Sequence,
)
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.db.models.paper import Paper
from app.research.models import (
    ResearchQuery,
    RetrievedDocument,
    ResearchSource,
)

logger = logging.getLogger(__name__)


PaperSearchFunction = Callable[
    [str, int],
    Iterable[Mapping[str, Any]]
    | Awaitable[Iterable[Mapping[str, Any]]],
]


class PaperRetriever:
    """
    Retrieves academic papers for research queries.

    Retrieval sources, in priority order:

    1. Injected ``search_fn`` provider.
    2. PostgreSQL ``papers`` table when ``session_factory`` is configured.

    The retriever does not fabricate papers.

    PostgreSQL papers currently contain bibliographic information and
    abstracts. The abstract is used as the searchable source content
    until the paper has been ingested into:

        documents
            -> document_sections
            -> document_chunks
            -> vector/keyword indexes

    Query handling
    --------------

    Research queries are usually natural-language questions, for example:

        "what you know about bert"
        "tell me about transformers"
        "what is attention is all you need"

    Those queries should NOT be searched literally as one PostgreSQL
    substring.

    Instead, the local database search:

    1. Normalizes the query.
    2. Removes conversational stop words.
    3. Extracts meaningful search terms.
    4. Searches those terms across title/abstract/identifiers.
    5. Calculates a deterministic title/abstract relevance score.

    This keeps the database retriever useful without pretending that
    lexical search is semantic retrieval.
    """

    # ------------------------------------------------------------------
    # Conversational / generic words that should not dominate paper
    # retrieval.
    # ------------------------------------------------------------------

    _QUERY_STOP_WORDS: frozenset[str] = frozenset(
        {
            "a",
            "an",
            "and",
            "are",
            "about",
            "be",
            "can",
            "could",
            "do",
            "does",
            "for",
            "from",
            "give",
            "has",
            "have",
            "how",
            "i",
            "information",
            "is",
            "me",
            "more",
            "of",
            "on",
            "please",
            "should",
            "tell",
            "the",
            "this",
            "to",
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
            "know",
            "explain",
            "describe",
            "discuss",
            "details",
            "detail",
            "something",
            "anything",
        }
    )

    # Terms shorter than this are generally too noisy for the local
    # lexical paper search, except identifiers handled separately.
    _MIN_QUERY_TERM_LENGTH = 2

    def __init__(
        self,
        top_k: int = 5,
        search_fn: PaperSearchFunction | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero"
            )

        self.top_k = top_k
        self._search_fn = search_fn
        self._session_factory = session_factory

    # ==================================================================
    # PUBLIC RETRIEVAL
    # ==================================================================

    async def retrieve(
        self,
        query: ResearchQuery,
    ) -> list[RetrievedDocument]:
        """
        Retrieve and normalize academic papers.
        """

        if query is None:
            raise ValueError(
                "query cannot be None"
            )

        # ResearchQuery.question is the canonical public/API field.
        query_text = query.question.strip()

        if not query_text:
            raise ValueError(
                "research query cannot be empty"
            )

        papers = await self.search_papers(
            query_text,
            top_k=self.top_k,
        )

        documents: list[RetrievedDocument] = []
        seen: set[str] = set()

        for paper in papers:
            normalized = self._normalize_paper(
                paper
            )

            if normalized is None:
                continue

            dedup_key = self._deduplication_key(
                normalized
            )

            if dedup_key in seen:
                continue

            seen.add(
                dedup_key
            )

            try:
                source_metadata = {
                    "paper_id": normalized.get(
                        "paper_id"
                    ),
                    "doi": normalized.get(
                        "doi"
                    ),
                    "arxiv_id": normalized.get(
                        "arxiv_id"
                    ),
                    "pmid": normalized.get(
                        "pmid"
                    ),
                    "provider": normalized.get(
                        "provider"
                    ),
                    "provider_paper_id": normalized.get(
                        "provider_paper_id"
                    ),
                    "year": normalized.get(
                        "year"
                    ),
                    "category": "academic",
                    "retrieval_source": normalized.get(
                        "retrieval_source",
                        "paper",
                    ),
                    "retrieval_score": normalized.get(
                        "score",
                        0.0,
                    ),
                    **normalized.get(
                        "metadata",
                        {},
                    ),
                }

                source = ResearchSource(
                    id=str(
                        uuid4()
                    ),
                    title=normalized["title"],
                    source_type="paper",
                    url=normalized.get(
                        "url"
                    ),
                    authors=normalized["authors"],
                    content=normalized["content"],
                    metadata=source_metadata,
                )

                document = RetrievedDocument(
                    id=str(
                        uuid4()
                    ),
                    source=source,
                    text=normalized["content"],
                    score=normalized["score"],
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                logger.warning(
                    "Skipping invalid paper result",
                    extra={
                        "error": str(exc),
                        "title": normalized.get(
                            "title"
                        ),
                    },
                )
                continue

            documents.append(
                document
            )

            if len(documents) >= self.top_k:
                break

        logger.info(
            "Paper retrieval completed: query=%r results=%d",
            query_text,
            len(documents),
        )

        return documents

    # ==================================================================
    # PAPER SEARCH
    # ==================================================================

    async def search_papers(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[Mapping[str, Any]]:
        """
        Search for academic papers.

        If an injected provider exists, it is used first.

        Otherwise, when ``session_factory`` is configured, the local
        PostgreSQL ``papers`` table is searched using meaningful query
        terms across:

        - title
        - abstract
        - arXiv ID
        - DOI
        - PMID
        - provider paper ID

        No mock or fabricated papers are returned.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty"
            )

        limit = (
            top_k
            if top_k is not None
            else self.top_k
        )

        if limit <= 0:
            raise ValueError(
                "top_k must be greater than zero"
            )

        # --------------------------------------------------------------
        # 1. External/injected provider
        # --------------------------------------------------------------

        if self._search_fn is not None:
            try:
                results = self._search_fn(
                    query,
                    limit,
                )

                if inspect.isawaitable(
                    results
                ):
                    results = await results

                if results is None:
                    return []

                return list(
                    results
                )[:limit]

            except Exception:
                logger.exception(
                    "Paper search provider failed; "
                    "falling back to PostgreSQL",
                    extra={
                        "query": query
                    },
                )

        # --------------------------------------------------------------
        # 2. Local PostgreSQL papers
        # --------------------------------------------------------------

        if self._session_factory is None:
            logger.warning(
                "No paper search provider or database configured",
                extra={
                    "query": query
                },
            )
            return []

        return await self._search_database(
            query=query,
            limit=limit,
        )

    # ==================================================================
    # DATABASE SEARCH
    # ==================================================================

    async def _search_database(
        self,
        query: str,
        limit: int,
    ) -> list[Mapping[str, Any]]:
        """
        Search the PostgreSQL papers table.

        Natural-language queries are converted into meaningful lexical
        terms before constructing the SQL query.

        Example:

            "what you know about bert"

        becomes approximately:

            ["bert"]

        Example:

            "tell me about transformer attention"

        becomes approximately:

            ["transformer", "attention"]

        The SQL query intentionally remains lexical. Semantic relevance
        belongs to the proper document/vector retrieval layer.
        """

        search_terms = self._extract_search_terms(
            query
        )

        # If all terms were filtered out, fall back to tokens from the
        # original query rather than producing a completely unbounded
        # database search.
        if not search_terms:
            search_terms = self._fallback_search_terms(
                query
            )

        if not search_terms:
            logger.warning(
                "No usable paper search terms extracted",
                extra={
                    "query": query
                },
            )
            return []

        # --------------------------------------------------------------
        # Build OR conditions for meaningful terms.
        #
        # A query like:
        #
        #     "what you know about bert"
        #
        # becomes:
        #
        #     title ILIKE "%bert%"
        #     OR abstract ILIKE "%bert%"
        #     OR ...
        # --------------------------------------------------------------

        search_conditions = []

        for term in search_terms:
            pattern = f"%{term}%"

            search_conditions.extend(
                [
                    Paper.title.ilike(
                        pattern
                    ),
                    Paper.abstract.ilike(
                        pattern
                    ),
                    Paper.arxiv_id.ilike(
                        pattern
                    ),
                    Paper.doi.ilike(
                        pattern
                    ),
                    Paper.pmid.ilike(
                        pattern
                    ),
                    Paper.provider_paper_id.ilike(
                        pattern
                    ),
                ]
            )

        stmt = (
            select(Paper)
            .where(
                or_(
                    *search_conditions
                )
            )
            .limit(
                max(
                    limit * 5,
                    25,
                )
            )
        )

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    stmt
                )

                papers = result.scalars().all()

        except Exception:
            logger.exception(
                "PostgreSQL paper search failed",
                extra={
                    "query": query,
                    "search_terms": search_terms,
                },
            )
            return []

        # --------------------------------------------------------------
        # Normalize and calculate deterministic lexical relevance.
        # --------------------------------------------------------------

        normalized_results: list[
            Mapping[str, Any]
        ] = []

        for paper in papers:
            content = (
                paper.abstract.strip()
                if paper.abstract
                and paper.abstract.strip()
                else ""
            )

            # A paper without abstract/content cannot become a useful
            # RetrievedDocument at this stage.
            if not content:
                logger.debug(
                    "Skipping paper without abstract",
                    extra={
                        "paper_id": paper.id,
                        "title": paper.title,
                    },
                )
                continue

            score = self._calculate_database_score(
                paper,
                query,
            )

            # Do not return papers that matched only a weak/irrelevant
            # identifier fragment.
            if score <= 0.0:
                continue

            normalized_results.append(
                {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "authors": [],
                    "year": paper.year,
                    "url": (
                        paper.landing_page_url
                        or paper.pdf_url
                    ),
                    "content": content,
                    "score": score,
                    "doi": paper.doi,
                    "arxiv_id": paper.arxiv_id,
                    "pmid": paper.pmid,
                    "provider": paper.provider,
                    "provider_paper_id": paper.provider_paper_id,
                    "retrieval_source": "postgresql",
                    "metadata": {
                        "paper_id": paper.id,
                        "citation_count": paper.citation_count,
                        "reference_count": paper.reference_count,
                        "language": paper.language,
                        "publication_date": (
                            paper.publication_date.isoformat()
                            if paper.publication_date
                            else None
                        ),
                        "search_terms": search_terms,
                    },
                }
            )

        # --------------------------------------------------------------
        # Deterministic ranking:
        #
        # 1. relevance score
        # 2. citation count
        # 3. publication year
        # 4. database ID
        # --------------------------------------------------------------

        normalized_results.sort(
            key=lambda item: (
                self._safe_score(
                    item.get(
                        "score",
                        0.0,
                    )
                ),
                self._safe_number(
                    item.get(
                        "metadata",
                        {},
                    ).get(
                        "citation_count",
                        0,
                    )
                ),
                self._safe_year(
                    item.get(
                        "year"
                    )
                )
                or 0,
                self._safe_number(
                    item.get(
                        "paper_id"
                    )
                ),
            ),
            reverse=True,
        )

        normalized_results = normalized_results[
            :limit
        ]

        logger.info(
            "PostgreSQL paper search completed: "
            "query=%r terms=%r results=%d",
            query,
            search_terms,
            len(normalized_results),
        )

        return normalized_results

    # ==================================================================
    # QUERY TERM EXTRACTION
    # ==================================================================

    @classmethod
    def _extract_search_terms(
        cls,
        query: str,
    ) -> list[str]:
        """
        Extract meaningful lexical terms from a natural-language query.

        Examples:

            "what you know about bert"
                -> ["bert"]

            "tell me about transformer architecture"
                -> ["transformer", "architecture"]

            "what is attention is all you need"
                -> ["attention", "all", "need"]

        The result is intentionally lexical rather than semantic.
        """

        normalized = query.lower().strip()

        if not normalized:
            return []

        # Keep alphanumeric technical tokens and common identifiers.
        tokens = re.findall(
            r"[a-zA-Z0-9][a-zA-Z0-9._:/-]*",
            normalized,
        )

        terms: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            token = token.strip(
                "._:/-"
            )

            if not token:
                continue

            if token in cls._QUERY_STOP_WORDS:
                continue

            if len(token) < cls._MIN_QUERY_TERM_LENGTH:
                continue

            # Ignore pure numeric fragments unless they resemble a
            # meaningful year.
            if token.isdigit():
                if len(token) != 4:
                    continue

            if token in seen:
                continue

            seen.add(
                token
            )
            terms.append(
                token
            )

        return terms

    @classmethod
    def _fallback_search_terms(
        cls,
        query: str,
    ) -> list[str]:
        """
        Conservative fallback when stop-word filtering removes
        everything useful.
        """

        tokens = re.findall(
            r"[a-zA-Z0-9][a-zA-Z0-9._:/-]*",
            query.lower(),
        )

        terms: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            token = token.strip(
                "._:/-"
            )

            if (
                len(token)
                < cls._MIN_QUERY_TERM_LENGTH
            ):
                continue

            if token in seen:
                continue

            seen.add(
                token
            )
            terms.append(
                token
            )

        return terms[:8]

    # ==================================================================
    # DATABASE RELEVANCE SCORE
    # ==================================================================

    @classmethod
    def _calculate_database_score(
        cls,
        paper: Paper,
        query: str,
    ) -> float:
        """
        Calculate a deterministic lexical relevance score.

        This is NOT a semantic similarity score.

        Scoring priority:

        - exact title match
        - phrase contained in title
        - meaningful-term title overlap
        - meaningful-term abstract overlap
        - identifier matches

        Title matches receive substantially more weight than abstract
        matches because they are generally stronger evidence that the
        paper is about the requested topic.

        The score is normalized to [0, 1].
        """

        query_normalized = cls._normalize_text(
            query
        )

        title_normalized = cls._normalize_text(
            paper.title or ""
        )

        abstract_normalized = cls._normalize_text(
            paper.abstract or ""
        )

        arxiv_normalized = cls._normalize_text(
            paper.arxiv_id or ""
        )

        doi_normalized = cls._normalize_text(
            paper.doi or ""
        )

        pmid_normalized = cls._normalize_text(
            paper.pmid or ""
        )

        provider_id_normalized = cls._normalize_text(
            paper.provider_paper_id or ""
        )

        # --------------------------------------------------------------
        # Exact title match
        # --------------------------------------------------------------

        if (
            query_normalized
            and query_normalized == title_normalized
        ):
            return 1.0

        # --------------------------------------------------------------
        # Query phrase contained in title
        # --------------------------------------------------------------

        if (
            query_normalized
            and query_normalized in title_normalized
        ):
            return 0.95

        terms = cls._extract_search_terms(
            query
        )

        if not terms:
            terms = cls._fallback_search_terms(
                query
            )

        if not terms:
            return 0.0

        title_tokens = set(
            cls._tokenize_text(
                title_normalized
            )
        )

        abstract_tokens = set(
            cls._tokenize_text(
                abstract_normalized
            )
        )

        # --------------------------------------------------------------
        # Meaningful term overlap
        # --------------------------------------------------------------

        title_hits = sum(
            1
            for term in terms
            if cls._term_matches(
                term,
                title_tokens,
            )
        )

        abstract_hits = sum(
            1
            for term in terms
            if cls._term_matches(
                term,
                abstract_tokens,
            )
        )

        title_ratio = (
            title_hits / len(terms)
        )

        abstract_ratio = (
            abstract_hits / len(terms)
        )

        # --------------------------------------------------------------
        # Identifier matching
        # --------------------------------------------------------------

        identifier_text = " ".join(
            value
            for value in (
                arxiv_normalized,
                doi_normalized,
                pmid_normalized,
                provider_id_normalized,
            )
            if value
        )

        identifier_hits = sum(
            1
            for term in terms
            if term in identifier_text
        )

        identifier_ratio = (
            identifier_hits / len(terms)
        )

        # --------------------------------------------------------------
        # Weighted lexical score
        #
        # Title is strongest.
        # Abstract provides supporting evidence.
        # Identifier matching is useful but deliberately weak.
        # --------------------------------------------------------------

        score = (
            0.60 * title_ratio
            + 0.35 * abstract_ratio
            + 0.05 * identifier_ratio
        )

        # --------------------------------------------------------------
        # Strong single-term title match.
        #
        # This is particularly important for queries such as:
        #
        #     "what you know about bert"
        #
        # where BERT may be the only meaningful term.
        # --------------------------------------------------------------

        if (
            len(terms) == 1
            and title_hits == 1
        ):
            score = max(
                score,
                0.90,
            )

        # --------------------------------------------------------------
        # Any strong exact token title match deserves a meaningful
        # score even if the abstract is unavailable/weak.
        # --------------------------------------------------------------

        if title_hits > 0:
            score = max(
                score,
                0.60 * title_ratio,
            )

        # --------------------------------------------------------------
        # No meaningful lexical overlap means no relevance.
        # --------------------------------------------------------------

        if (
            title_hits == 0
            and abstract_hits == 0
            and identifier_hits == 0
        ):
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

    # ==================================================================
    # TEXT NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        """
        Normalize text for deterministic lexical matching.
        """

        value = (
            value
            or ""
        ).lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _tokenize_text(
        value: str,
    ) -> list[str]:
        """
        Tokenize normalized text.
        """

        return re.findall(
            r"[a-zA-Z0-9][a-zA-Z0-9._:/-]*",
            value,
        )

    @staticmethod
    def _term_matches(
        term: str,
        tokens: set[str],
    ) -> bool:
        """
        Determine whether a query term matches a document token.

        Exact token matching is preferred.

        For longer technical terms, a contained-token match is allowed
        to handle simple morphological/identifier variations without
        turning the whole search into unrestricted substring matching.
        """

        if term in tokens:
            return True

        if len(term) < 4:
            return False

        for token in tokens:
            if (
                term in token
                or token in term
            ):
                return True

        return False

    # ==================================================================
    # PAPER NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_paper(
        paper: Mapping[str, Any] | Any,
    ) -> dict[str, Any] | None:
        """
        Normalize an external or database paper result.

        Invalid or content-less papers are rejected.
        """

        if not isinstance(
            paper,
            Mapping,
        ):
            return None

        title = str(
            paper.get(
                "title"
            )
            or ""
        ).strip()

        content = str(
            paper.get(
                "content"
            )
            or paper.get(
                "text"
            )
            or paper.get(
                "abstract"
            )
            or ""
        ).strip()

        if not title:
            return None

        if not content:
            return None

        authors_value = paper.get(
            "authors",
            [],
        )

        if isinstance(
            authors_value,
            str,
        ):
            authors = (
                [
                    authors_value.strip()
                ]
                if authors_value.strip()
                else []
            )

        elif isinstance(
            authors_value,
            Sequence,
        ) and not isinstance(
            authors_value,
            (str, bytes),
        ):
            authors = [
                str(author).strip()
                for author in authors_value
                if str(author).strip()
            ]

        else:
            authors = []

        score = PaperRetriever._safe_score(
            paper.get(
                "score",
                0.0,
            )
        )

        year = PaperRetriever._safe_year(
            paper.get(
                "year"
            )
        )

        url = paper.get(
            "url"
        )

        if url is not None:
            url = str(
                url
            ).strip() or None

        metadata = paper.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            metadata = {}

        return {
            "paper_id": paper.get(
                "paper_id"
            ),
            "title": title,
            "authors": authors,
            "year": year,
            "url": url,
            "content": content,
            "score": score,
            "doi": paper.get(
                "doi"
            ),
            "arxiv_id": paper.get(
                "arxiv_id"
            ),
            "pmid": paper.get(
                "pmid"
            ),
            "provider": paper.get(
                "provider"
            ),
            "provider_paper_id": paper.get(
                "provider_paper_id"
            ),
            "metadata": dict(
                metadata
            ),
            "retrieval_source": paper.get(
                "retrieval_source",
                "paper",
            ),
        }

    # ==================================================================
    # SAFE SCORE
    # ==================================================================

    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:
        """
        Normalize a score into [0, 1].
        """

        try:
            score = float(
                value
            )

            if score != score:
                return 0.0

            if score == float(
                "inf"
            ):
                return 0.0

            if score == float(
                "-inf"
            ):
                return 0.0

            return max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

    # ==================================================================
    # SAFE YEAR
    # ==================================================================

    @staticmethod
    def _safe_year(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            year = int(
                value
            )

            if 0 < year <= 9999:
                return year

        except (
            TypeError,
            ValueError,
        ):
            pass

        return None

    # ==================================================================
    # SAFE NUMBER
    # ==================================================================

    @staticmethod
    def _safe_number(
        value: Any,
    ) -> int:
        """
        Convert a value to an integer for deterministic sorting.
        """

        if value is None:
            return 0

        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

    # ==================================================================
    # DEDUPLICATION
    # ==================================================================

    @staticmethod
    def _deduplication_key(
        paper: Mapping[str, Any],
    ) -> str:
        """
        Prefer stable database/provider identifiers.

        Fall back to URL and finally normalized title.
        """

        paper_id = paper.get(
            "paper_id"
        )

        if paper_id is not None:
            return (
                f"paper_id:{paper_id}"
            )

        provider = paper.get(
            "provider"
        )

        provider_paper_id = paper.get(
            "provider_paper_id"
        )

        if (
            provider
            and provider_paper_id
        ):
            return (
                "provider:"
                f"{str(provider).lower()}:"
                f"{str(provider_paper_id).lower()}"
            )

        arxiv_id = paper.get(
            "arxiv_id"
        )

        if arxiv_id:
            return (
                "arxiv:"
                f"{str(arxiv_id).lower()}"
            )

        doi = paper.get(
            "doi"
        )

        if doi:
            return (
                "doi:"
                f"{str(doi).lower()}"
            )

        url = paper.get(
            "url"
        )

        if url:
            return (
                "url:"
                f"{str(url).strip().lower()}"
            )

        title = str(
            paper.get(
                "title"
            )
            or ""
        ).strip().lower()

        return (
            "title:"
            + " ".join(
                title.split()
            )
        )


__all__ = [
    "PaperRetriever",
    "PaperSearchFunction",
]