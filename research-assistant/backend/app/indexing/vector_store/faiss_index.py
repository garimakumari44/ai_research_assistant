import faiss
import numpy as np

from typing import List, Dict, Any

from app.core.logging import logger



class FAISSIndex:
    """
    FAISS vector database wrapper.

    Handles:
    - index creation
    - adding embeddings
    - similarity search
    """


    def __init__(
        self,
        dimension: int = 384,
    ):
        """
        BGE-small embedding dimension = 384
        """

        self.dimension = dimension

        self.index = self._create_index()

        self.ids = []


    def _create_index(self):
        """
        Create FAISS cosine similarity index.

        Using:
        IndexFlatIP

        Because embeddings are normalized,
        inner product = cosine similarity.
        """

        logger.info(
            "Creating FAISS index"
        )


        index = faiss.IndexFlatIP(
            self.dimension
        )


        logger.info(
            "FAISS index created"
        )


        return index



    def add(
        self,
        embeddings: List,
        ids: List[str],
    ):
        """
        Add embeddings into FAISS.

        Args:

        embeddings:
            List of vectors

        ids:
            Chunk identifiers
        """


        if len(embeddings) != len(ids):
            raise ValueError(
                "Embeddings and IDs count mismatch"
            )


        vectors = np.asarray(
            embeddings,
            dtype="float32",
        )


        self.index.add(
            vectors
        )


        self.ids.extend(
            ids
        )


        logger.info(
            f"Added {len(ids)} vectors to FAISS"
        )



    def search(
        self,
        query_embedding,
        top_k: int = 5,
    ):
        """
        Search similar vectors.

        Returns:

        [
            {
              id:"",
              score:0.95
            }
        ]

        """


        query = np.asarray(
            [query_embedding],
            dtype="float32",
        )


        scores, indexes = self.index.search(
            query,
            top_k,
        )


        results = []


        for score, idx in zip(
            scores[0],
            indexes[0],
        ):

            if idx == -1:
                continue


            results.append(
                {
                    "id": self.ids[idx],
                    "score": float(score),
                }
            )


        return results



    def count(self):
        """
        Return number of vectors.
        """

        return self.index.ntotal



    def reset(self):
        """
        Clear FAISS index.
        """

        self.index = self._create_index()

        self.ids = []


        logger.info(
            "FAISS index reset"
        )