from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_async_db_session, get_rag_service, get_session_store
from app.schemas.query import QueryRequest, QueryResponse, SessionClearResponse
from app.services.rag_service import RagService
from app.services.session_store import SessionStore

router = APIRouter(tags=["rag"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_async_db_session),
    rag_service: RagService = Depends(get_rag_service),
) -> QueryResponse:
    return await rag_service.answer_question(db, payload.question, payload.session_id)


@router.delete("/sessions/{session_id}", response_model=SessionClearResponse)
async def clear_session(
    session_id: str,
    session_store: SessionStore = Depends(get_session_store),
) -> SessionClearResponse:
    await session_store.clear_session(session_id)
    return SessionClearResponse(session_id=session_id, cleared=True)
