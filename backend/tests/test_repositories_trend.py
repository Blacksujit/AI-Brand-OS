from __future__ import annotations

import uuid

import pytest

from database import Database
from models.trend import TrendAnalysis, TrendSignal, TrendTopic
from models.user import User
from repositories.trend import TrendAnalysisRepository, TrendSignalRepository, TrendTopicRepository


@pytest.fixture
async def user_id(db: Database) -> uuid.UUID:
    uid = uuid.uuid4()
    async with db.session() as session:
        session.add(User(id=uid, email=f"{uid.hex[:12]}@test.com", password_hash="h", display_name="T"))
    return uid


@pytest.fixture
async def signal_repo(db: Database) -> TrendSignalRepository:
    async with db.session() as session:
        return TrendSignalRepository(session)


@pytest.fixture
async def topic_repo(db: Database) -> TrendTopicRepository:
    async with db.session() as session:
        return TrendTopicRepository(session)


@pytest.fixture
async def analysis_repo(db: Database) -> TrendAnalysisRepository:
    async with db.session() as session:
        return TrendAnalysisRepository(session)


class TestTrendSignalRepository:
    async def test_add(self, signal_repo: TrendSignalRepository) -> None:
        signal = TrendSignal(source_type="twitter", source_id="tweet-1", title="AI trends", relevance_score=0.9)
        created = await signal_repo.add(signal)
        assert created.id is not None
        assert created.title == "AI trends"

    async def test_get_by_id(self, signal_repo: TrendSignalRepository) -> None:
        signal = await signal_repo.add(TrendSignal(source_type="twitter", source_id="t1", title="T", relevance_score=0.5))
        found = await signal_repo.get_by_id(signal.id)
        assert found is not None

    async def test_get_by_source(self, signal_repo: TrendSignalRepository) -> None:
        await signal_repo.add(TrendSignal(source_type="twitter", source_id="t1", title="T", relevance_score=0.5))
        found = await signal_repo.get_by_source("twitter", "t1")
        assert found is not None

    async def test_upsert_insert(self, signal_repo: TrendSignalRepository) -> None:
        signal = TrendSignal(source_type="twitter", source_id="new", title="New signal", relevance_score=0.8)
        created = await signal_repo.upsert(signal)
        assert created.title == "New signal"

    async def test_upsert_update(self, signal_repo: TrendSignalRepository) -> None:
        signal = TrendSignal(source_type="twitter", source_id="existing", title="Original", relevance_score=0.3)
        await signal_repo.upsert(signal)
        signal.relevance_score = 0.9
        updated = await signal_repo.upsert(signal)
        assert updated.relevance_score == 0.9

    async def test_list_recent(self, signal_repo: TrendSignalRepository) -> None:
        for i in range(3):
            await signal_repo.add(TrendSignal(source_type="twitter", source_id=f"t{i}", title=f"T{i}", relevance_score=0.5))
        signals = await signal_repo.list_recent(limit=10)
        assert len(signals) == 3

    async def test_list_recent_filter_source_type(self, signal_repo: TrendSignalRepository) -> None:
        await signal_repo.add(TrendSignal(source_type="twitter", source_id="t1", title="Twitter post", relevance_score=0.5))
        await signal_repo.add(TrendSignal(source_type="news", source_id="n1", title="News article", relevance_score=0.6))
        signals = await signal_repo.list_recent(source_type="news")
        assert len(signals) == 1

    async def test_list_by_relevance(self, signal_repo: TrendSignalRepository) -> None:
        await signal_repo.add(TrendSignal(source_type="twitter", source_id="t1", title="Low", relevance_score=0.2))
        await signal_repo.add(TrendSignal(source_type="twitter", source_id="t2", title="High", relevance_score=0.9))
        results = await signal_repo.list_by_relevance(min_score=0.5)
        assert len(results) == 1
        assert results[0].title == "High"

    async def test_count_recent(self, signal_repo: TrendSignalRepository) -> None:
        await signal_repo.add(TrendSignal(source_type="twitter", source_id="t1", title="T", relevance_score=0.5))
        assert await signal_repo.count_recent(days=30) == 1


class TestTrendTopicRepository:
    async def test_add(self, topic_repo: TrendTopicRepository) -> None:
        topic = TrendTopic(name="AI")
        created = await topic_repo.add(topic)
        assert created.id is not None
        assert created.name == "AI"

    async def test_get_by_id(self, topic_repo: TrendTopicRepository) -> None:
        topic = await topic_repo.add(TrendTopic(name="ML"))
        found = await topic_repo.get_by_id(topic.id)
        assert found is not None

    async def test_get_by_name(self, topic_repo: TrendTopicRepository) -> None:
        await topic_repo.add(TrendTopic(name="AI"))
        found = await topic_repo.get_by_name("AI")
        assert found is not None

    async def test_list_by_status(self, topic_repo: TrendTopicRepository) -> None:
        await topic_repo.add(TrendTopic(name="A", status="emerging", velocity=1.0))
        await topic_repo.add(TrendTopic(name="B", status="emerging", velocity=5.0))
        await topic_repo.add(TrendTopic(name="C", status="declining"))
        topics = await topic_repo.list_by_status("emerging")
        assert len(topics) == 2
        assert topics[0].velocity >= topics[1].velocity

    async def test_list_trending(self, topic_repo: TrendTopicRepository) -> None:
        await topic_repo.add(TrendTopic(name="A", status="emerging"))
        await topic_repo.add(TrendTopic(name="B", status="trending"))
        await topic_repo.add(TrendTopic(name="C", status="declining"))
        topics = await topic_repo.list_trending()
        assert len(topics) == 2

    async def test_update_velocity(self, topic_repo: TrendTopicRepository) -> None:
        topic = await topic_repo.add(TrendTopic(name="T"))
        await topic_repo.update_velocity(topic.id, 0.85)
        found = await topic_repo.get_by_id(topic.id)
        assert found is not None
        assert found.velocity == 0.85

    async def test_update_status(self, topic_repo: TrendTopicRepository) -> None:
        topic = await topic_repo.add(TrendTopic(name="T"))
        await topic_repo.update_status(topic.id, "peaking")
        found = await topic_repo.get_by_id(topic.id)
        assert found is not None
        assert found.status == "peaking"


class TestTrendAnalysisRepository:
    async def test_create(self, analysis_repo: TrendAnalysisRepository, user_id: uuid.UUID) -> None:
        analysis = TrendAnalysis(user_id=user_id, topic_ids=["t1"], insights="Interesting trends")
        created = await analysis_repo.add(analysis)
        assert created.id is not None
        assert created.insights == "Interesting trends"

    async def test_get_by_id(self, analysis_repo: TrendAnalysisRepository, user_id: uuid.UUID) -> None:
        analysis = await analysis_repo.add(TrendAnalysis(user_id=user_id, topic_ids=["t1"], insights="I"))
        found = await analysis_repo.get_by_id(analysis.id)
        assert found is not None

    async def test_list_by_user(self, analysis_repo: TrendAnalysisRepository, user_id: uuid.UUID) -> None:
        for i in range(3):
            await analysis_repo.add(TrendAnalysis(user_id=user_id, topic_ids=["t1"], insights=f"Insight {i}"))
        analyses = await analysis_repo.list_by_user(user_id)
        assert len(analyses) == 3

    async def test_count_by_user(self, analysis_repo: TrendAnalysisRepository, user_id: uuid.UUID) -> None:
        await analysis_repo.add(TrendAnalysis(user_id=user_id, topic_ids=["t1"], insights="I"))
        assert await analysis_repo.count_by_user(user_id) == 1
