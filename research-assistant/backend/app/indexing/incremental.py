from typing import List, Dict, Any

from app.core.logging import logger

from app.indexing.pipeline import (
    IndexingPipeline,
)

from app.indexing.metadata.store import (
    MetadataStore,
)



class IncrementalIndexer:
    """
    Incremental indexing manager.

    Handles:

    - new documents
    - duplicate detection
    - document updates
    - document deletion
    """


    def __init__(self):

        self.pipeline = IndexingPipeline()

        self.metadata_store = MetadataStore()



    def filter_new_chunks(
        self,
        chunks: List[Dict[str, Any]],
    ):
        """
        Remove chunks that already exist.

        Prevents duplicate vectors.
        """


        new_chunks = []


        for chunk in chunks:

            chunk_id = chunk["id"]


            if not self.metadata_store.exists(
                chunk_id
            ):

                new_chunks.append(
                    chunk
                )


            else:

                logger.info(
                    f"Skipping existing chunk: {chunk_id}"
                )


        return new_chunks



    def add_new_chunks(
        self,
        chunks: List[Dict[str, Any]],
    ):
        """
        Add only new chunks.
        """


        new_chunks = self.filter_new_chunks(
            chunks
        )


        if not new_chunks:

            logger.info(
                "No new chunks to index"
            )

            return



        logger.info(
            f"Adding {len(new_chunks)} new chunks"
        )


        self.pipeline.index(
            new_chunks
        )



    def update_document(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
    ):
        """
        Update a document.

        Process:

        1. Remove old chunks
        2. Add new chunks

        """

        logger.info(
            f"Updating document {document_id}"
        )


        self.delete_document(
            document_id
        )


        self.pipeline.index(
            chunks
        )



    def delete_document(
        self,
        document_id: str,
    ):
        """
        Remove document metadata.

        Note:

        FAISS deletion requires
        rebuilding or using IndexIDMap.

        This implementation removes
        metadata references.
        """


        removed = 0


        keys = list(
            self.metadata_store.data.keys()
        )


        for chunk_id in keys:


            metadata = (
                self.metadata_store.get(
                    chunk_id
                )
            )


            if metadata.get(
                "document_id"
            ) == document_id:


                self.metadata_store.delete(
                    chunk_id
                )

                removed += 1



        logger.info(
            f"Removed {removed} chunks from metadata"
        )



    def sync(
        self,
        chunks: List[Dict[str, Any]],
    ):
        """
        Synchronize incoming chunks.

        Used by:

        - file watchers
        - document upload APIs
        - crawlers
        """


        self.add_new_chunks(
            chunks
        )


        logger.info(
            "Incremental sync completed"
        )