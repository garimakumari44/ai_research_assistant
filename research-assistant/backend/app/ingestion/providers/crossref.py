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


class CrossrefProvider(BasePaperProvider):
    """
    Crossref metadata provider.

    API:
        https://api.crossref.org

    Crossref is primarily used for:
        - DOI metadata
        - Journal metadata
        - Publisher metadata
        - Author metadata
        - Publication dates
    """

    name = "crossref"

    BASE_URL = "https://api.crossref.org"

    def __init__(
        self,
        *,
        mailto: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.mailto = mailto
        self.timeout = timeout

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
            "rows": limit,
            "offset": offset,
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
                "Crossref search failed",
                extra={
                    "query": query,
                },
            )
            raise

        payload = response.json()

        message = payload.get(
            "message",
            {},
        )

        results = message.get(
            "items",
            [],
        )

        papers: list[ProviderPaper] = []

        for item in results:
            try:
                paper = self._parse_work(item)

                if paper:
                    papers.append(paper)

            except Exception:
                logger.exception(
                    "Failed to parse Crossref work",
                    extra={
                        "doi": item.get("DOI"),
                    },
                )

        return papers

    async def get_by_id(
        self,
        provider_id: str,
    ) -> ProviderPaper | None:

        doi = self._normalize_doi(
            provider_id
        )

        if not doi:
            return None

        return await self.get_by_doi(doi)

    async def get_by_doi(
        self,
        doi: str,
    ) -> ProviderPaper | None:

        normalized_doi = self._normalize_doi(
            doi
        )

        if not normalized_doi:
            return None

        params: dict[str, Any] = {}

        if self.mailto:
            params["mailto"] = self.mailto

        try:
            response = await self._client.get(
                f"/works/{normalized_doi}",
                params=params,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

        except httpx.HTTPError:
            logger.exception(
                "Crossref DOI lookup failed",
                extra={
                    "doi": normalized_doi,
                },
            )
            raise

        payload = response.json()

        message = payload.get(
            "message"
        )

        if not message:
            return None

        return self._parse_work(message)

    async def health_check(self) -> bool:

        try:
            response = await self._client.get(
                "/works",
                params={
                    "rows": 1,
                },
            )

            return response.is_success

        except httpx.HTTPError:
            logger.warning(
                "Crossref health check failed",
                exc_info=True,
            )
            return False

    def _parse_work(
        self,
        data: dict[str, Any],
    ) -> ProviderPaper | None:

        doi = self._normalize_doi(
            data.get("DOI")
        )

        if not doi:
            return None

        title = self._extract_title(data)

        authors = self._extract_authors(data)

        published_at = self._extract_date(
            data
        )

        journal = self._extract_journal(
            data
        )

        publisher = self._clean_string(
            data.get("publisher")
        )

        venue = journal or publisher

        url = self._clean_string(
            data.get("URL")
        )

        citation_count = self._extract_int(
            data.get("is-referenced-by-count")
        )

        abstract = self._clean_string(
            data.get("abstract")
        )

        if abstract:
            abstract = self._strip_html(
                abstract
            )

        return ProviderPaper(
            provider=self.name,
            provider_id=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            doi=doi,
            url=url,
            published_at=published_at,
            venue=venue,
            journal=journal,
            citation_count=citation_count,
            pdf_url=None,
            raw_data=data,
        )

    @staticmethod
    def _extract_title(
        data: dict[str, Any],
    ) -> str | None:

        titles = data.get("title") or []

        if not titles:
            return None

        return CrossrefProvider._clean_string(
            titles[0]
        )

    @staticmethod
    def _extract_authors(
        data: dict[str, Any],
    ) -> list[str]:

        authors = data.get(
            "author"
        ) or []

        result: list[str] = []

        for author in authors:

            given = CrossrefProvider._clean_string(
                author.get("given")
            )

            family = CrossrefProvider._clean_string(
                author.get("family")
            )

            name = " ".join(
                part
                for part in [given, family]
                if part
            )

            if name:
                result.append(name)

        return result

    @staticmethod
    def _extract_journal(
        data: dict[str, Any],
    ) -> str | None:

        containers = data.get(
            "container-title"
        ) or []

        if not containers:
            return None

        return CrossrefProvider._clean_string(
            containers[0]
        )

    @staticmethod
    def _extract_date(
        data: dict[str, Any],
    ) -> datetime | None:

        date_fields = (
            "published-print",
            "published-online",
            "published",
            "issued",
            "created",
        )

        for field in date_fields:

            value = data.get(field)

            if not value:
                continue

            date_parts = value.get(
                "date-parts"
            )

            if not date_parts:
                continue

            parts = date_parts[0]

            if not parts:
                continue

            try:
                year = int(parts[0])

                month = (
                    int(parts[1])
                    if len(parts) > 1
                    else 1
                )

                day = (
                    int(parts[2])
                    if len(parts) > 2
                    else 1
                )

                return datetime(
                    year,
                    month,
                    day,
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

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

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _strip_html(
        value: str,
    ) -> str:

        import re

        return re.sub(
            r"<[^>]+>",
            "",
            value,
        ).strip()