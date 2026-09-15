from __future__ import annotations

from typing import Any

from app.retrieval.advanced.models import RetrievalSource
from app.retrieval.models import RetrievedDocument
from app.retrieval.sources.base import BaseRetrievalSource


class DocumentationSource(BaseRetrievalSource):
    """
    Documentation retrieval adapter.

    A documentation backend is injected into the source.

    Possible implementations include:

        - local documentation index
        - documentation database
        - vector-backed documentation store
        - external documentation provider
    """

    source_type = RetrievalSource.DOCUMENTATION

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