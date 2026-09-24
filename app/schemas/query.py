from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    session_id: str = Field(min_length=2, max_length=100)


class SourceCitation(BaseModel):
    document_id: str
    filename: str
    page_number: int | None
    chunk_index: int | None
    preview: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    latency_ms: float
    retrieval_time_ms: float
    generation_time_ms: float
    retrieved_chunks_count: int


class SessionClearResponse(BaseModel):
    session_id: str
    cleared: bool
