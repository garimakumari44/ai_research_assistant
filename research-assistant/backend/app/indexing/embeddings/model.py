from sentence_transformers import SentenceTransformer
from functools import lru_cache

from app.core.logging import logger


MODEL_NAME = "BAAI/bge-small-en-v1.5"


class EmbeddingModel:
    """
    Wrapper around BGE embedding model.
    Handles loading and accessing the embedding model.
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
    ):
        self.model_name = model_name
        self.model = self._load_model()


    def _load_model(self):
        """
        Load SentenceTransformer model.
        """

        try:
            logger.info(
                f"Loading embedding model: {self.model_name}"
            )

            model = SentenceTransformer(
                self.model_name
            )

            logger.info(
                "Embedding model loaded successfully"
            )

            return model


        except Exception as exc:
            logger.exception(
                "Failed to load embedding model"
            )
            raise exc


    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
    ):
        """
        Convert text chunks into embeddings.

        Args:
            texts:
                List of text chunks

            batch_size:
                Number of texts processed together

        Returns:
            numpy array of embeddings
        """

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings



@lru_cache()
def get_embedding_model():
    """
    Singleton embedding model loader.

    Prevents loading the model multiple times.
    """

    return EmbeddingModel()