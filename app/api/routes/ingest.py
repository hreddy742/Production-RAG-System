from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_async_db_session, get_ingestion_service
from app.schemas.ingest import IngestResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("", response_model=IngestResponse)
async def ingest_documents(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_async_db_session),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> IngestResponse:
    results = await ingestion_service.ingest_files(db, files)
    return IngestResponse(
        documents=results,
        total_documents=len(results),
        total_chunks=sum(item.chunk_count for item in results),
    )
