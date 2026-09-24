import httpx
from fastapi import APIRouter, Request
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def healthcheck(request: Request) -> HealthResponse:
    settings = get_settings()
    database_status = "ok"
    redis_status = "ok"
    ollama_status = "ok"

    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    try:
        redis_client: Redis = request.app.state.redis
        await redis_client.ping()
    except Exception:
        redis_status = "error"

    try:
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=10.0) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
    except Exception:
        ollama_status = "error"

    status = "ok" if all(item == "ok" for item in [database_status, redis_status, ollama_status]) else "degraded"
    return HealthResponse(
        status=status,
        app="ok",
        database=database_status,
        redis=redis_status,
        ollama=ollama_status,
    )
