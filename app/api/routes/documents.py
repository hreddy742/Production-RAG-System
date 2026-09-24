from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_async_db_session
from app.db.models import Document
from app.schemas.documents import DocumentListResponse, DocumentSummary

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(db: AsyncSession = Depends(get_async_db_session)) -> DocumentListResponse:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    documents = [
        DocumentSummary(
            id=item.id,
            filename=item.filename,
            chunk_count=item.chunk_count,
            created_at=item.created_at,
        )
        for item in result.scalars().all()
    ]
    return DocumentListResponse(documents=documents)
