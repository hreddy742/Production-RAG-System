import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import Settings


@lru_cache
def load_embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = load_embedding_model(self.settings.embedding_model)
        embeddings = await asyncio.to_thread(
            model.encode,
            texts,
            normalize_embeddings=True,
        )
        return embeddings.tolist()
