from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from database import Database
from models.knowledge import KnowledgeEntry, KnowledgeTag
from models.user import User
from repositories.knowledge import KnowledgeEntryRepository, KnowledgeTagRepository


@pytest.fixture
async def user_id(db: Database) -> uuid.UUID:
    uid = uuid.uuid4()
    async with db.session() as session:
        session.add(User(id=uid, email=f"{uid.hex[:12]}@test.com", password_hash="h", display_name="T"))
    return uid


@pytest_asyncio.fixture
async def entry_repo(db: Database) -> AsyncGenerator[KnowledgeEntryRepository, None]:
    from sqlalchemy.ext.asyncio import AsyncSession

    session: AsyncSession = db.session_factory()
    try:
        yield KnowledgeEntryRepository(session)
    finally:
        await session.close()


@pytest_asyncio.fixture
async def tag_repo(db: Database) -> AsyncGenerator[KnowledgeTagRepository, None]:
    from sqlalchemy.ext.asyncio import AsyncSession

    session: AsyncSession = db.session_factory()
    try:
        yield KnowledgeTagRepository(session)
    finally:
        await session.close()


@pytest_asyncio.fixture
async def shared_repos(db: Database) -> AsyncGenerator[tuple[KnowledgeEntryRepository, KnowledgeTagRepository], None]:
    from sqlalchemy.ext.asyncio import AsyncSession

    session: AsyncSession = db.session_factory()
    try:
        yield KnowledgeEntryRepository(session), KnowledgeTagRepository(session)
    finally:
        await session.close()


class TestKnowledgeEntryRepository:
    async def test_create(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        entry = KnowledgeEntry(user_id=user_id, source_type="web", source_id="url-1", title="T", content="C")
        created = await entry_repo.create(entry)
        assert created.id is not None
        assert created.title == "T"

    async def test_get_by_id(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        found = await entry_repo.get_by_id(entry.id)
        assert found is not None

    async def test_get_by_id_not_found(self, entry_repo: KnowledgeEntryRepository) -> None:
        assert await entry_repo.get_by_id(uuid.uuid4()) is None

    async def test_list_by_user(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        for i in range(3):
            await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id=f"u{i}", title=f"T{i}", content="C"))
        entries = await entry_repo.list_by_user(user_id)
        assert len(entries) == 3

    async def test_list_by_user_paginated(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        for i in range(5):
            await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id=f"u{i}", title=f"T{i}", content="C"))
        entries = await entry_repo.list_by_user(user_id, offset=1, limit=2)
        assert len(entries) == 2

    async def test_list_by_user_tag_filter(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        e1 = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T1", content="C"))
        e2 = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u2", title="T2", content="C"))
        await tag_repo.set_tags(e1.id, ["ai"])
        entries = await entry_repo.list_by_user(user_id, tag="ai")
        assert len(entries) == 1
        assert entries[0].id == e1.id

    async def test_list_by_user_source_type_filter(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="book", source_id="u2", title="T", content="C"))
        entries = await entry_repo.list_by_user(user_id, source_type="book")
        assert len(entries) == 1

    async def test_count_by_user(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        assert await entry_repo.count_by_user(user_id) == 1

    async def test_update_entry(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="Old", content="C"))
        updated = await entry_repo.update_entry(entry.id, {"title": "New", "relevance_score": 0.9})
        assert updated is not None
        assert updated.title == "New"
        assert updated.relevance_score == 0.9

    async def test_delete_entry(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        await entry_repo.delete_entry(entry.id)
        assert await entry_repo.get_by_id(entry.id) is None

    async def test_search_keyword(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="Machine Learning", content="Deep learning is fun"))
        await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u2", title="Cooking", content="Pasta recipes"))
        results = await entry_repo.search_keyword(user_id, "learning")
        assert len(results) == 1

    async def test_get_recent(self, entry_repo: KnowledgeEntryRepository, user_id: uuid.UUID) -> None:
        for i in range(3):
            await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id=f"u{i}", title=f"T{i}", content="C"))
        recent = await entry_repo.get_recent(user_id)
        assert len(recent) == 3


class TestKnowledgeTagRepository:
    async def test_add_tag(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        tag = KnowledgeTag(entry_id=entry.id, name="test-tag")
        created = await tag_repo.add_tag(tag)
        assert created.id is not None
        assert created.name == "test-tag"

    async def test_remove_tag(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        tag = await tag_repo.add_tag(KnowledgeTag(entry_id=entry.id, name="remove-me"))
        await tag_repo.remove_tag(tag.id)
        tags = await tag_repo.get_tags_for_entry(entry.id)
        assert len(tags) == 0

    async def test_get_tags_for_entry(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        await tag_repo.add_tag(KnowledgeTag(entry_id=entry.id, name="a"))
        await tag_repo.add_tag(KnowledgeTag(entry_id=entry.id, name="b"))
        tags = await tag_repo.get_tags_for_entry(entry.id)
        assert len(tags) == 2

    async def test_get_tags_by_name(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        await tag_repo.add_tag(KnowledgeTag(entry_id=entry.id, name="unique"))
        found = await tag_repo.get_tags_by_name(entry.id, "unique")
        assert found is not None
        assert found.name == "unique"

    async def test_get_distinct_tags(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        e1 = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T1", content="C"))
        e2 = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u2", title="T2", content="C"))
        await tag_repo.set_tags(e1.id, ["ai", "ml"])
        await tag_repo.set_tags(e2.id, ["ai"])
        tags = await tag_repo.get_distinct_tags(user_id)
        tag_map = dict(tags)
        assert tag_map["ai"] == 2
        assert tag_map["ml"] == 1

    async def test_set_tags_replaces(self, shared_repos: tuple[KnowledgeEntryRepository, KnowledgeTagRepository], user_id: uuid.UUID) -> None:
        entry_repo, tag_repo = shared_repos
        entry = await entry_repo.create(KnowledgeEntry(user_id=user_id, source_type="web", source_id="u1", title="T", content="C"))
        await tag_repo.set_tags(entry.id, ["old"])
        await tag_repo.set_tags(entry.id, ["new"])
        tags = await tag_repo.get_tags_for_entry(entry.id)
        assert len(tags) == 1
        assert tags[0].name == "new"


