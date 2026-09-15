import asyncio

from app.indexing.embeddings.generator import EmbeddingGenerator
from app.knowledge.indexing.registry import IndexRegistry


async def main():
    print("\n" + "=" * 80)
    print("RETRIEVAL INDEX DIAGNOSTIC")
    print("=" * 80)

    registry = IndexRegistry()

    print("\n[1] INDEX COUNTS")

    vector_count = await registry.vector.count()
    keyword_count = await registry.keyword.count()

    print(f"Vector index count : {vector_count}")
    print(f"Keyword index count: {keyword_count}")

    print("\n[2] VECTOR INDEX INTERNAL STATE")

    print(f"Vector _items count : {len(registry.vector._items)}")
    print(f"FAISS ntotal       : {registry.vector.faiss.index.ntotal}")
    print(f"FAISS IDs count    : {len(registry.vector.faiss.ids)}")

    print("\n[3] EMBEDDING QUERY")

    query = "Attention is all you need"

    embedder = EmbeddingGenerator()

    embedding = embedder.generate(query)

    print(f"Embedding type : {type(embedding)}")

    try:
        print(f"Embedding shape: {embedding.shape}")
    except AttributeError:
        print(f"Embedding length: {len(embedding)}")

    print("\n[4] DIRECT VECTOR SEARCH")

    try:
        vector_results = await registry.vector.search(
            embedding,
            top_k=10,
        )

        print(f"Vector results: {len(vector_results)}")

        for result in vector_results:
            print(
                f"  {result.chunk_id} | "
                f"score={result.score:.6f}"
            )

    except Exception as exc:
        print(f"VECTOR SEARCH ERROR: {type(exc).__name__}: {exc}")

    print("\n[5] DIRECT BM25 SEARCH")

    try:
        keyword_results = await registry.keyword.search(
            query=query,
            top_k=10,
        )

        print(f"Keyword results: {len(keyword_results)}")

        for result in keyword_results:
            print(
                f"  {result.chunk_id} | "
                f"score={result.score:.6f}"
            )

    except Exception as exc:
        print(f"BM25 SEARCH ERROR: {type(exc).__name__}: {exc}")

    print("\n[6] VECTOR ID CONSISTENCY")

    faiss_ids = registry.vector.faiss.ids

    missing_ids = []

    for raw_id in faiss_ids:
        if str(raw_id) not in registry.vector._items:
            missing_ids.append(str(raw_id))

    print(f"FAISS IDs          : {len(faiss_ids)}")
    print(f"Vector _items      : {len(registry.vector._items)}")
    print(f"Missing from items : {len(missing_ids)}")

    if missing_ids:
        print("\nFirst missing IDs:")

        for item_id in missing_ids[:10]:
            print(f"  {item_id}")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())