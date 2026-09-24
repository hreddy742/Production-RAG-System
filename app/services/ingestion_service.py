import time

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.db.models import Document, DocumentChunk
from app.schemas.ingest import IngestedDocumentResult
from app.services.embedding_service import EmbeddingService


class IngestionService:
    def __init__(self, settings: Settings, embedding_service: EmbeddingService) -> None:
        self.settings = settings
        self.embedding_service = embedding_service
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)

    async def ingest_files(self, db: AsyncSession, files: list[UploadFile]) -> list[IngestedDocumentResult]:
        results: list[IngestedDocumentResult] = []
        for file in files:
            results.append(await self.ingest_file(db, file))
        return results

    async def ingest_file(self, db: AsyncSession, file: UploadFile) -> IngestedDocumentResult:
        if file.content_type not in {"application/pdf", "application/octet-stream"}:
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")

        started = time.perf_counter()
        temp_dir = self.settings.project_root / self.settings.temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / (file.filename or "uploaded.pdf")

        content = await file.read()
        if len(content) > self.settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{file.filename} exceeds the size limit")

        temp_path.write_bytes(content)

        try:
            pages = await run_in_threadpool(lambda: PyPDFLoader(str(temp_path)).load())
            chunks = await run_in_threadpool(lambda: self.splitter.split_documents(pages))
            embeddings = await self.embedding_service.embed_texts([chunk.page_content for chunk in chunks])

            document = Document(
                filename=file.filename or "uploaded.pdf",
                content_type=file.content_type or "application/pdf",
                chunk_count=len(chunks),
                metadata_json={"source_file": file.filename or "uploaded.pdf"},
            )
            db.add(document)
            await db.flush()

            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        content=chunk.page_content,
                        embedding=embedding,
                        chunk_metadata={
                            "source_file": file.filename or "uploaded.pdf",
                            "page_number": chunk.metadata.get("page"),
                            "chunk_index": index,
                        },
                    )
                )

            await db.commit()
            await db.refresh(document)
        finally:
            if temp_path.exists():
                temp_path.unlink()

        return IngestedDocumentResult(
            document_id=document.id,
            source_file=document.filename,
            chunk_count=document.chunk_count,
            duration_ms=(time.perf_counter() - started) * 1000,
            created_at=document.created_at,
        )
