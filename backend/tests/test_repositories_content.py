from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from database import Database
from models.content import AgentRun, GeneratedPost
from models.user import User
from repositories.content import AgentRunRepository, GeneratedPostRepository


@pytest.fixture
async def user_id(db: Database) -> uuid.UUID:
    uid = uuid.uuid4()
    async with db.session() as session:
        user = User(
            id=uid,
            email=f"{uid.hex[:12]}@test.com",
            password_hash="hash",
            display_name="Test",
        )
        session.add(user)
    return uid


@pytest.fixture
async def post_repo(db: Database) -> GeneratedPostRepository:
    async with db.session() as session:
        return GeneratedPostRepository(session)


@pytest.fixture
async def run_repo(db: Database) -> AgentRunRepository:
    async with db.session() as session:
        return AgentRunRepository(session)


class TestGeneratedPostRepository:
    async def test_create(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        post = GeneratedPost(user_id=user_id, title="Test", body="Body")
        created = await post_repo.create(post)
        assert created.id is not None
        assert created.title == "Test"

    async def test_get_by_id(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        post = GeneratedPost(user_id=user_id, title="Title", body="Body")
        created = await post_repo.create(post)
        found = await post_repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    async def test_get_by_id_not_found(self, post_repo: GeneratedPostRepository) -> None:
        assert await post_repo.get_by_id(uuid.uuid4()) is None

    async def test_list_by_user(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        for i in range(3):
            await post_repo.create(GeneratedPost(user_id=user_id, title=f"P{i}", body="B"))
        posts = await post_repo.list_by_user(user_id)
        assert len(posts) == 3

    async def test_list_by_user_paginated(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        for i in range(5):
            await post_repo.create(GeneratedPost(user_id=user_id, title=f"P{i}", body="B"))
        posts = await post_repo.list_by_user(user_id, offset=2, limit=2)
        assert len(posts) == 2

    async def test_list_by_user_platform_filter(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        await post_repo.create(GeneratedPost(user_id=user_id, title="Post1", body="B", platform="linkedin"))
        await post_repo.create(GeneratedPost(user_id=user_id, title="Post2", body="B", platform="twitter"))
        posts = await post_repo.list_by_user(user_id, platform="linkedin")
        assert len(posts) == 1

    async def test_list_by_user_status_filter(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        await post_repo.create(GeneratedPost(user_id=user_id, title="Draft", body="B", status="draft"))
        await post_repo.create(GeneratedPost(user_id=user_id, title="Pub", body="B", status="published"))
        posts = await post_repo.list_by_user(user_id, status="published")
        assert len(posts) == 1

    async def test_count_by_user(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        await post_repo.create(GeneratedPost(user_id=user_id, title="A", body="B"))
        count = await post_repo.count_by_user(user_id)
        assert count == 1

    async def test_update_status(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        post = await post_repo.create(GeneratedPost(user_id=user_id, title="T", body="B"))
        updated = await post_repo.update_status(post.id, "published")
        assert updated is not None
        assert updated.status == "published"

    async def test_delete(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        post = await post_repo.create(GeneratedPost(user_id=user_id, title="T", body="B"))
        await post_repo.delete(post.id)
        assert await post_repo.get_by_id(post.id) is None

    async def test_upsert_pipeline_state_new(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        post = await post_repo.upsert_pipeline_state("pipeline-1", user_id, {"title": "New"})
        assert post.title == "New"

    async def test_upsert_pipeline_state_existing(self, post_repo: GeneratedPostRepository, user_id: uuid.UUID) -> None:
        first = await post_repo.upsert_pipeline_state("pipeline-1", user_id, {"title": "Old"})
        second = await post_repo.upsert_pipeline_state("pipeline-1", user_id, {"title": "Updated"})
        assert second.id == first.id
        assert second.title == "Updated"


class TestAgentRunRepository:
    async def test_create(self, run_repo: AgentRunRepository, user_id: uuid.UUID) -> None:
        run = AgentRun(user_id=user_id, agent_name="test-agent")
        created = await run_repo.create(run)
        assert created.id is not None
        assert created.agent_name == "test-agent"

    async def test_get_by_id(self, run_repo: AgentRunRepository, user_id: uuid.UUID) -> None:
        run = AgentRun(user_id=user_id, agent_name="agent")
        created = await run_repo.create(run)
        found = await run_repo.get_by_id(created.id)
        assert found is not None

    async def test_list_by_workflow(self, run_repo: AgentRunRepository, user_id: uuid.UUID) -> None:
        for i in range(3):
            await run_repo.create(AgentRun(user_id=user_id, agent_name="a", workflow_id="wf-1"))
        runs = await run_repo.list_by_workflow("wf-1")
        assert len(runs) == 3

    async def test_list_by_user(self, run_repo: AgentRunRepository, user_id: uuid.UUID) -> None:
        await run_repo.create(AgentRun(user_id=user_id, agent_name="a"))
        await run_repo.create(AgentRun(user_id=user_id, agent_name="b"))
        runs = await run_repo.list_by_user(user_id)
        assert len(runs) == 2

    async def test_update_status(self, run_repo: AgentRunRepository, user_id: uuid.UUID) -> None:
        run = await run_repo.create(AgentRun(user_id=user_id, agent_name="a"))
        updated = await run_repo.update_status(run.id, "completed")
        assert updated is not None
        assert updated.status == "completed"

    async def test_update_status_with_error(self, run_repo: AgentRunRepository, user_id: uuid.UUID) -> None:
        run = await run_repo.create(AgentRun(user_id=user_id, agent_name="a"))
        updated = await run_repo.update_status(run.id, "failed", error="something broke")
        assert updated is not None
        assert updated.status == "failed"
        assert updated.error == "something broke"
