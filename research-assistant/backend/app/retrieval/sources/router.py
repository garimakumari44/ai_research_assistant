from __future__ import annotations

from typing import Any

from app.knowledge.indexing.registry import IndexRegistry
from app.retrieval.advanced.models import RetrievalSource
from app.retrieval.models import RetrievedDocument
from app.retrieval.sources.arxiv_source import ArxivSource
from app.retrieval.sources.base import BaseRetrievalSource
from app.retrieval.sources.bm25_source import BM25Source
from app.retrieval.sources.documentation_source import DocumentationSource
from app.retrieval.sources.github_source import GithubSource
from app.retrieval.sources.vector_source import VectorSource


class RetrievalSourceRouter:
    """
    Central registry and dispatcher for Explore retrieval sources.

    The router does not decide which sources should be used.

    Source selection is handled by:

        IntentClassifier
        SourceSelector
        RetrievalPlanner

    The router only answers:

        "Given this RetrievalSource, which implementation should
         execute the retrieval task?"
    """

    def __init__(
        self,
        *,
        index_registry: IndexRegistry | None = None,
        arxiv_client: Any | None = None,
        github_client: Any | None = None,
        documentation_client: Any | None = None,
    ) -> None:

        self.sources: dict[
            RetrievalSource,
            BaseRetrievalSource,
        ] = {}

        if index_registry is not None:

            self.register(
                RetrievalSource.VECTOR_DB,
                VectorSource(
                    vector_index=index_registry.vector,
                ),
            )

            self.register(
                RetrievalSource.BM25,
                BM25Source(
                    keyword_index=index_registry.keyword,
                ),
            )

        self.register(
            RetrievalSource.ARXIV,
            ArxivSource(
                client=arxiv_client,
            ),
        )

        self.register(
            RetrievalSource.GITHUB,
            GithubSource(
                client=github_client,
            ),
        )

        self.register(
            RetrievalSource.DOCUMENTATION,
            DocumentationSource(
                client=documentation_client,
            ),
        )

    # ==================================================================
    # REGISTRATION
    # ==================================================================

    def register(
        self,
        source_type: RetrievalSource,
        source: BaseRetrievalSource,
    ) -> None:
        """
        Register a retrieval source.
        """

        if not isinstance(
            source_type,
            RetrievalSource,
        ):
            raise TypeError(
                "source_type must be a RetrievalSource"
            )

        if not isinstance(
            source,
            BaseRetrievalSource,
        ):
            raise TypeError(
                "source must implement BaseRetrievalSource"
            )

        self.sources[source_type] = source

    # ==================================================================
    # LOOKUP
    # ==================================================================

    def get(
        self,
        source_type: RetrievalSource,
    ) -> BaseRetrievalSource | None:
        """
        Return the source registered for a source type.
        """

        return self.sources.get(
            source_type
        )

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        source_type: RetrievalSource,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """
        Execute one retrieval request.
        """

        source = self.get(
            source_type
        )

        if source is None:
            return []

        return await source.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

    # ==================================================================
    # MULTI-SOURCE SEARCH
    # ==================================================================

    async def search_many(
        self,
        requests: list[
            dict[str, Any]
        ],
    ) -> list[RetrievedDocument]:
        """
        Execute multiple retrieval requests.

        Each request must contain:

            source
            query

        Optional:

            top_k
            filters
        """

        results: list[
            RetrievedDocument
        ] = []

        for request in requests:

            source_type = request.get(
                "source"
            )

            if isinstance(
                source_type,
                str,
            ):
                try:
                    source_type = (
                        RetrievalSource(
                            source_type
                        )
                    )
                except ValueError:
                    continue

            if not isinstance(
                source_type,
                RetrievalSource,
            ):
                continue

            query = request.get(
                "query",
                "",
            )

            if not isinstance(
                query,
                str,
            ):
                continue

            source_results = await self.search(
                source_type,
                query,
                top_k=request.get(
                    "top_k",
                    5,
                ),
                filters=request.get(
                    "filters"
                ),
            )

            results.extend(
                source_results
            )

        return results