import asyncio

from app.ingestion.providers import CrossrefProvider


async def main():
    provider = CrossrefProvider()

    try:
        doi = "10.7717/peerj.4375"

        print("Testing DOI:", doi)

        paper = await provider.get_by_doi(doi)

        if paper:
            print("CROSSREF OK")
            print("Provider:", paper.provider)
            print("ID:", paper.provider_id)
            print("Title:", paper.title)
            print("DOI:", paper.doi)
            print("Authors:", paper.authors[:5])
            print("Journal:", paper.journal)
            print("Venue:", paper.venue)
            print("Published:", paper.published_at)
            print("Citations:", paper.citation_count)
        else:
            print("CROSSREF NOT FOUND")

    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())