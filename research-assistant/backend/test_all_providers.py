import asyncio

from app.ingestion.providers import (
    OpenAlexProvider,
    SemanticScholarProvider,
    CrossrefProvider,
    ArxivProvider,
)


async def test_provider(name, operation):
    print(f"\n=== {name} ===")

    try:
        result = await operation()

        if isinstance(result, list):
            print("OK")
            print("Results:", len(result))

            for paper in result[:3]:
                print("-", paper.title)
                print("  ID:", paper.provider_id)
                print("  DOI:", paper.doi)

        elif result:
            print("OK")
            print("Title:", result.title)
            print("ID:", result.provider_id)
            print("DOI:", result.doi)
            print("Authors:", result.authors[:3])

        else:
            print("NOT FOUND")

    except Exception as exc:
        print("FAILED")
        print(type(exc).__name__)
        print(exc)


async def main():

    openalex = OpenAlexProvider()
    semantic = SemanticScholarProvider()
    crossref = CrossrefProvider()
    arxiv = ArxivProvider()

    try:

        await test_provider(
            "OPENALEX",
            lambda: openalex.get_by_id(
                "W2741809807"
            ),
        )

        await test_provider(
            "SEMANTIC SCHOLAR",
            lambda: semantic.search(
                "attention is all you need",
                limit=3,
            ),
        )

        await test_provider(
            "CROSSREF",
            lambda: crossref.get_by_doi(
                "10.48550/arXiv.1706.03762"
            ),
        )

        await test_provider(
            "ARXIV",
            lambda: arxiv.get_by_id(
                "1706.03762"
            ),
        )

    finally:

        print("\n=== CLOSING PROVIDERS ===")

        for provider in [
            openalex,
            semantic,
            crossref,
            arxiv,
        ]:
            try:
                await provider.close()
                print(
                    f"{provider.name}: closed"
                )
            except Exception as exc:
                print(
                    f"{provider.name}: close failed: {exc}"
                )


if __name__ == "__main__":
    asyncio.run(main())