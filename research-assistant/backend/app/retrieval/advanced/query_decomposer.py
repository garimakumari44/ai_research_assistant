from typing import List

from app.retrieval.advanced.models import QueryAnalysis


class QueryDecomposer:
    """
    Breaks complex queries into smaller
    retrieval-friendly sub queries.

    Responsibilities:

    - Detect multi-topic questions
    - Split compound queries
    - Create focused retrieval tasks
    """


    def __init__(self):
        pass



    def decompose(
        self,
        query: str
    ) -> List[str]:
        """
        Main decomposition method.

        Example:

        Input:

        Explain LoRA and QLoRA


        Output:

        [
            Explain LoRA,
            Explain QLoRA
        ]
        """


        query = query.strip()


        # Common connectors indicating
        # multiple information needs

        connectors = [
            " and ",
            " vs ",
            " versus ",
            " compared to ",
            " compare ",
            " difference between "
        ]


        for connector in connectors:

            if connector in query.lower():

                parts = query.lower().split(
                    connector
                )


                sub_queries = []


                for part in parts:

                    cleaned = part.strip()


                    if cleaned:

                        sub_queries.append(
                            self._expand_sub_query(
                                cleaned
                            )
                        )


                # Add comparison query
                if (
                    "compare" in query.lower()
                    or "difference" in query.lower()
                    or " vs " in query.lower()
                ):

                    sub_queries.append(
                        f"Compare: {query}"
                    )


                return sub_queries



        # Single query case

        return [
            self._expand_sub_query(query)
        ]



    def _expand_sub_query(
        self,
        query: str
    ) -> str:
        """
        Adds retrieval context
        to each sub query.
        """


        return (
            f"{query} "
            "technical explanation "
            "architecture "
            "research background "
            "implementation details"
        )



    def analyze(
        self,
        query: str
    ) -> QueryAnalysis:
        """
        Returns updated QueryAnalysis object.
        """


        sub_queries = self.decompose(
            query
        )


        return QueryAnalysis(

            original_query=query,

            sub_queries=sub_queries

        )