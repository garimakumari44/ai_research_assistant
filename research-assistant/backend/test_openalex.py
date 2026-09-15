import asyncio

from app.ingestion.providers.openalex import OpenAlexProvider


async def main():
    provider = OpenAlexProvider()

    try:
        papers = await provider.search(
            "retrieval augmented generation",
            limit=5,
        )

        print(f"\nFetched papers: {len(papers)}\n")

        for i, paper in enumerate(papers, start=1):
            print(f"{i}. {paper.title}")
            print(f"   ID: {paper.provider_id}")
            print(f"   DOI: {paper.doi}")
            print(f"   Authors: {paper.authors}")
            print(f"   Published: {paper.published_at}")
            print()

    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())