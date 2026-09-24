import httpx

from app.core.config import Settings


SYSTEM_PROMPT = (
    "You are a document question-answering assistant. "
    "Answer only from the retrieved context. "
    "If the answer is not supported by the retrieved context, say clearly that it was not found in the document."
)


class GenerationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_answer(self, question: str, context: str, history: list[dict[str, str]]) -> str:
        history_text = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history[-self.settings.max_history_messages :]
        )
        prompt = (
            f"Conversation history:\n{history_text or 'None'}\n\n"
            f"Retrieved context:\n{context or 'No context retrieved.'}\n\n"
            f"Question:\n{question}"
        )

        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=180.0) as client:
            response = await client.post(
                "/api/chat",
                json={
                    "model": self.settings.chat_model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
