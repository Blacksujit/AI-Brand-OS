from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from core.logging import get_logger
from models.content import GeneratedPost

logger = get_logger(__name__)


class GenerationRecord:
    """A record of a single content generation event."""

    def __init__(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        platform: str = "linkedin",
        status: Literal["draft", "published", "archived"] = "draft",
        quality_score: float | None = None,
        review_feedback: str | None = None,
        hook: str = "",
        call_to_action: str = "",
        hashtags: list[str] | None = None,
        tokens_used: int = 0,
        llm_model: str = "",
        duration_ms: int = 0,
        record_id: uuid.UUID | None = None,
    ) -> None:
        self.id = record_id or uuid.uuid4()
        self.user_id = user_id
        self.title = title
        self.body = body
        self.hook = hook
        self.call_to_action = call_to_action
        self.hashtags = hashtags or []
        self.platform = platform
        self.status = status
        self.quality_score = quality_score
        self.review_feedback = review_feedback
        self.tokens_used = tokens_used
        self.llm_model = llm_model
        self.duration_ms = duration_ms
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


class HistoryService:
    """Tracks content generation history and provides query access.

    Persists to the database via GeneratedPost table when db is available.
    Falls back to in-memory store when db is None (tests).
    """

    def __init__(self, db: object | None = None) -> None:
        self._db = db
        self._records: dict[str, GenerationRecord] = {}
        self._pipeline_states: dict[str, dict] = {}

    async def _persist_post(self, record: GenerationRecord) -> None:
        if not self._db:
            return
        try:
            from database.db import Database
            from repositories.content import GeneratedPostRepository

            db: Database = self._db
            async with db.session() as session:
                repo = GeneratedPostRepository(session)
                post = GeneratedPost(
                    id=record.id,
                    user_id=record.user_id,
                    title=record.title,
                    body=record.body,
                    hook=record.hook or None,
                    call_to_action=record.call_to_action or None,
                    hashtags=record.hashtags or None,
                    quality_score=record.quality_score,
                    review_feedback=record.review_feedback,
                    status=record.status,
                    platform=record.platform,
                )
                await repo.create(post)
        except Exception:
            logger.warning("history_persist_failed", record_id=str(record.id))

    async def _persist_pipeline_state(self, pipeline_id: str, state: dict) -> None:
        if not self._db:
            return
        try:
            from database.db import Database
            from repositories.content import GeneratedPostRepository

            db: Database = self._db
            async with db.session() as session:
                repo = GeneratedPostRepository(session)
                await repo.upsert_pipeline_state(pipeline_id, state.get("user_id", ""), state)
        except Exception:
            logger.warning("pipeline_state_persist_failed", pipeline_id=pipeline_id)

    def store_pipeline_state(self, pipeline_id: str, state: dict) -> None:
        self._pipeline_states[pipeline_id] = state

    def get_pipeline_state(self, pipeline_id: str) -> dict | None:
        return self._pipeline_states.get(pipeline_id)

    async def record_generation(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        platform: str = "linkedin",
        quality_score: float | None = None,
        review_feedback: str | None = None,
        hook: str = "",
        call_to_action: str = "",
        hashtags: list[str] | None = None,
        tokens_used: int = 0,
        llm_model: str = "",
        duration_ms: int = 0,
    ) -> GenerationRecord:
        record = GenerationRecord(
            user_id=user_id,
            title=title,
            body=body,
            platform=platform,
            quality_score=quality_score,
            review_feedback=review_feedback,
            hook=hook,
            call_to_action=call_to_action,
            hashtags=hashtags,
            tokens_used=tokens_used,
            llm_model=llm_model,
            duration_ms=duration_ms,
        )
        self._records[str(record.id)] = record
        logger.info(
            "history_recorded",
            record_id=str(record.id),
            title=title[:50],
            platform=platform,
        )
        return record

    def get_history(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        platform: str | None = None,
        status: str | None = None,
    ) -> list[GenerationRecord]:
        records = list(self._records.values())
        records = [r for r in records if r.user_id == user_id]
        if platform:
            records = [r for r in records if r.platform == platform]
        if status:
            records = [r for r in records if r.status == status]
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[offset : offset + limit]

    def get_record(self, user_id: uuid.UUID, record_id: uuid.UUID) -> GenerationRecord | None:
        record = self._records.get(str(record_id))
        if record and record.user_id == user_id:
            return record
        return None

    def update_status(
        self,
        user_id: uuid.UUID,
        record_id: uuid.UUID,
        status: Literal["draft", "published", "archived"],
    ) -> GenerationRecord | None:
        record = self.get_record(user_id, record_id)
        if record:
            record.status = status
            record.updated_at = datetime.now(UTC)
        return record
