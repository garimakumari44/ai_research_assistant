from __future__ import annotations

import logging

from app.ingestion.providers.base import (
    BasePaperProvider,
    ProviderPaper,
)

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Coordinates paper metadata providers.

    The rest of the application should depend on this manager
    instead of directly depending on OpenAlex, Semantic Scholar,
    Crossref, etc.
    """

    def __init__(
        self,
        providers: list[BasePaperProvider],
    ) -> None:

        if not providers:
            raise ValueError(
                "ProviderManager requires at least one provider"
            )

        self._providers = {
            provider.name: provider
            for provider in providers
        }

    def register(
        self,
        provider: BasePaperProvider,
    ) -> None:

        self._providers[provider.name] = provider

    def get(
        self,
        provider_name: str,
    ) -> BasePaperProvider:

        provider = self._providers.get(
            provider_name
        )

        if provider is None:
            raise ValueError(
                f"Unknown paper provider: {provider_name}"
            )

        return provider

    def providers(self) -> list[str]:
        return list(self._providers.keys())

    async def search(
        self,
        query: str,
        *,
        provider: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProviderPaper]:

        if provider:
            selected = [self.get(provider)]

        else:
            selected = list(
                self._providers.values()
            )

        results: list[ProviderPaper] = []

        for current_provider in selected:

            try:
                papers = await current_provider.search(
                    query,
                    limit=limit,
                    offset=offset,
                )

                results.extend(papers)

            except Exception:
                logger.exception(
                    "Paper provider search failed",
                    extra={
                        "provider": current_provider.name,
                        "query": query,
                    },
                )

        return results

    async def get_by_id(
        self,
        provider_name: str,
        provider_id: str,
    ) -> ProviderPaper | None:

        provider = self.get(provider_name)

        return await provider.get_by_id(
            provider_id
        )

    async def get_by_doi(
        self,
        doi: str,
        *,
        provider: str | None = None,
    ) -> ProviderPaper | None:

        if provider:
            selected = [self.get(provider)]

        else:
            selected = list(
                self._providers.values()
            )

        for current_provider in selected:

            try:
                paper = await current_provider.get_by_doi(
                    doi
                )

                if paper is not None:
                    return paper

            except Exception:
                logger.exception(
                    "Paper DOI lookup failed",
                    extra={
                        "provider": current_provider.name,
                        "doi": doi,
                    },
                )

        return None

    async def health_check(
        self,
    ) -> dict[str, bool]:

        results: dict[str, bool] = {}

        for provider in self._providers.values():

            try:
                results[provider.name] = (
                    await provider.health_check()
                )

            except Exception:
                logger.exception(
                    "Provider health check failed",
                    extra={
                        "provider": provider.name,
                    },
                )

                results[provider.name] = False

        return results