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


class SemanticScholarProvider(BasePaperProvider):
    """
    Semantic Scholar paper metadata provider.

    API:
        https://api.semanticscholar.org/graph/v1

    Responsibilities:
        - Search papers
        - Fetch paper by Semantic Scholar ID
        - Fetch paper by DOI
        - Normalize provider response into ProviderPaper

    This provider does not:
        - Persist papers
        - Deduplicate papers
        - Create canonical Paper objects
        - Access PostgreSQL
    """

    name = "semantic_scholar"

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    DEFAULT_FIELDS = (
        "paperId,"
        "externalIds,"
        "title,"
        "abstract,"
        "authors,"
        "year,"
        "publicationDate,"
        "venue,"
        "journal,"
        "citationCount,"
        "url,"
        "openAccessPdf"
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.timeout = timeout
        self.api_key = api_key

        headers = {
            "Accept": "application/json",
            "User-Agent": "AdaptiveResearchRAG/1.0",
        }

        if api_key:
            headers["x-api-key"] = api_key

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            headers=headers,
        )

    async def close(self) -> None:
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
            "query": query.strip(),
            "limit": limit,
            "offset": offset,
            "fields": self.DEFAULT_FIELDS,
        }

        try:
            response = await self._client.get(
                "/paper/search",
                params=params,
            )

            response.raise_for_status()

        except httpx.HTTPError:
            logger.exception(
                "Semantic Scholar search failed",
                extra={
                    "query": query,
                    "limit": limit,
                    "offset": offset,
                },
            )
            raise

        payload = response.json()

        results = payload.get("data", [])

        papers: list[ProviderPaper] = []

        for item in results:
            try:
                paper = self._parse_paper(item)

                if paper:
                    papers.append(paper)

            except Exception:
                logger.exception(
                    "Failed to parse Semantic Scholar paper",
                    extra={
                        "paper_id": item.get("paperId"),
                    },
                )

        return papers

    async def get_by_id(
        self,
        provider_id: str,
    ) -> ProviderPaper | None:

        if not provider_id:
            return None

        params = {
            "fields": self.DEFAULT_FIELDS,
        }

        try:
            response = await self._client.get(
                f"/paper/{provider_id}",
                params=params,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

        except httpx.HTTPError:
            logger.exception(
                "Semantic Scholar get_by_id failed",
                extra={
                    "provider_id": provider_id,
                },
            )
            raise

        return self._parse_paper(
            response.json()
        )

    async def get_by_doi(
        self,
        doi: str,
    ) -> ProviderPaper | None:

        normalized_doi = self._normalize_doi(doi)

        if not normalized_doi:
            return None

        return await self.get_by_id(
            f"DOI:{normalized_doi}"
        )

    async def health_check(self) -> bool:

        try:
            response = await self._client.get(
                "/paper/search",
                params={
                    "query": "test",
                    "limit": 1,
                    "fields": "paperId",
                },
            )

            return response.is_success

        except httpx.HTTPError:
            logger.warning(
                "Semantic Scholar health check failed",
                exc_info=True,
            )
            return False

    def _parse_paper(
        self,
        data: dict[str, Any],
    ) -> ProviderPaper | None:

        paper_id = self._clean_string(
            data.get("paperId")
        )

        if not paper_id:
            return None

        external_ids = data.get("externalIds") or {}

        doi = self._normalize_doi(
            external_ids.get("DOI")
        )

        authors = self._extract_authors(data)

        publication_date = self._parse_date(
            data.get("publicationDate")
        )

        if publication_date is None:
            year = data.get("year")

            if year:
                try:
                    publication_date = datetime(
                        int(year),
                        1,
                        1,
                    )
                except (TypeError, ValueError):
                    publication_date = None

        open_access_pdf = (
            data.get("openAccessPdf") or {}
        )

        pdf_url = self._clean_string(
            open_access_pdf.get("url")
        )

        journal = self._extract_journal(data)

        venue = self._clean_string(
            data.get("venue")
        )

        if journal is None:
            journal = venue

        return ProviderPaper(
            provider=self.name,
            provider_id=paper_id,
            title=self._clean_string(
                data.get("title")
            ),
            abstract=self._clean_string(
                data.get("abstract")
            ),
            authors=authors,
            doi=doi,
            url=self._clean_string(
                data.get("url")
            ),
            published_at=publication_date,
            venue=venue,
            journal=journal,
            citation_count=self._extract_int(
                data.get("citationCount")
            ),
            pdf_url=pdf_url,
            raw_data=data,
        )

    @staticmethod
    def _extract_authors(
        data: dict[str, Any],
    ) -> list[str]:

        authors = data.get("authors") or []

        result: list[str] = []

        for author in authors:
            name = author.get("name")

            if name:
                result.append(
                    name.strip()
                )

        return result

    @staticmethod
    def _extract_journal(
        data: dict[str, Any],
    ) -> str | None:

        journal = data.get("journal")

        if not journal:
            return None

        if isinstance(journal, dict):
            return SemanticScholarProvider._clean_string(
                journal.get("name")
            )

        return SemanticScholarProvider._clean_string(
            journal
        )

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

        return doi.strip() or None

    @staticmethod
    def _clean_string(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        value = str(value).strip()

        return value or None

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