
import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.chunk import Chunk


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Chunk).limit(20)
        )

        chunks = result.scalars().all()

        print("\n" + "=" * 80)
        print(f"FOUND {len(chunks)} CHUNKS")
        print("=" * 80)

        for chunk in chunks:
            print(f"\nID: {chunk.id}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Section ID: {chunk.section_id}")
            print(f"Chunk index: {chunk.chunk_index}")
            print(f"Page: {chunk.page_number}")
            print(f"Token count: {chunk.token_count}")
            print("-" * 80)
            print(chunk.content[:1500])


if __name__ == "__main__":
    asyncio.run(main())
