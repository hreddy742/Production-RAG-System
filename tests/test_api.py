from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core import dependencies
from app.main import create_app


class FakeRedis:
    async def close(self):
        return None

    async def ping(self):
        return True

    async def lrange(self, *args, **kwargs):
        return []

    async def rpush(self, *args, **kwargs):
        return None

    async def ltrim(self, *args, **kwargs):
        return None

    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None

    async def scan_iter(self, *args, **kwargs):
        if False:
            yield None


class FakeSession:
    async def execute(self, *args, **kwargs):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


def build_test_client(monkeypatch) -> TestClient:
    app = create_app()

    @asynccontextmanager
    async def fake_lifespan(app_instance):
        app_instance.state.redis = FakeRedis()
        app_instance.state.session_factory = lambda: FakeSession()
        yield

    app.router.lifespan_context = fake_lifespan

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return SimpleNamespace(raise_for_status=lambda: None)

    monkeypatch.setattr("app.api.routes.health.httpx.AsyncClient", FakeAsyncClient)
    return TestClient(app)


def test_health_endpoint(monkeypatch):
    client = build_test_client(monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_response_shape(monkeypatch):
    client = build_test_client(monkeypatch)

    class FakeRagService:
        async def answer_question(self, db, question, session_id):
            return {
                "answer": "Diffusion models reverse a noise process.",
                "sources": [
                    {
                        "document_id": "doc-1",
                        "filename": "sample.pdf",
                        "page_number": 8,
                        "chunk_index": 1,
                        "preview": "Diffusion Model learns to reverse a noise-addition process.",
                    }
                ],
                "latency_ms": 120.0,
                "retrieval_time_ms": 50.0,
                "generation_time_ms": 70.0,
                "retrieved_chunks_count": 1,
            }

    async def fake_db_dependency():
        yield None

    client.app.dependency_overrides[dependencies.get_rag_service] = lambda: FakeRagService()
    client.app.dependency_overrides[dependencies.get_async_db_session] = fake_db_dependency

    response = client.post("/api/query", json={"question": "What is a diffusion model?", "session_id": "demo"})
    assert response.status_code == 200
    assert response.json()["retrieved_chunks_count"] == 1
    assert response.json()["sources"][0]["filename"] == "sample.pdf"


def test_query_validation(monkeypatch):
    client = build_test_client(monkeypatch)
    response = client.post("/api/query", json={"question": "hi", "session_id": "x"})
    assert response.status_code == 422
