import asyncio

from sqlalchemy import select

from app.db.models.chunk import Chunk
from app.db.session import AsyncSessionLocal
from app.knowledge.indexing.keyword import (
    KeywordIndexItem,
    KeywordIndexer,
)


async def main():
    print("=" * 60)
    print("KEYWORD RETRIEVAL DIAGNOSTIC")
    print("=" * 60)

    index = KeywordIndexer()

    # --------------------------------------------------------------
    # Load chunks from PostgreSQL
    # --------------------------------------------------------------

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Chunk)
        )

        chunks = list(
            result.scalars().all()
        )

    print()
    print("DB chunks:", len(chunks))

    # --------------------------------------------------------------
    # Build keyword index
    # --------------------------------------------------------------

    items = []

    for chunk in chunks:
        items.append(
            KeywordIndexItem(
                chunk_id=chunk.id,
                text=chunk.content,
                metadata={
                    "document_id": str(
                        chunk.document_id
                    ),
                },
            )
        )

    await index.upsert_many(items)

    # --------------------------------------------------------------
    # Inspect index state
    # --------------------------------------------------------------

    print(
        "Keyword items:",
        await index.count(),
    )

    print(
        "BM25 exists:",
        index._bm25 is not None,
    )

    print(
        "BM25 corpus:",
        len(index._tokenized_corpus),
    )

    print(
        "Ordered IDs:",
        len(index._ordered_ids),
    )

    # --------------------------------------------------------------
    # Search
    # --------------------------------------------------------------

    query = "Attention is all you need"

    print()
    print("Query:", query)

    results = await index.search(
        query=query,
        top_k=10,
    )

    print(
        "Keyword results:",
        len(results),
    )

    # --------------------------------------------------------------
    # Display results
    # --------------------------------------------------------------

    for position, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{position}. "
            f"chunk_id={result.chunk_id} "
            f"score={result.score}"
        )

    print()
    print("=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())