print("\n=== DIRECT RETRIEVAL TEST ===")

query = "Attention is all you need"

print("\n--- KEYWORD ---")
keyword_results = keyword_retriever.search(
    query,
    top_k=10,
    filters={},
)

print("count:", len(keyword_results))

for i, result in enumerate(keyword_results[:10], start=1):
    print(
        i,
        "chunk_id=", result.chunk_id,
        "score=", result.score,
        "content=", result.content[:150],
    )


print("\n--- DENSE ---")
dense_results = dense_retriever.search(
    query,
    top_k=10,
    filters={},
)

print("count:", len(dense_results))

for i, result in enumerate(dense_results[:10], start=1):
    print(
        i,
        "chunk_id=", result.chunk_id,
        "score=", result.score,
        "content=", result.content[:150],
    )


print("\n--- HYBRID ---")
hybrid_results = hybrid_retriever.search(
    query,
    top_k=10,
    filters={},
)

print("count:", len(hybrid_results))

for i, result in enumerate(hybrid_results[:10], start=1):
    print(
        i,
        "chunk_id=", result.chunk_id,
        "score=", result.score,
        "content=", result.content[:150],
    )