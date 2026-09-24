from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: UUID
    filename: str
    chunk_count: int
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]
