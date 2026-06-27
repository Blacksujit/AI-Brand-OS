from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger
from models.content import AgentRun, GeneratedPost

logger = get_logger(__name__)


class GeneratedPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, post: GeneratedPost) -> GeneratedPost:
        self._session.add(post)
        await self._session.flush()
        return post

    async def get_by_id(self, post_id: uuid.UUID) -> GeneratedPost | None:
        result = await self._session.execute(
            select(GeneratedPost).where(GeneratedPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
        platform: str | None = None,
        status: str | None = None,
    ) -> list[GeneratedPost]:
        query = select(GeneratedPost).where(GeneratedPost.user_id == user_id)
        if platform:
            query = query.where(GeneratedPost.platform == platform)
        if status:
            query = query.where(GeneratedPost.status == status)
        query = query.order_by(GeneratedPost.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: uuid.UUID,
        platform: str | None = None,
        status: str | None = None,
    ) -> int:
        query = select(func.count(GeneratedPost.id)).where(GeneratedPost.user_id == user_id)
        if platform:
            query = query.where(GeneratedPost.platform == platform)
        if status:
            query = query.where(GeneratedPost.status == status)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def update_status(
        self,
        post_id: uuid.UUID,
        status: str,
    ) -> GeneratedPost | None:
        await self._session.execute(
            sql_update(GeneratedPost)
            .where(GeneratedPost.id == post_id)
            .values(status=status)
        )
        return await self.get_by_id(post_id)

    async def delete(self, post_id: uuid.UUID) -> None:
        await self._session.execute(delete(GeneratedPost).where(GeneratedPost.id == post_id))

    async def upsert_pipeline_state(
        self,
        pipeline_id: str,
        user_id: uuid.UUID,
        state: dict,
    ) -> GeneratedPost:
        result = await self._session.execute(
            select(GeneratedPost).where(
                GeneratedPost.extra_metadata["pipeline_id"].as_string() == pipeline_id,
                GeneratedPost.user_id == user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.extra_metadata = {**(existing.extra_metadata or {}), "pipeline_state": state}
            return existing
        post = GeneratedPost(
            user_id=user_id,
            title=state.get("topic") or "Untitled",
            body="",
            status="running",
            platform="linkedin",
            extra_metadata={"pipeline_id": pipeline_id, "pipeline_state": state},
        )
        self._session.add(post)
        await self._session.flush()
        return post


class AgentRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: AgentRun) -> AgentRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_by_id(self, run_id: uuid.UUID) -> AgentRun | None:
        result = await self._session.execute(
            select(AgentRun).where(AgentRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workflow(self, workflow_id: str) -> list[AgentRun]:
        result = await self._session.execute(
            select(AgentRun)
            .where(AgentRun.workflow_id == workflow_id)
            .order_by(AgentRun.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[AgentRun]:
        result = await self._session.execute(
            select(AgentRun)
            .where(AgentRun.user_id == user_id)
            .order_by(AgentRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        run_id: uuid.UUID,
        status: str,
        error: str | None = None,
    ) -> AgentRun | None:
        values: dict = {"status": status}
        if error is not None:
            values["error"] = error
        await self._session.execute(
            sql_update(AgentRun).where(AgentRun.id == run_id).values(**values)
        )
        return await self.get_by_id(run_id)
