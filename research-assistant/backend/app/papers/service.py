from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.ingestion.processing.resolver import PaperResolver
from app.ingestion.providers.base import ProviderPaper
from app.ingestion.providers.manager import ProviderManager

from app.papers.domain.paper import (
    Paper as DomainPaper,
    PaperAuthor,
)

from app.papers.schemas.paper import (
    PaperCreate,
    PaperListResponse,
    PaperResponse,
    PaperUpdate,
)

from app.papers.schemas.search import (
    PaperSearchRequest,
    PaperSearchResponse,
    PaperSearchResult,
)

logger = logging.getLogger(__name__)


# ============================================================
# ERRORS
# ============================================================


class PaperAlreadyExistsError(Exception):
    """Raised when a paper already exists."""

    def __init__(self, paper: Any) -> None:
        self.paper = paper

        canonical_key = getattr(
            paper,
            "canonical_key",
            None,
        )

        if not canonical_key:
            canonical_key = self._derive_canonical_key(
                paper
            )

        super().__init__(
            f"Paper already exists: {canonical_key}"
        )

    @staticmethod
    def _derive_canonical_key(
        paper: Any,
    ) -> str:
        doi = getattr(
            paper,
            "doi",
            None,
        )

        if doi:
            return f"doi:{doi}"

        arxiv_id = getattr(
            paper,
            "arxiv_id",
            None,
        )

        if arxiv_id:
            return f"arxiv:{arxiv_id}"

        pmid = getattr(
            paper,
            "pmid",
            None,
        )

        if pmid:
            return f"pmid:{pmid}"

        provider = getattr(
            paper,
            "provider",
            None,
        )

        provider_id = getattr(
            paper,
            "provider_paper_id",
            None,
        )

        if provider and provider_id:
            return f"{provider}:{provider_id}"

        return "unknown"


class PaperNotFoundError(Exception):
    """Raised when a requested paper does not exist."""


# ============================================================
# UPSERT RESULT
# ============================================================


@dataclass(slots=True)
class PaperUpsertResult:
    paper: Any
    created: bool
    duplicate: bool


# ============================================================
# PAPER SERVICE
# ============================================================


class PaperService:
    """
    Application service for the canonical paper catalog.

    Responsibilities:
        - CRUD
        - Search
        - Pagination
        - Duplicate detection
        - External ID normalization
        - Provider ingestion
        - Provider discovery
        - ProviderPaper -> DomainPaper conversion
        - Author synchronization
        - Response serialization
    """

    PROVIDER_SEARCH_MIN_QUERY_LENGTH = 3
    PROVIDER_SEARCH_LIMIT = 20

    def __init__(
        self,
        repository: Any,
        resolver: PaperResolver | None = None,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        self.repository = repository

        self.resolver = (
            resolver
            if resolver is not None
            else PaperResolver()
        )

        self.provider_manager = provider_manager

    # ========================================================
    # PROVIDER MANAGER
    # ========================================================

    def _get_provider_manager(
        self,
    ) -> ProviderManager:
        """Return the configured ProviderManager."""

        if self.provider_manager is None:
            raise RuntimeError(
                "ProviderManager is not configured for PaperService. "
                "Pass provider_manager=ProviderManager(...) "
                "when creating PaperService."
            )

        return self.provider_manager

    # ========================================================
    # SEARCH REQUEST BUILDER
    # ========================================================

    def _build_search_request(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        query: str | None = None,
        year: int | None = None,
        venue: str | None = None,
        author: str | None = None,
        doi: str | None = None,
        source: str | None = None,
        provider: str | None = None,
        provider_paper_id: str | None = None,
        category: str | None = None,
        published_from: date | None = None,
        published_to: date | None = None,
        sort_by: str = "publication_date",
        sort_order: str = "desc",
    ) -> PaperSearchRequest:

        page = max(
            int(page),
            1,
        )

        page_size = min(
            max(int(page_size), 1),
            100,
        )

        sort_by = (
            self._clean_string(sort_by)
            or "publication_date"
        )

        sort_order = (
            self._clean_string(sort_order)
            or "desc"
        ).lower()

        if sort_order not in {"asc", "desc"}:
            raise ValueError(
                "sort_order must be either 'asc' or 'desc'"
            )

        allowed_sort_fields = {
            "publication_date",
            "title",
            "citation_count",
            "created_at",
            "updated_at",
            "year",
        }

        if sort_by not in allowed_sort_fields:
            raise ValueError(
                "Unsupported sort_by value. "
                f"Supported values: "
                f"{', '.join(sorted(allowed_sort_fields))}"
            )

        if (
            published_from is not None
            and published_to is not None
            and published_from > published_to
        ):
            raise ValueError(
                "published_from cannot be after published_to"
            )

        return PaperSearchRequest(
            query=self._clean_string(query),
            author=self._clean_string(author),
            doi=(
                self.resolver.normalize_doi(doi)
                if doi
                else None
            ),
            source=self._clean_string(source),
            provider=self._clean_string(provider),
            provider_paper_id=self._clean_string(
                provider_paper_id
            ),
            venue=self._clean_string(venue),
            category=self._clean_string(category),
            year=year,
            published_from=published_from,
            published_to=published_to,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    # ========================================================
    # LIST
    # ========================================================

    async def list_papers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        query: str | None = None,
        year: int | None = None,
        venue: str | None = None,
        author: str | None = None,
        doi: str | None = None,
        source: str | None = None,
        provider: str | None = None,
        provider_paper_id: str | None = None,
        category: str | None = None,
        published_from: date | None = None,
        published_to: date | None = None,
        sort_by: str = "publication_date",
        sort_order: str = "desc",
    ) -> PaperListResponse:

        request = self._build_search_request(
            page=page,
            page_size=page_size,
            query=query,
            year=year,
            venue=venue,
            author=author,
            doi=doi,
            source=source,
            provider=provider,
            provider_paper_id=provider_paper_id,
            category=category,
            published_from=published_from,
            published_to=published_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        papers, total = await self.repository.search(
            request
        )

        total = max(
            int(total or 0),
            0,
        )

        pages = (
            math.ceil(
                total / request.page_size
            )
            if total > 0
            else 0
        )

        return PaperListResponse(
            items=[
                self._to_response(paper)
                for paper in papers
            ],
            total=total,
            page=request.page,
            page_size=request.page_size,
            pages=pages,
        )

    # ========================================================
    # SEARCH
    # ========================================================

    async def search_papers(
        self,
        *,
        query: str | None = None,
        page: int = 1,
        page_size: int = 20,
        year: int | None = None,
        venue: str | None = None,
        author: str | None = None,
        doi: str | None = None,
        source: str | None = None,
        provider: str | None = None,
        provider_paper_id: str | None = None,
        category: str | None = None,
        published_from: date | None = None,
        published_to: date | None = None,
        sort_by: str = "publication_date",
        sort_order: str = "desc",
    ) -> PaperSearchResponse:

        request = self._build_search_request(
            page=page,
            page_size=page_size,
            query=query,
            year=year,
            venue=venue,
            author=author,
            doi=doi,
            source=source,
            provider=provider,
            provider_paper_id=provider_paper_id,
            category=category,
            published_from=published_from,
            published_to=published_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # ----------------------------------------------------
        # STEP 1: Search canonical local catalog
        # ----------------------------------------------------

        papers, total = await self.repository.search(
            request
        )

        total = max(
            int(total or 0),
            0,
        )

        logger.debug(
            "Local paper search completed: "
            "query=%r author=%r provider=%r total=%d",
            request.query,
            request.author,
            request.provider,
            total,
        )

        # ----------------------------------------------------
        # STEP 2: Determine external discovery query
        # ----------------------------------------------------

        discovery_query = self._build_discovery_query(
            request
        )

        should_discover = (
            bool(discovery_query)
            and len(discovery_query)
            >= self.PROVIDER_SEARCH_MIN_QUERY_LENGTH
            and not request.provider_paper_id
        )

        # ----------------------------------------------------
        # STEP 3: External provider discovery
        # ----------------------------------------------------

        if should_discover:
            try:
                processed = await self._discover_provider_papers(
                    query=discovery_query,
                    provider=request.provider,
                )

                logger.info(
                    "Provider discovery completed: "
                    "query=%r original_query=%r author=%r "
                    "provider=%r processed=%d",
                    discovery_query,
                    request.query,
                    request.author,
                    request.provider,
                    processed,
                )

            except Exception:
                logger.exception(
                    "External provider discovery failed: "
                    "discovery_query=%r original_query=%r "
                    "author=%r provider=%r",
                    discovery_query,
                    request.query,
                    request.author,
                    request.provider,
                )

            # ------------------------------------------------
            # STEP 4: Search canonical DB again
            # ------------------------------------------------

            papers, total = await self.repository.search(
                request
            )

            total = max(
                int(total or 0),
                0,
            )

            logger.debug(
                "Post-discovery paper search completed: "
                "query=%r author=%r total=%d",
                request.query,
                request.author,
                total,
            )

        # ----------------------------------------------------
        # STEP 5: Response
        # ----------------------------------------------------

        total_pages = (
            math.ceil(
                total / request.page_size
            )
            if total > 0
            else 0
        )

        return PaperSearchResponse(
            papers=[
                self._to_search_result(paper)
                for paper in papers
            ],
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )

    # ========================================================
    # DISCOVERY QUERY
    # ========================================================

    @staticmethod
    def _build_discovery_query(
        request: PaperSearchRequest,
    ) -> str | None:
        """
        Build the query sent to external providers.

        Priority:
            1. Explicit paper query
            2. Author query

        The local repository remains responsible for applying
        the complete set of filters after provider ingestion.

        Example:

            query="Attention Is All You Need"
                -> provider query:
                   "Attention Is All You Need"

            author="Ashish Vaswani"
                -> provider query:
                   "Ashish Vaswani"

            query="transformers", author="Ashish Vaswani"
                -> provider query:
                   "transformers"

        We deliberately do not concatenate query + author because
        provider search engines interpret free-text queries
        differently. The local database search performs the exact
        author filtering afterward.
        """

        query = (
            request.query.strip()
            if request.query
            else ""
        )

        if query:
            return query

        author = (
            request.author.strip()
            if request.author
            else ""
        )

        if author:
            return author

        return None

    # ========================================================
    # PROVIDER DISCOVERY
    # ========================================================

    async def _discover_provider_papers(
        self,
        *,
        query: str,
        provider: str | None = None,
    ) -> int:
        """
        Search external providers and persist discovered papers.

        ProviderManager.search() expects:

            provider=...
            limit=...
            offset=...

        When provider is None, ProviderManager searches all
        configured providers.
        """

        manager = self._get_provider_manager()

        normalized_provider = (
            provider.strip().lower()
            if provider
            else None
        )

        logger.info(
            "Searching external providers: "
            "query=%r provider=%r limit=%d offset=%d",
            query,
            normalized_provider,
            self.PROVIDER_SEARCH_LIMIT,
            0,
        )

        provider_papers = await manager.search(
            query,
            provider=normalized_provider,
            limit=self.PROVIDER_SEARCH_LIMIT,
            offset=0,
        )

        logger.info(
            "External provider search returned %d results: "
            "query=%r provider=%r",
            len(provider_papers),
            query,
            normalized_provider,
        )

        if not provider_papers:
            logger.info(
                "No external provider results for "
                "query=%r provider=%r",
                query,
                normalized_provider,
            )
            return 0

        processed = 0

        for index, provider_paper in enumerate(
            provider_papers,
            start=1,
        ):
            if not isinstance(
                provider_paper,
                ProviderPaper,
            ):
                logger.warning(
                    "Skipping invalid provider search result: "
                    "index=%d type=%s",
                    index,
                    type(provider_paper).__name__,
                )
                continue

            current_provider = (
                getattr(
                    provider_paper,
                    "provider",
                    None,
                )
                or "unknown"
            )

            current_provider_id = getattr(
                provider_paper,
                "provider_id",
                None,
            )

            logger.debug(
                "Provider result received: "
                "index=%d provider=%s provider_id=%s "
                "title=%r",
                index,
                current_provider,
                current_provider_id,
                provider_paper.title,
            )

            try:
                domain_paper = (
                    self._provider_paper_to_domain(
                        provider_paper
                    )
                )

                title = self.resolver.normalize_title(
                    getattr(
                        domain_paper,
                        "title",
                        "",
                    )
                )

                if not title:
                    logger.warning(
                        "Skipping provider paper with empty title: "
                        "provider=%s id=%s",
                        current_provider,
                        current_provider_id,
                    )
                    continue

                result = await self.upsert_domain_paper(
                    domain_paper
                )

                processed += 1

                logger.debug(
                    "Provider paper processed: "
                    "provider=%s id=%s created=%s duplicate=%s "
                    "title=%r",
                    current_provider,
                    current_provider_id,
                    result.created,
                    result.duplicate,
                    title,
                )

            except Exception:
                logger.exception(
                    "Failed to persist provider paper: "
                    "provider=%s id=%s title=%r",
                    current_provider,
                    current_provider_id,
                    getattr(
                        provider_paper,
                        "title",
                        None,
                    ),
                )

        logger.info(
            "Processed %d external provider papers "
            "for query=%r provider=%r",
            processed,
            query,
            normalized_provider,
        )

        return processed

    # ========================================================
    # GET
    # ========================================================

    async def get_paper(
        self,
        paper_id: int | str,
    ) -> Any | None:
        return await self.repository.get_by_id(
            paper_id,
            load_relationships=True,
        )

    async def get(
        self,
        paper_id: int | str,
    ) -> Any:
        paper = await self.get_paper(
            paper_id
        )

        if paper is None:
            raise PaperNotFoundError(
                f"Paper not found: {paper_id}"
            )

        return paper

    # ========================================================
    # CREATE
    # ========================================================

    async def create(
        self,
        data: PaperCreate,
    ) -> Any:
        from app.db.models.paper import Paper

        doi = self.resolver.normalize_doi(
            data.doi
        )

        if doi:
            existing = await self.repository.find_existing(
                doi=doi
            )

            if existing is not None:
                raise PaperAlreadyExistsError(
                    existing
                )

        metadata = dict(
            data.metadata or {}
        )

        title = self.resolver.normalize_title(
            data.title
        )

        if not title:
            raise ValueError(
                "Paper title cannot be empty"
            )

        publication_date = data.publication_date
        publication_datetime = None

        if isinstance(
            publication_date,
            datetime,
        ):
            publication_datetime = publication_date

        elif isinstance(
            publication_date,
            date,
        ):
            publication_datetime = datetime.combine(
                publication_date,
                datetime.min.time(),
            )

        year = (
            publication_datetime.year
            if publication_datetime is not None
            else None
        )

        paper = Paper(
            provider="manual",
            provider_paper_id=None,
            doi=doi,
            arxiv_id=None,
            pmid=None,
            title=title,
            abstract=data.abstract,
            publication_date=publication_datetime,
            year=year,
            language=data.language,
            citation_count=max(
                int(
                    data.citation_count or 0
                ),
                0,
            ),
            reference_count=max(
                int(
                    data.reference_count or 0
                ),
                0,
            ),
            landing_page_url=data.url,
            pdf_url=data.pdf_url,
            source_metadata=self._serialize_metadata(
                metadata
            ),
        )

        return await self.repository.create(
            paper
        )

    # ========================================================
    # INGEST
    # ========================================================

    async def ingest_paper(
        self,
        *,
        provider: str,
        external_id: str,
    ) -> Any:

        provider = (
            provider.strip().lower()
            if provider
            else ""
        )

        external_id = (
            external_id.strip()
            if external_id
            else ""
        )

        if not provider:
            raise ValueError(
                "Provider cannot be empty"
            )

        if not external_id:
            raise ValueError(
                "External ID cannot be empty"
            )

        normalized_id = self._normalize_external_id(
            self.resolver,
            provider,
            external_id,
        )

        if not normalized_id:
            raise ValueError(
                f"Invalid external ID for provider: "
                f"{provider}"
            )

        existing = (
            await self.repository.get_by_external_id(
                provider,
                normalized_id,
            )
        )

        if existing is not None:
            return existing

        manager = self._get_provider_manager()

        provider_paper = await manager.get_by_id(
            provider_name=provider,
            provider_id=normalized_id,
        )

        if provider_paper is None:
            raise ValueError(
                f"Paper not found from provider "
                f"'{provider}': {normalized_id}"
            )

        if not isinstance(
            provider_paper,
            ProviderPaper,
        ):
            raise TypeError(
                "ProviderManager.get_by_id() returned "
                f"unexpected type: "
                f"{type(provider_paper).__name__}"
            )

        domain_paper = self._provider_paper_to_domain(
            provider_paper
        )

        result = await self.upsert_domain_paper(
            domain_paper
        )

        return result.paper

    # ========================================================
    # PROVIDER PAPER -> DOMAIN PAPER
    # ========================================================

    def _provider_paper_to_domain(
        self,
        provider_paper: ProviderPaper,
    ) -> DomainPaper:

        provider = (
            provider_paper.provider
            or "unknown"
        ).strip().lower()

        provider_id = (
            str(
                provider_paper.provider_id
            ).strip()
            if provider_paper.provider_id
            else None
        )

        external_ids: dict[str, str] = {}

        if provider_id:
            external_ids[provider] = provider_id

        if provider == "arxiv" and provider_id:
            external_ids["arxiv"] = provider_id

        authors: list[PaperAuthor] = []

        for index, author in enumerate(
            provider_paper.authors or []
        ):
            if isinstance(
                author,
                PaperAuthor,
            ):
                paper_author = author

            elif isinstance(
                author,
                str,
            ):
                name = author.strip()

                if not name:
                    continue

                paper_author = PaperAuthor(
                    name=name,
                    position=index,
                )

            elif isinstance(
                author,
                dict,
            ):
                name = str(
                    author.get(
                        "name",
                        author.get(
                            "full_name",
                            "",
                        ),
                    )
                ).strip()

                if not name:
                    continue

                paper_author = PaperAuthor(
                    name=name,
                    author_id=(
                        str(
                            author["author_id"]
                        )
                        if author.get(
                            "author_id"
                        )
                        else None
                    ),
                    orcid=(
                        str(
                            author["orcid"]
                        )
                        if author.get(
                            "orcid"
                        )
                        else None
                    ),
                    email=(
                        str(
                            author["email"]
                        )
                        if author.get(
                            "email"
                        )
                        else None
                    ),
                    affiliation=(
                        str(
                            author["affiliation"]
                        )
                        if author.get(
                            "affiliation"
                        )
                        else None
                    ),
                    position=index,
                )

            else:
                name = str(
                    author
                ).strip()

                if not name:
                    continue

                paper_author = PaperAuthor(
                    name=name,
                    position=index,
                )

            authors.append(
                paper_author
            )

        metadata = dict(
            provider_paper.raw_data or {}
        )

        metadata["provider"] = provider
        metadata["provider_id"] = provider_id

        if provider_paper.authors:
            metadata["authors"] = list(
                provider_paper.authors
            )

        if provider_paper.venue:
            metadata["venue"] = (
                provider_paper.venue
            )

        if provider_paper.journal:
            metadata["journal"] = (
                provider_paper.journal
            )

        categories: list[str] = []

        raw_data = (
            provider_paper.raw_data
            or {}
        )

        raw_categories = raw_data.get(
            "categories",
            [],
        )

        if isinstance(
            raw_categories,
            str,
        ):
            categories = [
                raw_categories
            ]

        elif isinstance(
            raw_categories,
            (list, tuple),
        ):
            categories = [
                str(value)
                for value in raw_categories
                if value
            ]

        if not categories:
            tags = raw_data.get(
                "tags",
                [],
            )

            if isinstance(
                tags,
                list,
            ):
                for tag in tags:
                    if isinstance(
                        tag,
                        dict,
                    ):
                        term = tag.get(
                            "term"
                        )

                        if term:
                            categories.append(
                                str(term)
                            )

        return DomainPaper(
            title=self.resolver.normalize_title(
                provider_paper.title or ""
            ),
            abstract=provider_paper.abstract,
            authors=authors,
            doi=self.resolver.normalize_doi(
                provider_paper.doi
            ),
            url=provider_paper.url,
            pdf_url=provider_paper.pdf_url,
            publication_date=(
                provider_paper.published_at
            ),
            venue=provider_paper.venue,
            journal=provider_paper.journal,
            categories=categories,
            citation_count=max(
                int(
                    provider_paper.citation_count
                    or 0
                ),
                0,
            ),
            reference_count=0,
            source=provider,
            external_ids=external_ids,
            metadata=metadata,
        )

    # ========================================================
    # UPDATE
    # ========================================================

    async def update(
        self,
        paper_id: int | str,
        data: PaperUpdate,
    ) -> Any:

        paper = await self.repository.get_by_id(
            paper_id
        )

        if paper is None:
            raise PaperNotFoundError(
                f"Paper not found: {paper_id}"
            )

        values = data.model_dump(
            exclude_unset=True
        )

        if (
            "title" in values
            and values["title"]
        ):
            values["title"] = (
                self.resolver.normalize_title(
                    values["title"]
                )
            )

        if "doi" in values:
            values["doi"] = (
                self.resolver.normalize_doi(
                    values["doi"]
                )
            )

            if values["doi"]:
                existing = (
                    await self.repository.get_by_doi(
                        values["doi"]
                    )
                )

                current_id = getattr(
                    paper,
                    "id",
                    None,
                )

                existing_id = (
                    getattr(
                        existing,
                        "id",
                        None,
                    )
                    if existing is not None
                    else None
                )

                if (
                    existing is not None
                    and existing_id != current_id
                ):
                    raise PaperAlreadyExistsError(
                        existing
                    )

        if "publication_date" in values:
            publication_date = values[
                "publication_date"
            ]

            if isinstance(
                publication_date,
                datetime,
            ):
                values["year"] = (
                    publication_date.year
                )

            elif isinstance(
                publication_date,
                date,
            ):
                values["publication_date"] = (
                    datetime.combine(
                        publication_date,
                        datetime.min.time(),
                    )
                )

                values["year"] = (
                    publication_date.year
                )

            elif publication_date is None:
                values["year"] = None

        if "url" in values:
            values["landing_page_url"] = (
                values.pop("url")
            )

        values.pop(
            "authors",
            None,
        )

        updated = await self.repository.update(
            paper_id,
            values,
        )

        if updated is None:
            raise PaperNotFoundError(
                f"Paper not found: {paper_id}"
            )

        return updated

    # ========================================================
    # DELETE
    # ========================================================

    async def delete_paper(
        self,
        paper_id: int | str,
    ) -> bool:
        return await self.repository.delete(
            paper_id
        )

    async def delete(
        self,
        paper_id: int | str,
    ) -> None:

        deleted = await self.repository.delete(
            paper_id
        )

        if not deleted:
            raise PaperNotFoundError(
                f"Paper not found: {paper_id}"
            )

    # ========================================================
    # DUPLICATE LOOKUP
    # ========================================================

    async def find_duplicate(
        self,
        paper: DomainPaper,
    ) -> Any | None:

        doi = self.resolver.normalize_doi(
            getattr(
                paper,
                "doi",
                None,
            )
        )

        if doi:
            existing = (
                await self.repository.get_by_doi(
                    doi
                )
            )

            if existing is not None:
                return existing

        external_ids = (
            getattr(
                paper,
                "external_ids",
                {},
            )
            or {}
        )

        for provider in (
            "arxiv",
            "openalex",
            "semantic_scholar",
            "pmid",
            "crossref",
        ):
            external_id = external_ids.get(
                provider
            )

            if not external_id:
                continue

            normalized_id = (
                self._normalize_external_id(
                    self.resolver,
                    provider,
                    str(external_id),
                )
            )

            if not normalized_id:
                continue

            if provider == "arxiv":
                existing = (
                    await self.repository.get_by_arxiv_id(
                        normalized_id
                    )
                )

            elif provider == "pmid":
                existing = (
                    await self.repository.get_by_pmid(
                        normalized_id
                    )
                )

            else:
                existing = (
                    await self.repository.get_by_provider_id(
                        provider,
                        normalized_id,
                    )
                )

            if existing is not None:
                return existing

        canonical_key = (
            self._get_domain_canonical_key(
                paper
            )
        )

        if canonical_key:
            existing = (
                await self.repository.get_by_canonical_key(
                    canonical_key
                )
            )

            if existing is not None:
                return existing

        return None

    # ========================================================
    # UPSERT DOMAIN PAPER
    # ========================================================

    async def upsert_domain_paper(
        self,
        paper: DomainPaper,
    ) -> PaperUpsertResult:

        existing = await self.find_duplicate(
            paper
        )

        if existing is not None:
            domain_authors = (
                getattr(
                    paper,
                    "authors",
                    None,
                )
                or []
            )

            if domain_authors:
                existing = (
                    await self.repository.sync_authors(
                        existing,
                        domain_authors,
                    )
                )

            return PaperUpsertResult(
                paper=existing,
                created=False,
                duplicate=True,
            )

        from app.db.models.paper import Paper

        title = self.resolver.normalize_title(
            getattr(
                paper,
                "title",
                "",
            )
        )

        if not title:
            raise ValueError(
                "Cannot persist paper with empty title"
            )

        doi = self.resolver.normalize_doi(
            getattr(
                paper,
                "doi",
                None,
            )
        )

        external_ids = (
            getattr(
                paper,
                "external_ids",
                {},
            )
            or {}
        )

        provider = (
            getattr(
                paper,
                "source",
                None,
            )
            or "unknown"
        )

        provider = provider.strip().lower()

        provider_paper_id = external_ids.get(
            provider
        )

        if provider_paper_id:
            provider_paper_id = str(
                provider_paper_id
            ).strip()

        publication_date = getattr(
            paper,
            "publication_date",
            None,
        )

        if (
            isinstance(
                publication_date,
                date,
            )
            and not isinstance(
                publication_date,
                datetime,
            )
        ):
            publication_datetime = (
                datetime.combine(
                    publication_date,
                    datetime.min.time(),
                )
            )
        else:
            publication_datetime = (
                publication_date
            )

        year = (
            publication_datetime.year
            if isinstance(
                publication_datetime,
                datetime,
            )
            else None
        )

        metadata = dict(
            getattr(
                paper,
                "metadata",
                {},
            )
            or {}
        )

        categories = getattr(
            paper,
            "categories",
            [],
        ) or []

        keywords = getattr(
            paper,
            "keywords",
            [],
        ) or []

        if categories:
            metadata["categories"] = [
                str(value)
                for value in categories
            ]

        if keywords:
            metadata["keywords"] = [
                str(value)
                for value in keywords
            ]

        journal = getattr(
            paper,
            "journal",
            None,
        )

        if journal:
            metadata["journal"] = str(
                journal
            )

        conference = getattr(
            paper,
            "conference",
            None,
        )

        if conference:
            metadata["conference"] = str(
                conference
            )

        metadata["external_ids"] = {
            str(key): str(value)
            for key, value in external_ids.items()
            if value is not None
        }

        orm_paper = Paper(
            provider=provider,
            provider_paper_id=provider_paper_id,
            doi=doi,
            arxiv_id=(
                str(
                    external_ids["arxiv"]
                )
                if external_ids.get("arxiv")
                else None
            ),
            pmid=(
                str(
                    external_ids["pmid"]
                )
                if external_ids.get("pmid")
                else None
            ),
            title=title,
            abstract=getattr(
                paper,
                "abstract",
                None,
            ),
            publication_date=publication_datetime,
            year=year,
            language=getattr(
                paper,
                "language",
                None,
            ),
            citation_count=max(
                int(
                    getattr(
                        paper,
                        "citation_count",
                        0,
                    )
                    or 0
                ),
                0,
            ),
            reference_count=max(
                int(
                    getattr(
                        paper,
                        "reference_count",
                        0,
                    )
                    or 0
                ),
                0,
            ),
            landing_page_url=getattr(
                paper,
                "url",
                None,
            ),
            pdf_url=getattr(
                paper,
                "pdf_url",
                None,
            ),
            source_metadata=self._serialize_metadata(
                metadata
            ),
        )

        created = await self.repository.create(
            orm_paper
        )

        domain_authors = (
            getattr(
                paper,
                "authors",
                None,
            )
            or []
        )

        if domain_authors:
            created = (
                await self.repository.sync_authors(
                    created,
                    domain_authors,
                )
            )

        return PaperUpsertResult(
            paper=created,
            created=True,
            duplicate=False,
        )

    # ========================================================
    # RESPONSE SERIALIZATION
    # ========================================================

    @classmethod
    def _to_response(
        cls,
        paper: Any,
    ) -> PaperResponse:

        metadata = cls._extract_metadata(
            paper
        )

        authors = cls._extract_authors(
            paper
        )

        paper_id = getattr(
            paper,
            "id",
            None,
        )

        venue_name = cls._extract_venue_name(
            paper
        )

        data = {
            "id": (
                str(paper_id)
                if paper_id is not None
                else None
            ),
            "title": (
                getattr(
                    paper,
                    "title",
                    "",
                )
                or ""
            ),
            "abstract": getattr(
                paper,
                "abstract",
                None,
            ),
            "authors": authors,
            "publication_date": (
                cls._normalize_publication_date(
                    getattr(
                        paper,
                        "publication_date",
                        None,
                    )
                )
            ),
            "venue": venue_name,
            "journal": metadata.get(
                "journal"
            ),
            "conference": metadata.get(
                "conference"
            ),
            "doi": getattr(
                paper,
                "doi",
                None,
            ),
            "url": getattr(
                paper,
                "landing_page_url",
                None,
            ),
            "pdf_url": getattr(
                paper,
                "pdf_url",
                None,
            ),
            "language": getattr(
                paper,
                "language",
                None,
            ),
            "keywords": cls._metadata_list(
                metadata,
                "keywords",
            ),
            "categories": cls._metadata_list(
                metadata,
                "categories",
            ),
            "external_ids": (
                cls._build_external_ids(
                    paper
                )
            ),
            "citation_count": max(
                int(
                    getattr(
                        paper,
                        "citation_count",
                        0,
                    )
                    or 0
                ),
                0,
            ),
            "reference_count": max(
                int(
                    getattr(
                        paper,
                        "reference_count",
                        0,
                    )
                    or 0
                ),
                0,
            ),
            "source": getattr(
                paper,
                "provider",
                None,
            ),
            "metadata": metadata,
            "created_at": getattr(
                paper,
                "created_at",
                None,
            ),
            "updated_at": getattr(
                paper,
                "updated_at",
                None,
            ),
            "canonical_key": (
                getattr(
                    paper,
                    "canonical_key",
                    None,
                )
                or cls._derive_canonical_key(
                    paper
                )
            ),
        }

        return PaperResponse.model_validate(
            data
        )

    # ========================================================
    # SEARCH RESPONSE
    # ========================================================

    @classmethod
    def _to_search_result(
        cls,
        paper: Any,
    ) -> PaperSearchResult:

        authors = cls._extract_authors(
            paper
        )

        author_names: list[str] = []

        for author in authors:
            if isinstance(
                author,
                dict,
            ):
                name = author.get(
                    "name"
                )

                if name:
                    author_names.append(
                        str(name)
                    )

            elif isinstance(
                author,
                str,
            ):
                author_names.append(
                    author
                )

        return PaperSearchResult(
            id=(
                str(paper.id)
                if getattr(
                    paper,
                    "id",
                    None,
                ) is not None
                else None
            ),
            title=(
                getattr(
                    paper,
                    "title",
                    "",
                )
                or ""
            ),
            abstract=getattr(
                paper,
                "abstract",
                None,
            ),
            authors=author_names,
            publication_date=(
                cls._normalize_publication_date(
                    getattr(
                        paper,
                        "publication_date",
                        None,
                    )
                )
            ),
            venue=cls._extract_venue_name(
                paper
            ),
            doi=getattr(
                paper,
                "doi",
                None,
            ),
            url=getattr(
                paper,
                "landing_page_url",
                None,
            ),
            pdf_url=getattr(
                paper,
                "pdf_url",
                None,
            ),
            citation_count=max(
                int(
                    getattr(
                        paper,
                        "citation_count",
                        0,
                    )
                    or 0
                ),
                0,
            ),
            source=getattr(
                paper,
                "provider",
                None,
            ),
            relevance_score=None,
        )

    # ========================================================
    # AUTHORS
    # ========================================================

    @staticmethod
    def _extract_authors(
        paper: Any,
    ) -> list[dict[str, Any]]:

        author_links = (
            getattr(
                paper,
                "author_links",
                [],
            )
            or []
        )

        result: list[dict[str, Any]] = []

        try:
            author_links = sorted(
                author_links,
                key=lambda link: (
                    getattr(
                        link,
                        "author_order",
                        0,
                    )
                    or 0
                ),
            )
        except Exception:
            pass

        for link in author_links:
            author = getattr(
                link,
                "author",
                None,
            )

            if author is None:
                continue

            name = (
                getattr(
                    author,
                    "full_name",
                    None,
                )
                or getattr(
                    author,
                    "name",
                    None,
                )
            )

            if not name:
                continue

            result.append(
                {
                    "name": str(name),
                    "author_id": getattr(
                        author,
                        "id",
                        None,
                    ),
                    "orcid": getattr(
                        author,
                        "orcid",
                        None,
                    ),
                    "email": getattr(
                        author,
                        "email",
                        None,
                    ),
                    "affiliation": getattr(
                        author,
                        "affiliation",
                        None,
                    ),
                    "position": getattr(
                        link,
                        "author_order",
                        None,
                    ),
                }
            )

        if result:
            return result

        direct_authors = (
            getattr(
                paper,
                "authors",
                None,
            )
            or []
        )

        for index, author in enumerate(
            direct_authors
        ):
            if isinstance(
                author,
                dict,
            ):
                name = (
                    author.get("name")
                    or author.get(
                        "full_name"
                    )
                )

                if not name:
                    continue

                result.append(
                    {
                        "name": str(name),
                        "author_id": author.get(
                            "author_id"
                        ),
                        "orcid": author.get(
                            "orcid"
                        ),
                        "email": author.get(
                            "email"
                        ),
                        "affiliation": author.get(
                            "affiliation"
                        ),
                        "position": author.get(
                            "position",
                            index,
                        ),
                    }
                )

            elif isinstance(
                author,
                str,
            ):
                name = author.strip()

                if name:
                    result.append(
                        {
                            "name": name,
                            "author_id": None,
                            "orcid": None,
                            "email": None,
                            "affiliation": None,
                            "position": index,
                        }
                    )

            else:
                name = (
                    getattr(
                        author,
                        "name",
                        None,
                    )
                    or getattr(
                        author,
                        "full_name",
                        None,
                    )
                )

                if name:
                    result.append(
                        {
                            "name": str(name),
                            "author_id": getattr(
                                author,
                                "id",
                                None,
                            ),
                            "orcid": getattr(
                                author,
                                "orcid",
                                None,
                            ),
                            "email": getattr(
                                author,
                                "email",
                                None,
                            ),
                            "affiliation": getattr(
                                author,
                                "affiliation",
                                None,
                            ),
                            "position": getattr(
                                author,
                                "position",
                                index,
                            ),
                        }
                    )

        return result

    # ========================================================
    # VENUE
    # ========================================================

    @staticmethod
    def _extract_venue_name(
        paper: Any,
    ) -> str | None:

        venue = getattr(
            paper,
            "venue",
            None,
        )

        if venue is None:
            metadata = PaperService._extract_metadata(
                paper
            )

            value = metadata.get(
                "venue"
            )

            return (
                str(value)
                if value
                else None
            )

        if isinstance(
            venue,
            str,
        ):
            return venue

        for field in (
            "name",
            "title",
            "display_name",
        ):
            value = getattr(
                venue,
                field,
                None,
            )

            if value:
                return str(value)

        return None

    # ========================================================
    # EXTERNAL IDS
    # ========================================================

    @staticmethod
    def _build_external_ids(
        paper: Any,
    ) -> dict[str, str]:

        result: dict[str, str] = {}

        arxiv_id = getattr(
            paper,
            "arxiv_id",
            None,
        )

        if arxiv_id:
            result["arxiv"] = str(
                arxiv_id
            )

        pmid = getattr(
            paper,
            "pmid",
            None,
        )

        if pmid:
            result["pmid"] = str(
                pmid
            )

        provider = getattr(
            paper,
            "provider",
            None,
        )

        provider_paper_id = getattr(
            paper,
            "provider_paper_id",
            None,
        )

        if provider and provider_paper_id:
            result[str(provider)] = str(
                provider_paper_id
            )

        metadata = (
            PaperService._extract_metadata(
                paper
            )
        )

        metadata_external_ids = (
            metadata.get(
                "external_ids"
            )
        )

        if isinstance(
            metadata_external_ids,
            dict,
        ):
            for key, value in (
                metadata_external_ids.items()
            ):
                if value is not None:
                    result.setdefault(
                        str(key),
                        str(value),
                    )

        return result

    # ========================================================
    # METADATA
    # ========================================================

    @staticmethod
    def _extract_metadata(
        paper: Any,
    ) -> dict[str, Any]:

        raw = getattr(
            paper,
            "source_metadata",
            None,
        )

        if not raw:
            return {}

        if isinstance(
            raw,
            dict,
        ):
            return dict(raw)

        if isinstance(
            raw,
            str,
        ):
            try:
                parsed = json.loads(
                    raw
                )

                if isinstance(
                    parsed,
                    dict,
                ):
                    return parsed

            except (
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ):
                return {
                    "raw": raw
                }

        return {}

    @staticmethod
    def _serialize_metadata(
        metadata: dict[str, Any] | None,
    ) -> str | None:

        if not metadata:
            return None

        try:
            return json.dumps(
                metadata,
                default=str,
            )

        except (
            TypeError,
            ValueError,
        ):
            return json.dumps(
                {
                    "raw": str(
                        metadata
                    )
                }
            )

    @staticmethod
    def _metadata_list(
        metadata: dict[str, Any],
        key: str,
    ) -> list[str]:

        value = metadata.get(
            key,
            [],
        )

        if isinstance(
            value,
            tuple,
        ):
            value = list(value)

        if isinstance(
            value,
            set,
        ):
            value = list(value)

        if not isinstance(
            value,
            list,
        ):
            return []

        return [
            str(item)
            for item in value
            if item is not None
        ]

    # ========================================================
    # CANONICAL KEY
    # ========================================================

    @staticmethod
    def _derive_canonical_key(
        paper: Any,
    ) -> str | None:

        canonical_key = getattr(
            paper,
            "canonical_key",
            None,
        )

        if canonical_key:
            return str(
                canonical_key
            )

        doi = getattr(
            paper,
            "doi",
            None,
        )

        if doi:
            return f"doi:{doi}"

        arxiv_id = getattr(
            paper,
            "arxiv_id",
            None,
        )

        if arxiv_id:
            return f"arxiv:{arxiv_id}"

        pmid = getattr(
            paper,
            "pmid",
            None,
        )

        if pmid:
            return f"pmid:{pmid}"

        provider = getattr(
            paper,
            "provider",
            None,
        )

        provider_id = getattr(
            paper,
            "provider_paper_id",
            None,
        )

        if provider and provider_id:
            return (
                f"{provider}:{provider_id}"
            )

        return None

    @staticmethod
    def _get_domain_canonical_key(
        paper: DomainPaper,
    ) -> str | None:

        canonical_key = getattr(
            paper,
            "canonical_key",
            None,
        )

        if canonical_key:
            return str(
                canonical_key
            )

        doi = getattr(
            paper,
            "doi",
            None,
        )

        if doi:
            return f"doi:{doi}"

        external_ids = (
            getattr(
                paper,
                "external_ids",
                {},
            )
            or {}
        )

        arxiv_id = external_ids.get(
            "arxiv"
        )

        if arxiv_id:
            return f"arxiv:{arxiv_id}"

        pmid = external_ids.get(
            "pmid"
        )

        if pmid:
            return f"pmid:{pmid}"

        provider = getattr(
            paper,
            "source",
            None,
        )

        provider_id = (
            external_ids.get(
                provider
            )
            if provider
            else None
        )

        if provider and provider_id:
            return (
                f"{provider}:{provider_id}"
            )

        return None

    # ========================================================
    # DATE
    # ========================================================

    @staticmethod
    def _normalize_publication_date(
        value: Any,
    ) -> date | None:

        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            try:
                return date.fromisoformat(
                    value[:10]
                )
            except (
                TypeError,
                ValueError,
            ):
                return None

        return None

    # ========================================================
    # EXTERNAL ID NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_external_id(
        resolver: PaperResolver,
        provider: str,
        external_id: str,
    ) -> str | None:

        if not external_id:
            return None

        provider = provider.strip().lower()
        external_id = external_id.strip()

        if not provider or not external_id:
            return None

        if provider == "arxiv":
            return resolver.normalize_arxiv_id(
                external_id
            )

        if provider == "openalex":
            return resolver.normalize_openalex_id(
                external_id
            )

        if provider == "semantic_scholar":
            return (
                resolver.normalize_semantic_scholar_id(
                    external_id
                )
            )

        if provider == "pmid":
            return resolver.normalize_pmid(
                external_id
            )

        if provider == "crossref":
            return external_id

        return external_id

    # ========================================================
    # STRING NORMALIZATION
    # ========================================================

    @staticmethod
    def _clean_string(
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = str(value).strip()

        return value or None