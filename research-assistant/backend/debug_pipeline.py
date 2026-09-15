import asyncio

from app.main import _load_persisted_indexes
from app.knowledge.indexing.registry import IndexRegistry
from app.retrieval.models import RetrievalQuery, RetrievalMode
from app.retrieval.pipeline import RetrievalPipeline


async def main():
    print("=" * 70)
    print("FULL RETRIEVAL PIPELINE DIAGNOSTIC")
    print("=" * 70)

    # --------------------------------------------------------------
    # Create the SAME shared registry architecture as main.py
    # --------------------------------------------------------------

    registry = IndexRegistry.create()

    print()
    print("Restoring indexes...")
    await _load_persisted_indexes(registry)

    # --------------------------------------------------------------
    # Inspect actual application-level state
    # --------------------------------------------------------------

    vector_count = await registry.vector.count()
    keyword_count = await registry.keyword.count()

    print()
    print("VECTOR INDEX ITEMS:", vector_count)
    print("KEYWORD INDEX ITEMS:", keyword_count)

    print(
        "FAISS COUNT:",
        registry.vector._faiss.count(),
    )

    print(
        "VECTOR _items:",
        len(registry.vector._items),
    )

    print(
        "KEYWORD _items:",
        len(registry.keyword._items),
    )

    print(
        "BM25 EXISTS:",
        registry.keyword._bm25 is not None,
    )

    # --------------------------------------------------------------
    # Create the REAL retrieval pipeline
    # --------------------------------------------------------------

    pipeline = RetrievalPipeline(
        index_registry=registry,
    )

    query = "Attention is all you need"

    request = RetrievalQuery(
        query=query,
        top_k=10,
        mode=RetrievalMode.HYBRID,
    )

    print()
    print("-" * 70)
    print("RUNNING RETRIEVAL PIPELINE")
    print("-" * 70)
    print("Query:", query)
    print("Mode:", request.mode)
    print("Top K:", request.top_k)

    # --------------------------------------------------------------
    # Run complete pipeline
    # --------------------------------------------------------------

    response = await pipeline.retrieve(request)

    # --------------------------------------------------------------
    # Print response summary
    # --------------------------------------------------------------

    print()
    print("-" * 70)
    print("PIPELINE RESPONSE")
    print("-" * 70)

    print("Total results:", response.total_results)
    print("Retrieval mode:", response.retrieval_mode)

    # --------------------------------------------------------------
    # Print internal stage counts
    # --------------------------------------------------------------

    metadata = response.metadata or {}

    print()
    print("STAGE COUNTS")
    print("-" * 70)

    for key in (
        "dense_candidates",
        "sparse_candidates",
        "fused_candidates",
        "ranked_candidates",
        "resolved_documents",
        "final_results",
    ):
        print(
            f"{key}:",
            metadata.get(key),
        )

    # --------------------------------------------------------------
    # Print routing/planning information
    # --------------------------------------------------------------

    print()
    print("ROUTING")
    print("-" * 70)

    print(
        "query_type:",
        metadata.get("query_type"),
    )

    print(
        "routing_confidence:",
        metadata.get("routing_confidence"),
    )

    print(
        "routing_reason:",
        metadata.get("routing_reason"),
    )

    print(
        "query_intent:",
        metadata.get("query_intent"),
    )

    print(
        "query_complexity:",
        metadata.get("query_complexity"),
    )

    print()
    print("PLAN")
    print("-" * 70)

    print(
        metadata.get("plan")
    )

    # --------------------------------------------------------------
    # Print actual final results
    # --------------------------------------------------------------

    print()
    print("FINAL RESULTS")
    print("-" * 70)

    for index, result in enumerate(
        response.results,
        start=1,
    ):
        document = result.document

        print()
        print(f"RESULT {index}")
        print("chunk_id:", document.chunk_id)
        print("document_id:", document.document_id)
        print("score:", result.score)
        print("retrieval_method:", result.retrieval_method)
        print(
            "text:",
            document.text[:300].replace(
                "\n",
                " ",
            ),
        )

    print()
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())