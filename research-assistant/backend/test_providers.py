import asyncio

from app.ingestion.providers import OpenAlexProvider


async def main():
    provider = OpenAlexProvider()

    try:
        paper = await provider.get_by_id("W2741809807")

        if paper:
            print("OPENALEX OK")
            print("Provider:", paper.provider)
            print("ID:", paper.provider_id)
            print("Title:", paper.title)
            print("DOI:", paper.doi)
            print("Authors:", paper.authors[:3])
            print("URL:", paper.url)
            print("PDF:", paper.pdf_url)
        else:
            print("OPENALEX: PAPER NOT FOUND")

    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())