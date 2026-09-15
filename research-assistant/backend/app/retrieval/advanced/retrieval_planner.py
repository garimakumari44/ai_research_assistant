from typing import List

from app.retrieval.advanced.models import (
    QueryAnalysis,
    RetrievalPlan,
    RetrievalTask,
    QueryIntent,
    RetrievalSource
)

from app.retrieval.advanced.query_rewriter import (
    QueryRewriter
)

from app.retrieval.advanced.query_decomposer import (
    QueryDecomposer
)

from app.retrieval.advanced.intent_classifier import (
    IntentClassifier
)

from app.retrieval.advanced.source_selector import (
    SourceSelector
)



class RetrievalPlanner:
    """
    Main controller for adaptive retrieval.

    Pipeline:

    User Query

        |
        v

    Intent Classification

        |
        v

    Query Rewriting

        |
        v

    Query Decomposition

        |
        v

    Source Selection

        |
        v

    Retrieval Plan


    """


    def __init__(self):

        self.query_rewriter = QueryRewriter()

        self.query_decomposer = QueryDecomposer()

        self.intent_classifier = IntentClassifier()

        self.source_selector = SourceSelector()



    def create_plan(
        self,
        query: str
    ) -> RetrievalPlan:
        """
        Generates executable retrieval plan.
        """


        # Step 1:
        # Understand user intent

        intent = self.intent_classifier.classify(
            query
        )


        # Step 2:
        # Rewrite query

        rewritten_query = self.query_rewriter.rewrite(
            query
        )


        # Step 3:
        # Break into smaller queries

        sub_queries = self.query_decomposer.decompose(
            query
        )


        # Step 4:
        # Select retrieval sources

        sources = self.source_selector.select(
            intent
        )


        # Step 5:
        # Create retrieval tasks

        tasks = self._build_tasks(
            sub_queries,
            sources
        )


        return RetrievalPlan(

            original_query=query,

            intent=intent,

            tasks=tasks,

            execution_strategy="parallel"

        )



    def _build_tasks(
        self,
        queries: List[str],
        sources: List[str]
    ) -> List[RetrievalTask]:
        """
        Converts queries and sources
        into retrieval jobs.
        """


        tasks = []


        for query in queries:

            for source in sources:


                tasks.append(

                    RetrievalTask(

                        query=query,

                        source=RetrievalSource(
                            source
                        ),

                        top_k=5

                    )

                )


        return tasks



    def analyze_query(
        self,
        query: str
    ) -> QueryAnalysis:
        """
        Returns complete query analysis.

        Useful for debugging
        and monitoring.
        """


        intent = self.intent_classifier.classify(
            query
        )


        rewritten = self.query_rewriter.rewrite(
            query
        )


        sub_queries = self.query_decomposer.decompose(
            query
        )


        sources = self.source_selector.select(
            intent
        )


        return QueryAnalysis(

            original_query=query,

            rewritten_query=rewritten,

            intent=intent,

            sub_queries=sub_queries,

            selected_sources=sources

        )