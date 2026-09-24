import hashlib
import json

from redis.asyncio import Redis

from app.core.config import Settings


class SessionStore:
    def __init__(self, redis_client: Redis, settings: Settings) -> None:
        self.redis_client = redis_client
        self.settings = settings

    def _history_key(self, session_id: str) -> str:
        return f"session:{session_id}:history"

    def _cache_key(self, session_id: str, question: str) -> str:
        digest = hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()
        return f"session:{session_id}:cache:{digest}"

    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        items = await self.redis_client.lrange(self._history_key(session_id), 0, -1)
        return [json.loads(item) for item in items]

    async def append_turn(self, session_id: str, role: str, content: str) -> None:
        key = self._history_key(session_id)
        payload = json.dumps({"role": role, "content": content})
        await self.redis_client.rpush(key, payload)
        await self.redis_client.ltrim(key, -self.settings.max_history_messages, -1)

    async def get_cached_answer(self, session_id: str, question: str) -> dict | None:
        payload = await self.redis_client.get(self._cache_key(session_id, question))
        return json.loads(payload) if payload else None

    async def set_cached_answer(self, session_id: str, question: str, response_payload: dict) -> None:
        await self.redis_client.set(
            self._cache_key(session_id, question),
            json.dumps(response_payload),
            ex=self.settings.cache_ttl_seconds,
        )

    async def clear_session(self, session_id: str) -> None:
        keys = [self._history_key(session_id)]
        async for key in self.redis_client.scan_iter(match=f"session:{session_id}:cache:*"):
            keys.append(key)
        if keys:
            await self.redis_client.delete(*keys)
