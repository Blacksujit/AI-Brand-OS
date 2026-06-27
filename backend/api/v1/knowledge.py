# ruff: noqa: B008
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user_id, get_db_session
from core.chroma import ChromaService
from core.config import Settings, get_settings
from core.embedding import EmbeddingService
from core.logging import get_logger
from database.db import Database
from schemas.knowledge import (
    AddKnowledgeEntryRequest,
    IngestMarkdownRequest,
    IngestResponse,
    IngestUrlRequest,
    KnowledgeContextResponse,
    KnowledgeEntryResponse,
    KnowledgeListResponse,
    KnowledgeSearchResponse,
    KnowledgeTagResponse,
    UpdateKnowledgeEntryRequest,
)
from services.ingestion import IngestionPipeline
from services.knowledge import KnowledgeBaseService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = get_logger(__name__)


async def _get_kb_service(db: Database = Depends(get_db_session)) -> KnowledgeBaseService:
    return KnowledgeBaseService(db, None, None)  # type: ignore[arg-type]


async def _get_ingestion(
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> IngestionPipeline:
    from core.llm import LLMClient

    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    llm = LLMClient(settings)
    return IngestionPipeline(db, kb, llm)


@router.get("/entries", response_model=KnowledgeListResponse)
async def list_entries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tag: str | None = None,
    source_type: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeListResponse:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    return await kb.list_entries(
        user_id=user_id,
        page=page,
        page_size=page_size,
        tag=tag,
        source_type=source_type,
    )


@router.post("/entries", response_model=KnowledgeEntryResponse, status_code=201)
async def add_entry(
    body: AddKnowledgeEntryRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeEntryResponse:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    entry = await kb.add_entry(user_id, body)
    return _entry_to_response(entry)


@router.get("/entries/{entry_id}", response_model=KnowledgeEntryResponse)
async def get_entry(
    entry_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeEntryResponse:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    entry = await kb.get_entry(user_id, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    async with db.session() as session:
        from repositories.knowledge import KnowledgeTagRepository

        tag_repo = KnowledgeTagRepository(session)
        tags = await tag_repo.get_tags_for_entry(entry.id)

    resp = _entry_to_response(entry)
    resp.tags = [t.name for t in tags]
    return resp


@router.put("/entries/{entry_id}", response_model=KnowledgeEntryResponse)
async def update_entry(
    entry_id: uuid.UUID,
    body: UpdateKnowledgeEntryRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeEntryResponse:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    entry = await kb.update_entry(user_id, entry_id, body)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return _entry_to_response(entry)


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> None:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    deleted = await kb.delete_entry(user_id, entry_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_entries(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeSearchResponse:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    return await kb.search(user_id=user_id, query_text=q, limit=limit)


@router.get("/tags", response_model=list[KnowledgeTagResponse])
async def list_tags(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[KnowledgeTagResponse]:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    return await kb.get_tags(user_id)


@router.post("/ingest/markdown", response_model=IngestResponse, status_code=201)
async def ingest_markdown(
    body: IngestMarkdownRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    pipeline: IngestionPipeline = Depends(_get_ingestion),
) -> IngestResponse:
    return await pipeline.ingest_markdown(
        user_id=user_id,
        title=body.title,
        content=body.content,
        source_id=body.source_id,
        tags=body.tags,
    )


@router.post("/ingest/url", response_model=IngestResponse, status_code=201)
async def ingest_url(
    body: IngestUrlRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    pipeline: IngestionPipeline = Depends(_get_ingestion),
) -> IngestResponse:
    return await pipeline.ingest_url(
        user_id=user_id,
        url=body.url,
        title=body.title,
        tags=body.tags,
    )


@router.get("/context", response_model=KnowledgeContextResponse)
async def get_context(
    limit: int = Query(default=20, ge=1, le=50),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeContextResponse:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    kb = KnowledgeBaseService(db, chroma, embedding)
    items = await kb.get_recent_context(user_id, limit)
    tags = await kb.get_tags(user_id)
    return KnowledgeContextResponse(
        items=items,
        tags=tags,
        total_count=len(items),
    )


def _entry_to_response(entry: object) -> KnowledgeEntryResponse:
    return KnowledgeEntryResponse(
        id=str(entry.id),
        user_id=str(entry.user_id),
        source_type=entry.source_type,
        source_id=entry.source_id,
        title=entry.title,
        content=entry.content,
        summary=entry.summary,
        tags=[],
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
    )
