from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IngestedDocumentResult(BaseModel):
    document_id: UUID
    source_file: str
    chunk_count: int
    duration_ms: float
    created_at: datetime


class IngestResponse(BaseModel):
    documents: list[IngestedDocumentResult]
    total_documents: int
    total_chunks: int
