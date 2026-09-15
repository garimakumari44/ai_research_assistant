import asyncio

from app.main import _load_chunks


async def main():
    chunks = await _load_chunks()

    print(f"Loaded chunks: {len(chunks)}")

    found = 0

    for chunk in chunks:
        metadata = dict(chunk.metadata_ or {})

        if metadata.get("title") == "Attention Is All You Need":
            found += 1

            print()
            print("CHUNK:", chunk.id)
            print("DOCUMENT:", chunk.document_id)
            print("PAPER:", metadata.get("paper_id"))
            print("TITLE:", metadata.get("title"))
            print(
                "ABSTRACT:",
                bool(metadata.get("paper_abstract")),
            )

    print()
    print(
        f"Chunks with title 'Attention Is All You Need': {found}"
    )


if __name__ == "__main__":
    asyncio.run(main())
