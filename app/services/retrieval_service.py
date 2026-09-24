from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService, top_k: int) -> None:
        self.embedding_service = embedding_service
        self.top_k = top_k

    async def retrieve(self, db: AsyncSession, question: str) -> list[dict]:
        query_embedding = await self.embedding_service.embed_query(question)

        stmt = (
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(self.top_k)
        )
        result = await db.execute(stmt)

        return [
            {
                "document_id": str(document.id),
                "filename": document.filename,
                "content": chunk.content,
                "page_number": chunk.chunk_metadata.get("page_number"),
                "chunk_index": chunk.chunk_metadata.get("chunk_index"),
            }
            for chunk, document in result.all()
        ]
