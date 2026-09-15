"""
Semantic based document chunking.

Uses sentence boundaries.
"""

from uuid import uuid4

import nltk


class SemanticChunker:


    def __init__(
        self,
        max_words: int = 300,
    ):

        self.max_words = max_words


        nltk.download(
            "punkt",
            quiet=True
        )


    def chunk(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[dict]:


        sentences = nltk.sent_tokenize(
            text
        )


        chunks = []

        current = []

        count = 0


        for sentence in sentences:

            words = len(
                sentence.split()
            )


            if count + words > self.max_words:

                chunks.append(
                    self._create_chunk(
                        current,
                        metadata
                    )
                )


                current = []

                count = 0


            current.append(sentence)

            count += words



        if current:

            chunks.append(
                self._create_chunk(
                    current,
                    metadata
                )
            )


        return chunks



    def _create_chunk(
        self,
        sentences,
        metadata
    ):

        text = " ".join(sentences)


        return {
            "chunk_id": str(uuid4()),
            "text": text,
            "token_count": len(text.split()),
            "metadata": metadata or {},
        }