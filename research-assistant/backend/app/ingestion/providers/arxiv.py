from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import feedparser
import httpx

from app.ingestion.providers.base import (
    BasePaperProvider,
    ProviderPaper,
)

logger = logging.getLogger(__name__)


class ArxivProvider(BasePaperProvider):
    """
    arXiv paper metadata provider.

    API:
        https://export.arxiv.org/api/query

    Responsibilities:
        - Search arXiv
        - Fetch paper by arXiv ID
        - Normalize Atom/XML responses
        - Return ProviderPaper objects

    This provider does NOT:
        - Persist papers
        - Deduplicate papers
        - Create canonical Paper objects
        - Interact with PostgreSQL
    """

    name = "arxiv"

    BASE_URL = "https://export.arxiv.org/api/query"

    DEFAULT_TIMEOUT = 60.0
    DEFAULT_RETRIES = 2

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ) -> None:
        self.timeout = max(5.0, float(timeout))
        self.retries = max(0, int(retries))

        headers = {
            "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
            "User-Agent": (
                "AdaptiveResearchRAG/1.0 "
                "(academic-research-assistant)"
            ),
        }

        timeout_config = httpx.Timeout(
            connect=15.0,
            read=self.timeout,
            write=15.0,
            pool=15.0,
        )

        self._client = httpx.AsyncClient(
            timeout=timeout_config,
            headers=headers,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """
        Close the underlying HTTP client.
        """
        if not self._client.is_closed:
            await self._client.aclose()

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProviderPaper]:
        """
        Search arXiv.

        Example:
            BERT
            Retrieval-Augmented Generation
            transformer architecture
        """

        normalized_query = self._clean_string(query)

        if not normalized_query:
            return []

        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))

        params = {
            "search_query": f"all:{normalized_query}",
            "start": offset,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        logger.info(
            "Searching arXiv",
            extra={
                "query": normalized_query,
                "limit": limit,
                "offset": offset,
            },
        )

        response = await self._request(
            params=params,
            operation="search",
            query=normalized_query,
        )

        papers = self._parse_feed(response.text)

        logger.info(
            "arXiv search completed",
            extra={
                "query": normalized_query,
                "returned": len(papers),
            },
        )

        return papers

    async def get_by_id(
        self,
        provider_id: str,
    ) -> ProviderPaper | None:
        """
        Fetch one paper using an arXiv ID.

        Supports values such as:

            1706.03762
            1706.03762v7
            arxiv:1706.03762
            https://arxiv.org/abs/1706.03762
            https://arxiv.org/pdf/1706.03762.pdf
        """

        normalized_id = self._normalize_arxiv_id(provider_id)

        if not normalized_id:
            return None

        params = {
            "id_list": normalized_id,
            "max_results": 1,
        }

        logger.info(
            "Fetching arXiv paper",
            extra={
                "provider_id": normalized_id,
            },
        )

        response = await self._request(
            params=params,
            operation="get_by_id",
            query=normalized_id,
        )

        papers = self._parse_feed(response.text)

        if not papers:
            return None

        return papers[0]

    async def get_by_doi(
        self,
        doi: str,
    ) -> ProviderPaper | None:
        """
        arXiv does not provide a reliable DOI lookup endpoint.

        DOI lookup should be handled by Crossref/OpenAlex.
        """
        return None

    async def health_check(self) -> bool:
        """
        Check whether arXiv API is reachable.
        """

        try:
            response = await self._request(
                params={
                    "search_query": "all:test",
                    "start": 0,
                    "max_results": 1,
                },
                operation="health_check",
                query="test",
            )

            return response.is_success

        except httpx.HTTPError:
            logger.warning(
                "arXiv health check failed",
                exc_info=True,
            )
            return False

    async def _request(
        self,
        *,
        params: dict[str, Any],
        operation: str,
        query: str,
    ) -> httpx.Response:
        """
        Execute an arXiv request with retry handling.

        Retries transient network failures and HTTP 429/5xx responses.
        """

        attempts = self.retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.get(
                    self.BASE_URL,
                    params=params,
                )

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    if attempt < attempts:
                        delay = float(2 ** (attempt - 1))

                        logger.warning(
                            "Transient arXiv response; retrying",
                            extra={
                                "operation": operation,
                                "query": query,
                                "status_code": response.status_code,
                                "attempt": attempt,
                                "max_attempts": attempts,
                                "retry_in_seconds": delay,
                            },
                        )

                        await response.aclose()
                        await asyncio.sleep(delay)
                        continue

                response.raise_for_status()

                return response

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            ) as exc:

                if attempt >= attempts:
                    logger.exception(
                        "arXiv request failed after retries",
                        extra={
                            "operation": operation,
                            "query": query,
                            "attempts": attempts,
                        },
                    )
                    raise

                delay = float(2 ** (attempt - 1))

                logger.warning(
                    "Transient arXiv network error; retrying",
                    extra={
                        "operation": operation,
                        "query": query,
                        "attempt": attempt,
                        "max_attempts": attempts,
                        "retry_in_seconds": delay,
                        "error": str(exc),
                    },
                )

                await asyncio.sleep(delay)

            except httpx.HTTPError:
                logger.exception(
                    "arXiv HTTP request failed",
                    extra={
                        "operation": operation,
                        "query": query,
                        "attempt": attempt,
                    },
                )
                raise

        raise RuntimeError(
            "arXiv request failed unexpectedly"
        )

    def _parse_feed(
        self,
        content: str,
    ) -> list[ProviderPaper]:
        """
        Parse arXiv Atom/XML response.
        """

        if not content or not content.strip():
            logger.warning(
                "arXiv returned an empty response"
            )
            return []

        feed = feedparser.parse(content)

        if getattr(feed, "bozo", False):
            logger.warning(
                "arXiv feed parser reported malformed XML",
                extra={
                    "bozo_exception": str(
                        getattr(
                            feed,
                            "bozo_exception",
                            "",
                        )
                    ),
                },
            )

        entries = getattr(
            feed,
            "entries",
            [],
        )

        papers: list[ProviderPaper] = []

        for entry in entries:
            try:
                paper = self._parse_entry(entry)

                if paper is not None:
                    papers.append(paper)

            except Exception:
                logger.exception(
                    "Failed to parse arXiv entry"
                )

        return papers

    def _parse_entry(
        self,
        entry: Any,
    ) -> ProviderPaper | None:
        """
        Convert one arXiv Atom entry into ProviderPaper.
        """

        entry_id = self._clean_string(
            getattr(
                entry,
                "id",
                None,
            )
        )

        provider_id = self._normalize_arxiv_id(
            entry_id
        )

        if not provider_id:
            return None

        title = self._normalize_text(
            getattr(
                entry,
                "title",
                None,
            )
        )

        abstract = self._normalize_text(
            getattr(
                entry,
                "summary",
                None,
            )
        )

        authors = self._extract_authors(
            entry
        )

        published_at = self._parse_date(
            getattr(
                entry,
                "published",
                None,
            )
        )

        pdf_url = self._extract_pdf_url(
            entry
        )

        categories = self._extract_categories(
            entry
        )

        return ProviderPaper(
            provider=self.name,
            provider_id=provider_id,
            title=title,
            abstract=abstract,
            authors=authors,
            doi=self._extract_doi(entry),
            url=f"https://arxiv.org/abs/{provider_id}",
            published_at=published_at,
            venue=(
                ", ".join(categories)
                if categories
                else "arXiv"
            ),
            journal=None,
            citation_count=None,
            pdf_url=pdf_url,
            raw_data=self._entry_to_dict(entry),
        )

    @staticmethod
    def _extract_authors(
        entry: Any,
    ) -> list[str]:
        """
        Extract author names from feedparser's entry.
        """

        authors = getattr(
            entry,
            "authors",
            [],
        ) or []

        result: list[str] = []

        for author in authors:
            try:
                if isinstance(author, dict):
                    name = author.get("name")
                else:
                    name = getattr(
                        author,
                        "name",
                        None,
                    )

                name = ArxivProvider._clean_string(
                    name
                )

                if name:
                    result.append(name)

            except Exception:
                logger.debug(
                    "Failed to parse arXiv author",
                    exc_info=True,
                )

        return result

    @staticmethod
    def _extract_categories(
        entry: Any,
    ) -> list[str]:
        """
        Extract arXiv category tags.
        """

        tags = getattr(
            entry,
            "tags",
            [],
        ) or []

        categories: list[str] = []

        for tag in tags:
            try:
                if isinstance(tag, dict):
                    term = tag.get("term")
                else:
                    term = getattr(
                        tag,
                        "term",
                        None,
                    )

                term = ArxivProvider._clean_string(
                    term
                )

                if term and term not in categories:
                    categories.append(term)

            except Exception:
                logger.debug(
                    "Failed to parse arXiv category",
                    exc_info=True,
                )

        return categories

    @staticmethod
    def _extract_pdf_url(
        entry: Any,
    ) -> str | None:
        """
        Extract PDF URL from Atom links.
        """

        links = getattr(
            entry,
            "links",
            [],
        ) or []

        for link in links:
            try:
                if isinstance(link, dict):
                    href = link.get("href")
                    link_type = link.get("type")
                    title = link.get("title")
                else:
                    href = getattr(
                        link,
                        "href",
                        None,
                    )
                    link_type = getattr(
                        link,
                        "type",
                        None,
                    )
                    title = getattr(
                        link,
                        "title",
                        None,
                    )

                href = ArxivProvider._clean_string(
                    href
                )

                if not href:
                    continue

                if (
                    link_type == "application/pdf"
                    or str(title).lower() == "pdf"
                    or "/pdf/" in href
                ):
                    return href

            except Exception:
                logger.debug(
                    "Failed to parse arXiv PDF link",
                    exc_info=True,
                )

        return None

    @staticmethod
    def _extract_doi(
        entry: Any,
    ) -> str | None:
        """
        Extract DOI when arXiv includes one.

        feedparser usually exposes this through the
        arXiv namespace as `arxiv_doi`.
        """

        possible_values = [
            getattr(
                entry,
                "arxiv_doi",
                None,
            ),
            getattr(
                entry,
                "doi",
                None,
            ),
        ]

        for value in possible_values:
            normalized = ArxivProvider._clean_string(
                value
            )

            if normalized:
                return normalized

        return None

    @staticmethod
    def _normalize_arxiv_id(
        value: Any,
    ) -> str | None:
        """
        Normalize different arXiv ID representations.
        """

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        # Remove URI prefix.
        if value.startswith(
            "http://arxiv.org/abs/"
        ):
            value = value.split(
                "http://arxiv.org/abs/",
                1,
            )[1]

        elif value.startswith(
            "https://arxiv.org/abs/"
        ):
            value = value.split(
                "https://arxiv.org/abs/",
                1,
            )[1]

        elif value.startswith(
            "http://arxiv.org/pdf/"
        ):
            value = value.split(
                "http://arxiv.org/pdf/",
                1,
            )[1]

        elif value.startswith(
            "https://arxiv.org/pdf/"
        ):
            value = value.split(
                "https://arxiv.org/pdf/",
                1,
            )[1]

        elif value.startswith(
            "arXiv:"
        ):
            value = value[6:]

        elif value.startswith(
            "arxiv:"
        ):
            value = value[6:]

        value = value.strip()

        # Remove PDF suffix.
        if value.lower().endswith(".pdf"):
            value = value[:-4]

        # Remove trailing slash.
        value = value.rstrip("/").strip()

        return value or None

    @staticmethod
    def _clean_string(
        value: Any,
    ) -> str | None:
        """
        Convert arbitrary values into clean strings.
        """

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str | None:
        """
        Normalize whitespace in titles and abstracts.
        """

        value = ArxivProvider._clean_string(
            value
        )

        if not value:
            return None

        return " ".join(
            value.split()
        )

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> datetime | None:
        """
        Parse arXiv ISO timestamps.

        Example:
            2017-06-12T17:57:34Z
        """

        if not value:
            return None

        raw_value = str(value).strip()

        if not raw_value:
            return None

        try:
            return datetime.fromisoformat(
                raw_value.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:
            logger.debug(
                "Unable to parse arXiv date",
                extra={
                    "value": raw_value,
                },
            )
            return None

    @staticmethod
    def _entry_to_dict(
        entry: Any,
    ) -> dict[str, Any]:
        """
        Convert feedparser's Struct into a normal
        JSON-like dictionary where possible.

        This is only used as provider raw metadata.
        """

        try:
            if hasattr(
                entry,
                "keys",
            ):
                return {
                    str(key): ArxivProvider._safe_raw_value(
                        entry[key]
                    )
                    for key in entry.keys()
                }

        except Exception:
            logger.debug(
                "Failed to convert arXiv entry to dict",
                exc_info=True,
            )

        return {}

    @staticmethod
    def _safe_raw_value(
        value: Any,
    ) -> Any:
        """
        Make feedparser values safe for raw_data.
        """

        if value is None:
            return None

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        if isinstance(
            value,
            list,
        ):
            return [
                ArxivProvider._safe_raw_value(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key): ArxivProvider._safe_raw_value(
                    item
                )
                for key, item in value.items()
            }

        try:
            if hasattr(value, "keys"):
                return {
                    str(key): ArxivProvider._safe_raw_value(
                        value[key]
                    )
                    for key in value.keys()
                }
        except Exception:
            pass

        return str(value)