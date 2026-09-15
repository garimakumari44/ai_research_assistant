from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field



class ChunkMetadata(BaseModel):
    """
    Metadata associated with a document chunk.

    This connects FAISS vectors back
    to the original source.
    """


    chunk_id: str = Field(
        ...,
        description="Unique chunk identifier"
    )


    document_id: str = Field(
        ...,
        description="Original document identifier"
    )


    source: str = Field(
        ...,
        description="Document source path or URL"
    )


    text: Optional[str] = Field(
        default=None,
        description="Original chunk text"
    )


    page_number: Optional[int] = Field(
        default=None,
        description="PDF page number"
    )


    section: Optional[str] = Field(
        default=None,
        description="Document section heading"
    )


    file_type: Optional[str] = Field(
        default=None,
        description="pdf, markdown, html, etc."
    )


    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )



    class Config:
        json_schema_extra = {
            "example": {

                "chunk_id": "doc1_chunk_001",

                "document_id": "research_paper_001",

                "source": "paper.pdf",

                "text": "Retrieval augmented generation combines search and generation.",

                "page_number": 3,

                "section": "Introduction",

                "file_type": "pdf",

                "extra": {
                    "author": "John Doe"
                }

            }
        }