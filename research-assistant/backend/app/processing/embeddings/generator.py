"""
Embedding generator.

Creates vectors from document chunks.
"""

from app.processing.embeddings.model import (
    get_embedding_model
)



class EmbeddingGenerator:


    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ):

        self.model = get_embedding_model(
            model_name
        )



    def generate(
        self,
        chunks: list[dict],
    ) -> list[dict]:
        """
        Generate embeddings for chunks.
        """


        if not chunks:

            return []



        texts = [
            chunk["text"]
            for chunk in chunks
        ]



        embeddings = self.model.encode(
            texts
        )



        results = []


        for chunk, vector in zip(
            chunks,
            embeddings
        ):

            results.append(

                {
                    **chunk,

                    "embedding": vector.tolist(),

                }

            )


        return results