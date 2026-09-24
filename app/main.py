from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.routes import documents, health, ingest, query
from app.core.config import get_settings
from app.db.session import create_engine_and_sessionmaker, init_database
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)

    engine, session_factory = create_engine_and_sessionmaker(settings)
    await init_database(engine)

    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    yield

    await app.state.redis.close()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(documents.router, prefix=settings.api_prefix)
    app.include_router(ingest.router, prefix=settings.api_prefix)
    app.include_router(query.router, prefix=settings.api_prefix)
    return app


app = create_app()
