import asyncio

from app.knowledge.indexing.registry import IndexRegistry

async def main():
    registry = IndexRegistry()
    await registry.restore()

    items = registry.vector_indexer.items()

    print(f"\nVECTOR ITEMS: {len(items)}")

    for item in items[:10]:
        print("\n--- ITEM ---")
        print("chunk_id:", item.chunk_id)
        print("metadata:", item.metadata)
        print("title:", item.metadata.get("title"))

asyncio.run(main())
