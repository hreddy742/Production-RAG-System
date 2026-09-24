# Architecture Notes

## Request Path
Streamlit -> FastAPI -> Redis history/cache -> PostgreSQL/pgvector retrieval -> Ollama generation -> response with citations

## Ingestion Path
Upload PDF -> PyPDFLoader -> RecursiveCharacterTextSplitter -> embeddings -> PostgreSQL storage

## Why This Feels Production-Style
- separate backend and frontend
- real vector database
- typed API contracts
- Redis-backed state
- structured logs
- Dockerized local stack
