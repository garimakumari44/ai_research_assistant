from __future__ import annotations

from typing import Any

from app.knowledge.indexing.keyword import KeywordIndexer
from app.retrieval.advanced.models import RetrievalSource
from app.retrieval.models import RetrievedDocument
from app.retrieval.sources.base import BaseRetrievalSource


class BM25Source(BaseRetrievalSource):
    """
    BM25 keyword retrieval source.

    Architecture:

        query
          ↓
        KeywordIndexer
          ↓
        BM25Okapi
          ↓
        KeywordSearchResult
          ↓
        RetrievedDocument
    """

    source_type = RetrievalSource.BM25

    def __init__(
        self,
        keyword_index: KeywordIndexer,
    ) -> None:
        super().__init__()

        self.keyword_index = keyword_index

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """
        Perform sparse/BM25 retrieval.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if not isinstance(top_k, int):
            return []

        if top_k <= 0:
            return []

        try:
            results = await self.keyword_index.search(
                query=query,
                top_k=top_k,
                filters=filters or {},
            )
        except Exception:
            return []

        documents: list[RetrievedDocument] = []

        for result in results:
            item = await self.keyword_index.get(
                result.chunk_id
            )

            if item is None:
                continue

            documents.append(
                RetrievedDocument(
                    id=str(result.chunk_id),
                    content=item.text,
                    source=self.source_type.value,
                    score=float(result.score),
                    metadata=dict(
                        result.metadata or {}
                    ),
                )
            )

        return documents