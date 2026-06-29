import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    CollectionStatsResponse,
    CollectionsResponse,
    HealthResponse,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    TextIngestRequest,
    UrlIngestRequest,
)
from app.services.chunker import chunk_text
from app.services.loaders.document_loader import load_document_text
from app.services.loaders.web_loader import load_website
from app.services.loaders.youtube_loader import load_youtube_transcript
from app.services.rag import get_rag_service
from app.services.text_cleaner import clean_text
from app.services.vector_store import get_vector_store, normalize_collection_name

settings = get_settings()

app = FastAPI(
    title="MultiSource RAG Assistant API",
    description="FastAPI backend for multi-source RAG using Supabase pgvector and Groq.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_collection_name(collection_name: str) -> str:
    normalized = normalize_collection_name(collection_name)

    if not normalized:
        raise HTTPException(status_code=400, detail="Collection name is required.")

    return normalized


def validate_text(text: str) -> None:
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in this source.")


def validate_file_size(upload_file: UploadFile) -> None:
    max_bytes = settings.max_file_mb * 1024 * 1024

    upload_file.file.seek(0, os.SEEK_END)
    size = upload_file.file.tell()
    upload_file.file.seek(0)

    if size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max allowed size is {settings.max_file_mb} MB.",
        )


def build_metadatas(
    collection_name: str,
    source_type: str,
    source_name: str,
    source_url: str | None,
    chunks: list,
) -> list[dict]:
    normalized_collection = normalize_collection_name(collection_name)

    return [
        {
            "collection_name": normalized_collection,
            "source_type": source_type,
            "source_name": source_name,
            "source_url": source_url,
            "chunk_index": chunk.index,
        }
        for chunk in chunks
    ]


def ingest_text_to_vector_db(
    collection_name: str,
    source_type: str,
    source_name: str,
    text: str,
    source_url: str | None = None,
) -> IngestResponse:
    normalized_collection = validate_collection_name(collection_name)
    validate_text(text)

    cleaned_text = clean_text(text)
    validate_text(cleaned_text)

    chunks = chunk_text(cleaned_text)

    if not chunks:
        raise HTTPException(status_code=400, detail="Text was extracted but no chunks were created.")

    metadatas = build_metadatas(
        collection_name=normalized_collection,
        source_type=source_type,
        source_name=source_name,
        source_url=source_url,
        chunks=chunks,
    )

    added_count = get_vector_store().add_chunks(
        normalized_collection,
        [chunk.text for chunk in chunks],
        metadatas,
    )

    return IngestResponse(
        collection_name=normalized_collection,
        source_type=source_type,
        source_name=source_name,
        chunks_added=added_count,
        characters=len(cleaned_text),
    )


@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "name": "MultiSource RAG Assistant API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health() -> HealthResponse:
    data = {"status": "ok", "database": "unknown"}

    try:
        get_vector_store().heartbeat()
        data["database"] = "ok"
    except Exception as exc:
        data["status"] = "error"
        data["database"] = f"error: {type(exc).__name__}"

    return HealthResponse(**data)


@app.get("/collections", response_model=CollectionsResponse, tags=["Collections"])
def list_collections() -> CollectionsResponse:
    collections = get_vector_store().list_collections()
    return CollectionsResponse(collections=collections)


@app.get(
    "/collections/{collection_name}/stats",
    response_model=CollectionStatsResponse,
    tags=["Collections"],
)
def get_collection_stats(collection_name: str) -> dict:
    return get_vector_store().collection_stats(collection_name)


@app.delete("/collections/{collection_name}", tags=["Collections"])
def delete_collection(collection_name: str) -> dict:
    normalized_collection = validate_collection_name(collection_name)
    get_vector_store().delete_collection(normalized_collection)

    return {
        "deleted": True,
        "collection_name": normalized_collection,
    }


@app.post("/ingest/text", response_model=IngestResponse, tags=["Ingestion"])
def ingest_text(payload: TextIngestRequest) -> IngestResponse:
    return ingest_text_to_vector_db(
        collection_name=payload.collection_name,
        source_type="text",
        source_name=payload.source_name or "pasted_text",
        text=payload.text,
    )


@app.post("/ingest/file", response_model=IngestResponse, tags=["Ingestion"])
def ingest_file(
    collection_name: str = Form(...),
    source_name: str | None = Form(None),
    file: UploadFile = File(...),
) -> IngestResponse:
    validate_collection_name(collection_name)
    validate_file_size(file)

    original_filename = file.filename or "uploaded_file"
    safe_source_name = source_name.strip() if source_name and source_name.strip() else original_filename
    suffix = Path(original_filename).suffix.lower()

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(file.file.read())
            temp_path = temp.name

        text = load_document_text(temp_path, original_filename)

        return ingest_text_to_vector_db(
            collection_name=collection_name,
            source_type="file",
            source_name=safe_source_name,
            text=text,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not ingest file: {type(exc).__name__}") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/ingest/url", response_model=IngestResponse, tags=["Ingestion"])
def ingest_url(payload: UrlIngestRequest) -> IngestResponse:
    try:
        text = load_website(payload.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not load website: {type(exc).__name__}") from exc

    return ingest_text_to_vector_db(
        collection_name=payload.collection_name,
        source_type="url",
        source_name=payload.url,
        text=text,
        source_url=payload.url,
    )


@app.post("/ingest/youtube", response_model=IngestResponse, tags=["Ingestion"])
def ingest_youtube(payload: UrlIngestRequest) -> IngestResponse:
    try:
        data = load_youtube_transcript(payload.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ingest_text_to_vector_db(
        collection_name=payload.collection_name,
        source_type="youtube",
        source_name=data["source_name"],
        text=data["text"],
        source_url=data["source_url"],
    )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
def query(payload: QueryRequest) -> dict:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    result = get_rag_service().answer(
        collection_name=payload.collection_name,
        question=payload.question,
        top_k=payload.top_k,
        persona=payload.persona,
        chat_history=payload.chat_history,
    )

    sources = []

    for item in result.get("sources", []):
        metadata = item.get("metadata", {}) or {}

        sources.append(
            {
                "source_type": metadata.get("source_type", "unknown"),
                "source_name": metadata.get("source_name", "unknown"),
                "chunk_index": metadata.get("chunk_index"),
                "text": item.get("text", ""),
                "score": item.get("score"),
                "metadata": metadata,
            }
        )

    return {
        "answer": result.get("answer", ""),
        "sources": sources,
    }