import asyncio

from app.db.session import AsyncSessionLocal
from app.ingestion.providers.openalex import OpenAlexProvider
from app.ingestion.providers.manager import ProviderManager
from app.repositories.paper_repository import PaperRepository
from app.papers.service import PaperService


async def main():
    provider = OpenAlexProvider()

    try:
        manager = ProviderManager(
            providers=[provider],
        )

        async with AsyncSessionLocal() as session:
            repository = PaperRepository(session=session)

            service = PaperService(
                repository=repository,
                provider_manager=manager,
            )

            print("SERVICE:", service)
            print("STARTING SEARCH...")

            result = await service.search_papers(
                query="BERT",
                page=1,
                page_size=20,
                provider="openalex",
            )

            print()
            print("RESULT:")
            print("TOTAL:", result.total)
            print("PAPERS:", len(result.papers))

            for paper in result.papers:
                print(
                    paper.id,
                    "|",
                    paper.title,
                )

    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())