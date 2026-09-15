from typing import List

from app.retrieval.models import RetrievedDocument



class ContextCompressor:
    """
    Compress retrieved documents before
    sending them to the LLM.

    Strategies:
    - length filtering
    - relevance filtering
    - sentence extraction

    Later can support:
    - LLM compression
    - embedding compression
    - Contextual Compression Retriever
    """



    def __init__(
        self,
        max_length: int = 1000
    ):
        """
        Args:

            max_length:
                Maximum characters per chunk
        """

        self.max_length = max_length



    def truncate_text(
        self,
        text: str
    ) -> str:
        """
        Simple length-based compression.
        """

        if len(text) <= self.max_length:

            return text


        return (
            text[:self.max_length]
            +
            "..."
        )



    def compress_document(
        self,
        document: RetrievedDocument
    ) -> RetrievedDocument:
        """
        Compress a single document.
        """

        document.text = self.truncate_text(
            document.text
        )

        return document



    def compress(
        self,
        documents: List[RetrievedDocument]
    ) -> List[RetrievedDocument]:
        """
        Compress multiple documents.
        """

        compressed = []


        for document in documents:

            compressed.append(

                self.compress_document(
                    document
                )

            )


        return compressed



    def remove_duplicates(
        self,
        documents: List[RetrievedDocument]
    ) -> List[RetrievedDocument]:
        """
        Remove duplicate chunks.
        """

        seen = set()

        unique_documents = []


        for document in documents:


            text_hash = hash(
                document.text
            )


            if text_hash not in seen:

                seen.add(
                    text_hash
                )

                unique_documents.append(
                    document
                )


        return unique_documents



    def process(
        self,
        documents: List[RetrievedDocument]
    ) -> List[RetrievedDocument]:
        """
        Complete compression pipeline.
        """

        documents = self.remove_duplicates(
            documents
        )


        documents = self.compress(
            documents
        )


        return documents