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

    async def store_pipeline_state(self, pipeline_id: str, state: dict) -> None:
        self._pipeline_states[pipeline_id] = state
        await self._persist_pipeline_state(pipeline_id, state)

    async def get_pipeline_state(self, pipeline_id: str) -> dict | None:
        cached = self._pipeline_states.get(pipeline_id)
        if cached is not None:
            return cached
        if self._db is not None:
            try:
                from database.db import Database
                from repositories.content import GeneratedPostRepository

                db: Database = self._db
                async with db.session() as session:
                    repo = GeneratedPostRepository(session)
                    posts = await repo.list_by_user(
                        uuid.UUID(int=0), limit=1
                    )
                    for post in posts:
                        if post.extra_metadata:
                            ps = post.extra_metadata.get("pipeline_state")
                            if ps:
                                self._pipeline_states[pipeline_id] = ps
                                return ps
            except Exception:
                logger.warning("pipeline_state_db_read_failed", pipeline_id=pipeline_id)
        return None

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
        await self._persist_post(record)
        return record

    async def get_history(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        platform: str | None = None,
        status: str | None = None,
    ) -> list[GenerationRecord]:
        if self._db is not None:
            try:
                from database.db import Database
                from models.content import GeneratedPost as DBPost
                from repositories.content import GeneratedPostRepository

                db: Database = self._db
                async with db.session() as session:
                    repo = GeneratedPostRepository(session)
                    db_posts = await repo.list_by_user(
                        user_id, offset=offset, limit=limit, platform=platform, status=status
                    )
                    db_records: dict[str, GenerationRecord] = {}
                    for p in db_posts:
                        rec = GenerationRecord(
                            user_id=p.user_id,
                            title=p.title,
                            body=p.body,
                            platform=p.platform or "linkedin",
                            status=p.status or "draft",
                            quality_score=p.quality_score,
                            review_feedback=p.review_feedback,
                            hook=p.hook or "",
                            call_to_action=p.call_to_action or "",
                            hashtags=p.hashtags or [],
                            record_id=p.id,
                        )
                        rec.created_at = p.created_at if p.created_at else rec.created_at
                        rec.updated_at = p.updated_at if p.updated_at else rec.updated_at
                        db_records[str(p.id)] = rec

                    for rid, rec in self._records.items():
                        if rec.user_id == user_id:
                            db_records[rid] = rec

                    result = sorted(db_records.values(), key=lambda r: r.created_at, reverse=True)
                    return result[offset : offset + limit]
            except Exception:
                logger.warning("history_db_read_failed")

        records = list(self._records.values())
        records = [r for r in records if r.user_id == user_id]
        if platform:
            records = [r for r in records if r.platform == platform]
        if status:
            records = [r for r in records if r.status == status]
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[offset : offset + limit]

    async def get_record(self, user_id: uuid.UUID, record_id: uuid.UUID) -> GenerationRecord | None:
        cached = self._records.get(str(record_id))
        if cached and cached.user_id == user_id:
            return cached
        if self._db is not None:
            try:
                from database.db import Database
                from repositories.content import GeneratedPostRepository

                db: Database = self._db
                async with db.session() as session:
                    repo = GeneratedPostRepository(session)
                    post = await repo.get_by_id(record_id)
                    if post and post.user_id == user_id:
                        rec = GenerationRecord(
                            user_id=post.user_id,
                            title=post.title,
                            body=post.body,
                            platform=post.platform or "linkedin",
                            status=post.status or "draft",
                            quality_score=post.quality_score,
                            review_feedback=post.review_feedback,
                            hook=post.hook or "",
                            call_to_action=post.call_to_action or "",
                            hashtags=post.hashtags or [],
                            record_id=post.id,
                        )
                        if post.created_at:
                            rec.created_at = post.created_at
                        if post.updated_at:
                            rec.updated_at = post.updated_at
                        self._records[str(record_id)] = rec
                        return rec
            except Exception:
                logger.warning("history_db_record_read_failed", record_id=str(record_id))
        return None

    async def update_status(
        self,
        user_id: uuid.UUID,
        record_id: uuid.UUID,
        status: Literal["draft", "published", "archived"],
    ) -> GenerationRecord | None:
        record = await self.get_record(user_id, record_id)
        if record:
            record.status = status
            record.updated_at = datetime.now(UTC)
            self._records[str(record_id)] = record
            if self._db is not None:
                try:
                    from database.db import Database
                    from repositories.content import GeneratedPostRepository

                    db: Database = self._db
                    async with db.session() as session:
                        repo = GeneratedPostRepository(session)
                        await repo.update_status(record_id, status)
                        await session.commit()
                except Exception:
                    logger.warning("history_status_update_failed", record_id=str(record_id))
        return record