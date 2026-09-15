import os
import json

from typing import List, Dict, Optional

from app.core.logging import logger

from app.indexing.metadata.schema import (
    ChunkMetadata,
)



class MetadataStore:
    """
    Stores and retrieves chunk metadata.

    Storage format:

    metadata.json

    {
        "chunk_id": {
            "document_id": "...",
            "source": "...",
            "text": "..."
        }
    }
    """


    def __init__(
        self,
        storage_path: str = "storage/metadata",
    ):

        self.storage_path = storage_path

        os.makedirs(
            self.storage_path,
            exist_ok=True,
        )


        self.file_path = os.path.join(
            self.storage_path,
            "metadata.json",
        )


        self.data = self._load()



    def _load(self):
        """
        Load metadata from disk.
        """

        if not os.path.exists(
            self.file_path
        ):
            return {}


        try:

            with open(
                self.file_path,
                "r",
                encoding="utf-8",
            ) as file:

                return json.load(file)


        except Exception as exc:

            logger.exception(
                "Failed loading metadata"
            )

            raise exc



    def _save(self):
        """
        Persist metadata.
        """

        with open(
            self.file_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4,
                default=str,
            )



    def add(
        self,
        metadata: ChunkMetadata,
    ):
        """
        Add single chunk metadata.
        """

        self.data[
            metadata.chunk_id
        ] = metadata.model_dump(
            mode="json"
        )


        self._save()


        logger.info(
            f"Metadata stored: {metadata.chunk_id}"
        )



    def add_many(
        self,
        items: List[ChunkMetadata],
    ):
        """
        Bulk insert metadata.

        Useful during indexing.
        """


        for item in items:

            self.data[
                item.chunk_id
            ] = item.model_dump(
                mode="json"
            )


        self._save()


        logger.info(
            f"Stored {len(items)} metadata records"
        )



    def get(
        self,
        chunk_id: str,
    ) -> Optional[Dict]:
        """
        Retrieve metadata by chunk ID.
        """


        return self.data.get(
            chunk_id
        )



    def get_many(
        self,
        chunk_ids: List[str],
    ):
        """
        Retrieve multiple chunks.
        """

        results = []


        for chunk_id in chunk_ids:

            metadata = self.get(
                chunk_id
            )

            if metadata:
                results.append(
                    metadata
                )


        return results



    def exists(
        self,
        chunk_id: str,
    ) -> bool:
        """
        Check if chunk already exists.
        """

        return chunk_id in self.data



    def delete(
        self,
        chunk_id: str,
    ):
        """
        Delete metadata entry.
        """

        if chunk_id in self.data:

            del self.data[
                chunk_id
            ]

            self._save()



    def count(self):
        """
        Return number of stored chunks.
        """

        return len(
            self.data
        )



    def clear(self):
        """
        Remove all metadata.
        """

        self.data = {}

        self._save()