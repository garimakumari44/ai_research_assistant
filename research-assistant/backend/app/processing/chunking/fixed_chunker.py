"""
Fixed size document chunking.

Used for:
- PDFs
- Articles
- Documentation
- General text
"""

from uuid import uuid4

from app.processing.tokenization import get_tokenizer


class FixedChunker:

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 100,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.tokenizer = get_tokenizer()


    def chunk(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[dict]:
        """
        Split text into fixed token chunks.
        """

        if not text:
            return []


        tokens = self.tokenizer.encode(text)

        chunks = []

        start = 0


        while start < len(tokens):

            end = start + self.chunk_size

            chunk_tokens = tokens[start:end]

            chunk_text = self.tokenizer.decode(
                chunk_tokens
            )


            chunks.append(
                {
                    "chunk_id": str(uuid4()),
                    "text": chunk_text,
                    "token_count": len(chunk_tokens),
                    "metadata": metadata or {},
                }
            )


            start = end - self.overlap


        return chunks