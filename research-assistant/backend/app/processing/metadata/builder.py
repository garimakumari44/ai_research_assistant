"""
Metadata builder.

Creates normalized metadata objects
used throughout the RAG pipeline.
"""

from uuid import uuid4
from datetime import datetime



class MetadataBuilder:


    def build(
        self,
        extracted_metadata: dict,
        extra_metadata: dict | None = None,
    ) -> dict:
        """
        Create final metadata object.
        """


        metadata = {

            "document_id": str(uuid4()),

            "created_at": datetime.utcnow(),

        }


        metadata.update(
            extracted_metadata
        )


        if extra_metadata:

            metadata.update(
                extra_metadata
            )


        return metadata



    def add_chunk_metadata(
        self,
        document_metadata: dict,
        chunk_index: int,
    ) -> dict:
        """
        Attach chunk level metadata.
        """


        return {

            **document_metadata,

            "chunk_index": chunk_index,

        }