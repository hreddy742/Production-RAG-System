import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.query import QueryResponse, SourceCitation
from app.services.generation_service import GenerationService
from app.services.retrieval_service import RetrievalService
from app.services.session_store import SessionStore

logger = logging.getLogger(__name__)


class RagService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        generation_service: GenerationService,
        session_store: SessionStore,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.generation_service = generation_service
        self.session_store = session_store

    async def answer_question(self, db: AsyncSession, question: str, session_id: str) -> QueryResponse:
        total_start = time.perf_counter()
        cached = await self.session_store.get_cached_answer(session_id, question)
        if cached:
            return QueryResponse(**cached)

        history = await self.session_store.get_history(session_id)

        retrieval_start = time.perf_counter()
        retrieved = await self.retrieval_service.retrieve(db, question)
        retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

        context = "\n\n".join(
            f"[Source: {item['filename']} | page {item['page_number']} | chunk {item['chunk_index']}]\n{item['content']}"
            for item in retrieved
        )

        generation_start = time.perf_counter()
        answer = await self.generation_service.generate_answer(question, context, history)
        generation_time_ms = (time.perf_counter() - generation_start) * 1000
        latency_ms = (time.perf_counter() - total_start) * 1000

        sources = [
            SourceCitation(
                document_id=item["document_id"],
                filename=item["filename"],
                page_number=item["page_number"],
                chunk_index=item["chunk_index"],
                preview=item["content"][:240],
            )
            for item in retrieved
        ]

        logger.info(
            "rag_query_completed",
            extra={
                "extra": {
                    "question": question,
                    "session_id": session_id,
                    "retrieval_time_ms": round(retrieval_time_ms, 2),
                    "generation_time_ms": round(generation_time_ms, 2),
                    "latency_ms": round(latency_ms, 2),
                    "answer_length": len(answer),
                    "source_count": len(sources),
                }
            },
        )

        response = QueryResponse(
            answer=answer,
            sources=sources,
            latency_ms=latency_ms,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            retrieved_chunks_count=len(retrieved),
        )

        await self.session_store.append_turn(session_id, "user", question)
        await self.session_store.append_turn(session_id, "assistant", answer)
        await self.session_store.set_cached_answer(session_id, question, response.model_dump())
        return response
