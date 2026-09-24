from collections.abc import AsyncGenerator

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.services.embedding_service import EmbeddingService
from app.services.generation_service import GenerationService
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService
from app.services.session_store import SessionStore


def get_app_settings() -> Settings:
    return get_settings()


async def get_async_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session(request.app.state.session_factory):
        yield session


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis


def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    return IngestionService(settings, EmbeddingService(settings))


def get_session_store(request: Request) -> SessionStore:
    settings = get_settings()
    return SessionStore(request.app.state.redis, settings)


def get_rag_service(request: Request) -> RagService:
    settings = get_settings()
    embedding_service = EmbeddingService(settings)
    retrieval_service = RetrievalService(embedding_service, settings.retrieval_top_k)
    generation_service = GenerationService(settings)
    session_store = SessionStore(request.app.state.redis, settings)
    return RagService(retrieval_service, generation_service, session_store)
