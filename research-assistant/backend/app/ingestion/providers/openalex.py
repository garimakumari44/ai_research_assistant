from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from app.ingestion.providers.base import (
    BasePaperProvider,
    ProviderPaper,
)

logger = logging.getLogger(__name__)


class OpenAlexProvider(BasePaperProvider):
    """
    OpenAlex paper metadata provider.

    OpenAlex API:
        https://api.openalex.org

    Responsibilities:
        - Search OpenAlex
        - Fetch a work by OpenAlex ID
        - Map OpenAlex responses into ProviderPaper

    This class does NOT:
        - Persist papers
        - Deduplicate papers
        - Create canonical Paper objects
        - Interact with PostgreSQL
    """

    name = "openalex"

    BASE_URL = "https://api.openalex.org"

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        mailto: str | None = None,
    ) -> None:
        self.timeout = timeout
        self.mailto = mailto

        headers = {
            "Accept": "application/json",
            "User-Agent": "AdaptiveResearchRAG/1.0",
        }

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            headers=headers,
        )

    async def close(self) -> None:
        """
        Close the underlying HTTP client.
        """
        await self._client.aclose()

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProviderPaper]:

        if not query or not query.strip():
            return []

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        params: dict[str, Any] = {
            "search": query.strip(),
            "per-page": limit,
            "page": (offset // limit) + 1,
        }

        if self.mailto:
            params["mailto"] = self.mailto

        try:
            response = await self._client.get(
                "/works",
                params=params,
            )

            response.raise_for_status()

        except httpx.HTTPError:
            logger.exception(
                "OpenAlex search request failed",
                extra={
                    "query": query,
                    "limit": limit,
                    "offset": offset,
                },
            )
            raise

        payload = response.json()

        results = payload.get("results", [])

        papers: list[ProviderPaper] = []

        for item in results:
            try:
                paper = self._parse_work(item)

                if paper is not None:
                    papers.append(paper)

            except Exception:
                logger.exception(
                    "Failed to parse OpenAlex work",
                    extra={
                        "openalex_id": item.get("id"),
                    },
                )

        return papers

    async def get_by_id(
        self,
        provider_id: str,
    ) -> ProviderPaper | None:

        if not provider_id:
            return None

        normalized_id = self._normalize_work_id(provider_id)

        if not normalized_id:
            return None

        params: dict[str, Any] = {}

        if self.mailto:
            params["mailto"] = self.mailto

        try:
            response = await self._client.get(
                f"/works/{normalized_id}",
                params=params,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

        except httpx.HTTPError:
            logger.exception(
                "OpenAlex get_by_id request failed",
                extra={
                    "provider_id": provider_id,
                },
            )
            raise

        return self._parse_work(response.json())

    async def get_by_doi(
        self,
        doi: str,
    ) -> ProviderPaper | None:

        normalized_doi = self._normalize_doi(doi)

        if not normalized_doi:
            return None

        params: dict[str, Any] = {
            "filter": f"doi:{normalized_doi}",
            "per-page": 1,
        }

        if self.mailto:
            params["mailto"] = self.mailto

        try:
            response = await self._client.get(
                "/works",
                params=params,
            )

            response.raise_for_status()

        except httpx.HTTPError:
            logger.exception(
                "OpenAlex DOI lookup failed",
                extra={
                    "doi": doi,
                },
            )
            raise

        payload = response.json()
        results = payload.get("results", [])

        if not results:
            return None

        return self._parse_work(results[0])

    async def health_check(self) -> bool:

        try:
            response = await self._client.get(
                "/works",
                params={
                    "per-page": 1,
                },
            )

            return response.is_success

        except httpx.HTTPError:
            logger.warning(
                "OpenAlex health check failed",
                exc_info=True,
            )
            return False

    def _parse_work(
        self,
        data: dict[str, Any],
    ) -> ProviderPaper | None:

        provider_id = self._extract_provider_id(
            data.get("id")
        )

        if not provider_id:
            return None

        title = self._clean_string(
            data.get("title")
        )

        abstract = self._extract_abstract(data)

        authors = self._extract_authors(data)

        doi = self._normalize_doi(
            data.get("doi")
        )

        url = self._clean_string(
            data.get("id")
        )

        published_at = self._parse_date(
            data.get("publication_date")
        )

        venue = self._extract_venue(data)

        journal = self._extract_journal(data)

        citation_count = self._extract_int(
            data.get("cited_by_count")
        )

        pdf_url = self._extract_pdf_url(data)

        return ProviderPaper(
            provider=self.name,
            provider_id=provider_id,
            title=title,
            abstract=abstract,
            authors=authors,
            doi=doi,
            url=url,
            published_at=published_at,
            venue=venue,
            journal=journal,
            citation_count=citation_count,
            pdf_url=pdf_url,
            raw_data=data,
        )

    @staticmethod
    def _extract_provider_id(
        value: Any,
    ) -> str | None:

        if not value:
            return None

        value = str(value).strip()

        if "/W" in value:
            return value.rsplit("/", 1)[-1]

        return value

    @staticmethod
    def _normalize_work_id(
        value: str,
    ) -> str | None:

        value = value.strip()

        if not value:
            return None

        if value.startswith("https://openalex.org/"):
            return value.rsplit("/", 1)[-1]

        if value.startswith("http://openalex.org/"):
            return value.rsplit("/", 1)[-1]

        return value

    @staticmethod
    def _normalize_doi(
        value: Any,
    ) -> str | None:

        if not value:
            return None

        doi = str(value).strip()

        prefixes = (
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
            "DOI:",
        )

        for prefix in prefixes:
            if doi.startswith(prefix):
                doi = doi[len(prefix):]

        doi = doi.strip()

        return doi or None

    @staticmethod
    def _clean_string(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _extract_authors(
        data: dict[str, Any],
    ) -> list[str]:

        authorships = data.get("authorships") or []

        authors: list[str] = []

        for authorship in authorships:
            author = authorship.get("author") or {}

            display_name = author.get("display_name")

            if display_name:
                authors.append(display_name.strip())

        return authors

    @staticmethod
    def _extract_abstract(
        data: dict[str, Any],
    ) -> str | None:

        inverted_index = data.get(
            "abstract_inverted_index"
        )

        if not inverted_index:
            return None

        words: list[tuple[int, str]] = []

        for word, positions in inverted_index.items():

            if not isinstance(positions, list):
                continue

            for position in positions:
                try:
                    words.append(
                        (int(position), word)
                    )
                except (TypeError, ValueError):
                    continue

        if not words:
            return None

        words.sort(key=lambda item: item[0])

        return " ".join(
            word for _, word in words
        ).strip() or None

    @staticmethod
    def _extract_venue(
        data: dict[str, Any],
    ) -> str | None:

        primary_location = (
            data.get("primary_location") or {}
        )

        source = (
            primary_location.get("source") or {}
        )

        return OpenAlexProvider._clean_string(
            source.get("display_name")
        )

    @staticmethod
    def _extract_journal(
        data: dict[str, Any],
    ) -> str | None:

        primary_location = (
            data.get("primary_location") or {}
        )

        source = (
            primary_location.get("source") or {}
        )

        source_type = source.get("type")

        if source_type == "journal":
            return OpenAlexProvider._clean_string(
                source.get("display_name")
            )

        return None

    @staticmethod
    def _extract_pdf_url(
        data: dict[str, Any],
    ) -> str | None:

        best_oa_location = (
            data.get("best_oa_location") or {}
        )

        pdf_url = best_oa_location.get(
            "pdf_url"
        )

        if pdf_url:
            return str(pdf_url).strip()

        locations = data.get("locations") or []

        for location in locations:
            pdf_url = location.get("pdf_url")

            if pdf_url:
                return str(pdf_url).strip()

        return None

    @staticmethod
    def _extract_int(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> datetime | None:

        if not value:
            return None

        try:
            return datetime.fromisoformat(
                str(value)
            )

        except ValueError:
            return None