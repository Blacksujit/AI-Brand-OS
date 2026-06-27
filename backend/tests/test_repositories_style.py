from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from database import Database
from models.style import StyleProfile, StyleRating, StyleSignal
from models.user import User
from repositories.style import StyleProfileRepository, StyleRatingRepository, StyleSignalRepository


@pytest.fixture
async def user_id(db: Database) -> uuid.UUID:
    uid = uuid.uuid4()
    async with db.session() as session:
        session.add(User(id=uid, email=f"{uid.hex[:12]}@test.com", password_hash="h", display_name="T"))
    return uid


@pytest_asyncio.fixture
async def profile_repo(db: Database) -> AsyncGenerator[StyleProfileRepository, None]:
    from sqlalchemy.ext.asyncio import AsyncSession
    session: AsyncSession = db.session_factory()
    try:
        yield StyleProfileRepository(session)
    finally:
        await session.close()


@pytest_asyncio.fixture
async def signal_repo(db: Database) -> AsyncGenerator[StyleSignalRepository, None]:
    from sqlalchemy.ext.asyncio import AsyncSession
    session: AsyncSession = db.session_factory()
    try:
        yield StyleSignalRepository(session)
    finally:
        await session.close()


@pytest_asyncio.fixture
async def rating_repo(db: Database) -> AsyncGenerator[StyleRatingRepository, None]:
    from sqlalchemy.ext.asyncio import AsyncSession
    session: AsyncSession = db.session_factory()
    try:
        yield StyleRatingRepository(session)
    finally:
        await session.close()


@pytest_asyncio.fixture
async def style_profile(profile_repo: StyleProfileRepository, user_id: uuid.UUID) -> StyleProfile:
    sp = await profile_repo.create(StyleProfile(user_id=user_id))
    return sp


@pytest_asyncio.fixture
async def signal_repos_for_profile(db: Database, user_id: uuid.UUID) -> AsyncGenerator[tuple[StyleProfileRepository, StyleSignalRepository, StyleProfile], None]:
    from sqlalchemy.ext.asyncio import AsyncSession
    session: AsyncSession = db.session_factory()
    try:
        p_repo = StyleProfileRepository(session)
        s_repo = StyleSignalRepository(session)
        profile = await p_repo.create(StyleProfile(user_id=user_id))
        yield p_repo, s_repo, profile
    finally:
        await session.close()


class TestStyleProfileRepository:
    async def test_create(self, profile_repo: StyleProfileRepository, user_id: uuid.UUID) -> None:
        sp = await profile_repo.create(StyleProfile(user_id=user_id))
        assert sp.id is not None
        assert sp.user_id == user_id

    async def test_get_by_user_id(self, profile_repo: StyleProfileRepository, user_id: uuid.UUID) -> None:
        await profile_repo.create(StyleProfile(user_id=user_id))
        found = await profile_repo.get_by_user_id(user_id)
        assert found is not None

    async def test_get_by_user_id_not_found(self, profile_repo: StyleProfileRepository) -> None:
        assert await profile_repo.get_by_user_id(uuid.uuid4()) is None

    async def test_update(self, profile_repo: StyleProfileRepository, style_profile: StyleProfile) -> None:
        updated = await profile_repo.update(style_profile.id, {"confidence": 0.95, "learning_rate": 0.05})
        assert updated is not None
        assert updated.confidence == 0.95
        assert updated.learning_rate == 0.05

    async def test_upsert_by_user_id_insert(self, profile_repo: StyleProfileRepository, user_id: uuid.UUID) -> None:
        sp = await profile_repo.upsert_by_user_id(user_id, {"confidence": 0.5})
        assert sp.user_id == user_id
        assert sp.confidence == 0.5

    async def test_upsert_by_user_id_update(self, profile_repo: StyleProfileRepository, style_profile: StyleProfile) -> None:
        sp = await profile_repo.upsert_by_user_id(style_profile.user_id, {"confidence": 0.99})
        assert sp.id == style_profile.id
        assert sp.confidence == 0.99


class TestStyleSignalRepository:
    async def test_add(self, signal_repos_for_profile: tuple[StyleProfileRepository, StyleSignalRepository, StyleProfile]) -> None:
        _, signal_repo, profile = signal_repos_for_profile
        signal = StyleSignal(profile_id=profile.id, signal_type="edit", weight=1.0)
        created = await signal_repo.add(signal)
        assert created.id is not None
        assert created.signal_type == "edit"

    async def test_count_by_profile(self, signal_repos_for_profile: tuple[StyleProfileRepository, StyleSignalRepository, StyleProfile]) -> None:
        _, signal_repo, profile = signal_repos_for_profile
        for _ in range(3):
            await signal_repo.add(StyleSignal(profile_id=profile.id, signal_type="edit", weight=1.0))
        count = await signal_repo.count_by_profile(profile.id)
        assert count == 3

    async def test_count_by_profile_filtered(self, signal_repos_for_profile: tuple[StyleProfileRepository, StyleSignalRepository, StyleProfile]) -> None:
        _, signal_repo, profile = signal_repos_for_profile
        await signal_repo.add(StyleSignal(profile_id=profile.id, signal_type="edit", weight=1.0))
        await signal_repo.add(StyleSignal(profile_id=profile.id, signal_type="approve", weight=1.0))
        count = await signal_repo.count_by_profile(profile.id, signal_type="edit")
        assert count == 1

    async def test_list_recent(self, signal_repos_for_profile: tuple[StyleProfileRepository, StyleSignalRepository, StyleProfile]) -> None:
        _, signal_repo, profile = signal_repos_for_profile
        for i in range(5):
            await signal_repo.add(StyleSignal(profile_id=profile.id, signal_type=f"type{i}", weight=1.0))
        signals = await signal_repo.list_recent(profile.id, limit=3)
        assert len(signals) == 3


class TestStyleRatingRepository:
    async def test_add(self, rating_repo: StyleRatingRepository, user_id: uuid.UUID) -> None:
        rating = StyleRating(user_id=user_id, draft_id="draft-1", score=8)
        created = await rating_repo.add(rating)
        assert created.id is not None
        assert created.score == 8

    async def test_get_by_user_and_draft(self, rating_repo: StyleRatingRepository, user_id: uuid.UUID) -> None:
        await rating_repo.add(StyleRating(user_id=user_id, draft_id="draft-1", score=7))
        found = await rating_repo.get_by_user_and_draft(user_id, "draft-1")
        assert found is not None
        assert found.score == 7

    async def test_get_by_user_and_draft_not_found(self, rating_repo: StyleRatingRepository, user_id: uuid.UUID) -> None:
        assert await rating_repo.get_by_user_and_draft(user_id, "nonexistent") is None

    async def test_count_by_user(self, rating_repo: StyleRatingRepository, user_id: uuid.UUID) -> None:
        await rating_repo.add(StyleRating(user_id=user_id, draft_id="d1", score=5))
        await rating_repo.add(StyleRating(user_id=user_id, draft_id="d2", score=6))
        assert await rating_repo.count_by_user(user_id) == 2

    async def test_list_recent(self, rating_repo: StyleRatingRepository, user_id: uuid.UUID) -> None:
        for i in range(4):
            await rating_repo.add(StyleRating(user_id=user_id, draft_id=f"d{i}", score=5))
        ratings = await rating_repo.list_recent(user_id, limit=2)
        assert len(ratings) == 2
