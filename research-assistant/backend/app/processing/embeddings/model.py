"""
Embedding model loader.

Responsible for loading
and managing embedding models.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.logging import logger



class EmbeddingModel:


    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
    ):

        self.model_name = model_name

        self.device = device

        self.model = self._load_model()



    def _load_model(self):

        try:

            model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )


            logger.info(
                f"Loaded embedding model: {self.model_name}"
            )


            return model


        except Exception as exc:

            logger.exception(
                "Failed loading embedding model"
            )

            raise exc



    def encode(
        self,
        texts: list[str],
    ):

        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )



    def dimension(self):

        return self.model.get_sentence_embedding_dimension()



@lru_cache()
def get_embedding_model(
    model_name: str = "BAAI/bge-small-en-v1.5",
):

    return EmbeddingModel(
        model_name=model_name
    )