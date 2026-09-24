# P4 Production RAG System

## Overview
This project rebuilds P4 as a local-first, open-source, production-style RAG system for PDF question answering.

Core stack:
- FastAPI backend
- Streamlit UI
- PostgreSQL + pgvector
- Redis
- Ollama
- Sentence Transformers
- LangChain for document loading and chunking

## Architecture
Upload PDF -> ingest and split -> embed locally -> store chunks in PostgreSQL -> ask question -> retrieve top-k chunks -> generate grounded answer -> return citations and latency.

## Open-Source Replacements
- `OpenAIEmbeddings` -> `sentence-transformers/all-MiniLM-L6-v2`
- hosted LLM -> `llama3.1:8b` via local Ollama
- LangSmith-style observability -> local structured JSON logs
- hosted vector store -> PostgreSQL + pgvector

## Folder Structure
```text
p4_production_rag/
  app/
    api/routes/
    core/
    db/
    schemas/
    services/
    utils/
  ui/
  tests/
  scripts/
  docs/
  docker-compose.yml
  Dockerfile.api
  Dockerfile.ui
  requirements.txt
  .env.example
```

## API Endpoints
- `POST /api/ingest`
- `POST /api/query`
- `GET /health`
- `GET /api/documents`
- `DELETE /api/sessions/{session_id}`

## Docker Run
```powershell
docker compose up --build
docker exec -it p4_rag_ollama ollama pull llama3.1:8b
```

Open:
- `http://localhost:8000/docs`
- `http://localhost:8501`

## Local Run
Install:
```powershell
pip install -r requirements.txt
```

Start API:
```powershell
uvicorn app.main:app --reload
```

Start UI:
```powershell
streamlit run ui/streamlit_app.py
```

## Sample Requests
Ingest:
```bash
curl -X POST "http://localhost:8000/api/ingest" -F "files=@sample.pdf"
```

Query:
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is a diffusion model?\",\"session_id\":\"demo-session\"}"
```

## Test Checklist
1. ingest one PDF
2. ask a question with an answer in the document
3. ask a question not in the document
4. confirm citations are returned
5. confirm `/health` reports component status
6. confirm uploaded documents appear in Streamlit
