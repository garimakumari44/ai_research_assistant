from typing import List

from app.retrieval.advanced.models import (
    QueryIntent,
    RetrievalSource
)


class SourceSelector:
    """
    Selects retrieval sources based on
    query intent.

    This controls which retrievers
    are executed.

    Example:

    RESEARCH
        |
        +-- arxiv
        +-- papers
        +-- documentation


    CODING
        |
        +-- github
        +-- documentation
    """



    def __init__(self):

        self.source_mapping = {


            QueryIntent.RESEARCH:
            [
                RetrievalSource.ARXIV,
                RetrievalSource.DOCUMENTATION,
                RetrievalSource.VECTOR_DB
            ],



            QueryIntent.CODING:
            [
                RetrievalSource.GITHUB,
                RetrievalSource.DOCUMENTATION,
                RetrievalSource.VECTOR_DB
            ],



            QueryIntent.COMPARISON:
            [
                RetrievalSource.ARXIV,
                RetrievalSource.DOCUMENTATION,
                RetrievalSource.VECTOR_DB
            ],



            QueryIntent.SUMMARY:
            [
                RetrievalSource.VECTOR_DB,
                RetrievalSource.DOCUMENTATION
            ],



            QueryIntent.TROUBLESHOOTING:
            [
                RetrievalSource.GITHUB,
                RetrievalSource.DOCUMENTATION,
                RetrievalSource.WEB
            ],



            QueryIntent.EXPLANATION:
            [
                RetrievalSource.VECTOR_DB,
                RetrievalSource.DOCUMENTATION
            ],



            QueryIntent.FACTUAL:
            [
                RetrievalSource.VECTOR_DB
            ]

        }



    def select(
        self,
        intent: QueryIntent
    ) -> List[str]:
        """
        Returns sources for given intent.

        Example:

        Input:

        QueryIntent.RESEARCH


        Output:

        [
            "arxiv",
            "documentation",
            "vector_db"
        ]
        """


        sources = self.source_mapping.get(
            intent,
            [
                RetrievalSource.VECTOR_DB
            ]
        )


        return [
            source.value
            for source in sources
        ]



    def select_with_priority(
        self,
        intent: QueryIntent
    ) -> List[dict]:
        """
        Returns sources with priority.

        Useful for retrieval planning.

        Higher priority sources
        execute first.
        """


        sources = self.select(
            intent
        )


        return [

            {
                "source": source,
                "priority": index + 1
            }

            for index, source
            in enumerate(sources)

        ]



    def add_source(
        self,
        intent: QueryIntent,
        source: RetrievalSource
    ):
        """
        Dynamically add a retrieval source.

        Useful when adding new connectors.

        Example:

        Add:
        Knowledge Graph
        Web Search
        Internal Docs
        """


        if intent not in self.source_mapping:

            self.source_mapping[intent] = []


        if source not in self.source_mapping[intent]:

            self.source_mapping[intent].append(
                source
            )