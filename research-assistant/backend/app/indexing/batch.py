from typing import List, Dict, Any, Generator

from app.core.logging import logger

from app.indexing.pipeline import (
    IndexingPipeline,
)



class BatchIndexer:
    """
    Handles batch indexing of large datasets.

    Used for:

    - large PDFs
    - arXiv papers
    - GitHub repositories
    - documentation websites

    Flow:

    Chunks
       |
       ↓
    Split batches
       |
       ↓
    Index each batch
    """



    def __init__(
        self,
        batch_size: int = 100,
    ):

        self.batch_size = batch_size

        self.pipeline = (
            IndexingPipeline()
        )



    def create_batches(
        self,
        chunks: List[Dict[str, Any]],
    ) -> Generator:

        """
        Split chunks into smaller batches.

        Example:

        1000 chunks

        batch_size=100

        returns:

        10 batches
        """


        total = len(chunks)


        for start in range(
            0,
            total,
            self.batch_size,
        ):

            yield chunks[
                start:
                start + self.batch_size
            ]



    def index_batches(
        self,
        chunks: List[Dict[str, Any]],
    ):
        """
        Index chunks batch by batch.
        """


        total_chunks = len(
            chunks
        )


        logger.info(
            f"Starting batch indexing: {total_chunks} chunks"
        )


        processed = 0


        batch_number = 1



        for batch in self.create_batches(
            chunks
        ):

            logger.info(
                f"Processing batch {batch_number}"
            )


            self.pipeline.index(
                batch
            )


            processed += len(
                batch
            )


            logger.info(
                f"Processed {processed}/{total_chunks}"
            )


            batch_number += 1



        logger.info(
            "Batch indexing completed"
        )



    def index_stream(
        self,
        chunk_generator,
    ):
        """
        Index streaming chunks.

        Useful when:

        - reading huge files
        - crawling websites
        - processing repositories
        """


        batch = []


        for chunk in chunk_generator:


            batch.append(
                chunk
            )


            if len(batch) >= self.batch_size:


                self.pipeline.index(
                    batch
                )


                batch = []



        # remaining chunks

        if batch:

            self.pipeline.index(
                batch
            )


        logger.info(
            "Streaming indexing completed"
        )