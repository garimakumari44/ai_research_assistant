from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentModel(BaseModel):
    """
    Raw document representation
    """

    id: str

    content: str

    metadata: Dict = Field(
        default_factory=dict
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )



class ChunkModel(BaseModel):
    """
    Searchable document chunk
    """

    id: str

    document_id: str

    content: str

    metadata: Dict = Field(
        default_factory=dict
    )

    token_count: int = 0



class ProcessedDocument(BaseModel):
    """
    Output after processing
    """

    document_id: str

    chunks: List[ChunkModel]


class EmbeddingModel(BaseModel):
    """
    Vector representation
    """

    chunk_id: str

    vector: List[float]

    metadata: Dict = Field(
        default_factory=dict
    )