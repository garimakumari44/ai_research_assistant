from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ProviderPaper:
    """
    Provider-level representation of a research paper.

    This is NOT the canonical Paper domain model.

    Each provider is responsible for translating its API response
    into this common provider representation. The application can
    then normalize this into the canonical Paper model.
    """

    provider: str
    provider_id: str

    title: str | None = None
    abstract: str | None = None

    authors: list[str] = field(default_factory=list)

    doi: str | None = None
    url: str | None = None

    published_at: datetime | None = None

    venue: str | None = None
    journal: str | None = None

    citation_count: int | None = None

    pdf_url: str | None = None

    raw_data: dict[str, Any] = field(default_factory=dict)


class BasePaperProvider(ABC):
    """
    Abstract interface for paper metadata providers.

    Implementations:
        - OpenAlexProvider
        - SemanticScholarProvider
        - CrossrefProvider
        - ArxivProvider
    """

    name: str

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProviderPaper]:
        """
        Search for papers using the provider.

        Args:
            query: Search query.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of provider-level papers.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        provider_id: str,
    ) -> ProviderPaper | None:
        """
        Fetch a single paper by provider-specific ID.
        """
        raise NotImplementedError

    async def get_by_doi(
        self,
        doi: str,
    ) -> ProviderPaper | None:
        """
        Optional DOI lookup.

        Providers that do not support DOI lookup can use the
        default implementation.
        """
        return None

    async def health_check(self) -> bool:
        """
        Check whether the provider is reachable.

        Providers can override this with a real health check.
        """
        return True