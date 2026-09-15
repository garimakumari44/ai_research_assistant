import asyncio

from app.ingestion.providers import (
    ProviderManager,
    OpenAlexProvider,
    SemanticScholarProvider,
    CrossrefProvider,
    ArxivProvider,
)


async def main():
    openalex = OpenAlexProvider()
    semantic = SemanticScholarProvider()
    crossref = CrossrefProvider()
    arxiv = ArxivProvider()

    manager = ProviderManager(
        [
            openalex,
            semantic,
            crossref,
            arxiv,
        ]
    )

    try:
        # ==========================================
        # REGISTERED PROVIDERS
        # ==========================================
        print("\n=== REGISTERED PROVIDERS ===")
        print(manager.providers())

        # ==========================================
        # GET PROVIDER
        # ==========================================
        print("\n=== GET PROVIDER ===")

        provider = manager.get("openalex")

        print("Provider:", provider.name)

        # ==========================================
        # OPENALEX SEARCH
        # ==========================================
        print("\n=== MANAGER SEARCH: OPENALEX ===")

        results = await manager.search(
            "open access",
            provider="openalex",
            limit=3,
        )

        print("Results:", len(results))

        for paper in results:
            print("-", paper.title)
            print("  Provider:", paper.provider)
            print("  ID:", paper.provider_id)

        # ==========================================
        # CROSSREF DOI
        # ==========================================
        print("\n=== MANAGER DOI LOOKUP: CROSSREF ===")

        paper = await manager.get_by_doi(
            "10.7717/peerj.4375",
            provider="crossref",
        )

        if paper:
            print("OK")
            print("Provider:", paper.provider)
            print("ID:", paper.provider_id)
            print("Title:", paper.title)
            print("DOI:", paper.doi)
        else:
            print("NOT FOUND")

        # ==========================================
        # ARXIV ID
        # ==========================================
        print("\n=== MANAGER ID LOOKUP: ARXIV ===")

        paper = await manager.get_by_id(
            "arxiv",
            "1706.03762",
        )

        if paper:
            print("OK")
            print("Provider:", paper.provider)
            print("ID:", paper.provider_id)
            print("Title:", paper.title)
        else:
            print("NOT FOUND")

        # ==========================================
        # HEALTH CHECK
        # ==========================================
        print("\n=== HEALTH CHECK ===")

        health = await manager.health_check()

        for name, status in health.items():
            print(f"{name}: {status}")

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
                print(f"{provider.name}: closed")
            except Exception as exc:
                print(
                    f"{provider.name}: close failed: {exc}"
                )


if __name__ == "__main__":
    asyncio.run(main())