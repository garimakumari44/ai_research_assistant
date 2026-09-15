from __future__ import annotations

from typing import Any

from app.retrieval.advanced.models import RetrievalSource
from app.retrieval.models import RetrievedDocument
from app.retrieval.sources.base import BaseRetrievalSource


class GithubSource(BaseRetrievalSource):
    """
    GitHub retrieval adapter.

    A GitHub client/search backend is injected rather than created
    inside this class.

    This keeps authentication, API limits, caching and GitHub-specific
    logic outside the retrieval architecture.
    """

    source_type = RetrievalSource.GITHUB

    def __init__(
        self,
        client: Any | None = None,
    ) -> None:
        super().__init__()

        self.client = client

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:

        if self.client is None:
            return []

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        search_method = getattr(
            self.client,
            "search",
            None,
        )

        if search_method is None:
            return []

        try:
            results = search_method(
                query=query,
                top_k=top_k,
                filters=filters or {},
            )

            if hasattr(results, "__await__"):
                results = await results

        except Exception:
            return []

        normalized: list[RetrievedDocument] = []

        for result in results or []:
            document = self.normalize_result(
                result,
                default_source=self.source_type.value,
            )

            if document.id or document.content:
                normalized.append(document)

        return normalized