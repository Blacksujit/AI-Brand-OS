from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


class TestTrendScorer:
    def test_recency_score_fresh(self) -> None:
        from services.trend.service import TrendScorer

        scorer = TrendScorer()
        score = scorer.compute_recency_score(datetime.now(UTC))
        assert score == pytest.approx(1.0, rel=0.01)

    def test_recency_score_old(self) -> None:
        from services.trend.service import TrendScorer

        scorer = TrendScorer(half_life_hours=1.0)
        old = datetime.now(UTC) - timedelta(hours=24)
        score = scorer.compute_recency_score(old)
        assert score < 0.01

    def test_velocity_score_no_signals(self) -> None:
        from models.trend import TrendTopic
        from services.trend.service import TrendScorer

        scorer = TrendScorer()
        topic = TrendTopic(name="test", signal_count=0)
        score = scorer.compute_velocity_score(topic, [])
        assert score == 0.0

    def test_classify_peaking(self) -> None:
        from datetime import timedelta

        from models.trend import TrendSignal, TrendTopic
        from services.trend.service import TrendScorer

        scorer = TrendScorer(half_life_hours=72.0)
        now = __import__("datetime").datetime.now(UTC)
        topic = TrendTopic(
            name="test",
            signal_count=10,
            created_at=now,
        )
        signals = [
            TrendSignal(
                source_type="rss",
                source_id=f"sig{i}",
                title=f"signal {i}",
                created_at=now - timedelta(hours=i),
                relevance_score=0.9,
            )
            for i in range(5)
        ]
        status = scorer.classify_status(topic, signals)
        assert status == "peaking"

    def test_classify_declining(self) -> None:
        from models.trend import TrendSignal, TrendTopic
        from services.trend.service import TrendScorer

        scorer = TrendScorer()
        old = __import__("datetime").datetime.now(UTC) - __import__("datetime").timedelta(days=30)
        topic = TrendTopic(
            name="test",
            signal_count=0,
            created_at=old,
        )
        signals = [
            TrendSignal(
                source_type="rss",
                source_id="old",
                title="old signal",
                created_at=old,
                relevance_score=0.1,
            )
        ]
        status = scorer.classify_status(topic, signals)
        assert status == "declining"

    def test_compute_relevance_score_empty(self) -> None:
        from services.trend.service import TrendScorer

        scorer = TrendScorer()
        assert scorer.compute_relevance_score([]) == 0.0


class TestTrendClusterer:
    def test_cluster_insufficient_signals(self) -> None:
        from services.trend.service import TrendClusterer

        clusterer = TrendClusterer(min_signals_per_topic=5)
        topics, groups = clusterer.cluster([])
        assert topics == []
        assert groups == {}

    def test_cluster_similar_signals(self) -> None:
        from models.trend import TrendSignal
        from services.trend.service import TrendClusterer

        clusterer = TrendClusterer(
            min_signals_per_topic=2,
            similarity_threshold=0.3,
        )
        signals = [
            TrendSignal(
                source_type="rss",
                source_id=f"id{i}",
                title=f"AI and machine learning topic {i}",
                summary="deep learning artificial intelligence trends",
                keywords=["ai", "ml", "deep learning"],
                relevance_score=0.8,
            )
            for i in range(5)
        ]
        topics, _groups = clusterer.cluster(signals)
        assert len(topics) >= 1

    def test_cluster_diverse_signals(self) -> None:
        from models.trend import TrendSignal
        from services.trend.service import TrendClusterer

        clusterer = TrendClusterer(
            min_signals_per_topic=2,
            similarity_threshold=0.8,
        )
        topics = [
            "AI and machine learning are transforming the industry",
            "The weather today is sunny and warm in California",
            "Quantum computing breakthroughs in particle physics",
            "Sports team wins championship after overtime victory",
            "Deep learning models achieve state of the art results",
        ]
        signals = [
            TrendSignal(
                source_type="rss",
                source_id=f"id{i}",
                title=title,
                keywords=[],
                relevance_score=0.5,
            )
            for i, title in enumerate(topics)
        ]
        result_topics, groups = clusterer.cluster(signals)
        assert isinstance(result_topics, list)
        assert isinstance(groups, dict)

    def test_extract_text_with_all_fields(self) -> None:
        from models.trend import TrendSignal
        from services.trend.service import TrendClusterer

        clusterer = TrendClusterer()
        signal = TrendSignal(
            source_type="rss",
            source_id="test",
            title="Test Title",
            summary="Test summary",
            keywords=["key1", "key2"],
            relevance_score=0.5,
        )
        text = clusterer._extract_text(signal)
        assert "Test Title" in text
        assert "Test summary" in text
        assert "key1" in text

    def test_extract_text_minimal(self) -> None:
        from models.trend import TrendSignal
        from services.trend.service import TrendClusterer

        clusterer = TrendClusterer()
        signal = TrendSignal(
            source_type="rss",
            source_id="test",
            title="Only Title",
            relevance_score=0.0,
        )
        text = clusterer._extract_text(signal)
        assert text == "Only Title"

    def test_extract_cluster_keywords(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        from models.trend import TrendSignal
        from services.trend.service import TrendClusterer

        clusterer = TrendClusterer()
        vectorizer = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
        signals = [
            TrendSignal(
                source_type="rss",
                source_id=f"id{i}",
                title=f"AI trends in machine learning {i}",
                relevance_score=0.5,
            )
            for i in range(3)
        ]
        _ = vectorizer.fit_transform([clusterer._extract_text(s) for s in signals])
        keywords = clusterer._extract_cluster_keywords(signals, vectorizer)
        assert isinstance(keywords, list)
        assert any(len(kw) > 0 for kw in keywords)


class TestTrendService:
    @pytest.mark.asyncio
    async def test_ingest_signals(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": "test-1",
                "title": "AI trends in 2026",
                "summary": "Summary about AI",
                "keywords": ["ai", "trends"],
                "relevance_score": 0.8,
            },
            {
                "source_type": "rss",
                "source_id": "test-2",
                "title": "Machine learning advances",
                "summary": "Summary about ML",
                "keywords": ["ml", "advances"],
                "relevance_score": 0.7,
            },
        ]
        result = await service.ingest_signals(signals_data)
        assert result["created"] == 2
        assert result["updated"] == 0
        assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_ingest_duplicate(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signal = {
            "source_type": "rss",
            "source_id": "dup-1",
            "title": "Original",
            "relevance_score": 0.5,
        }
        await service.ingest_signals([signal])
        signal["title"] = "Updated"
        result = await service.ingest_signals([signal])
        assert result["updated"] == 1
        assert result["created"] == 0

    @pytest.mark.asyncio
    async def test_cluster_trends(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": f"cluster-{i}",
                "title": f"AI and deep learning trends in technology {i}",
                "summary": "artificial intelligence machine learning",
                "keywords": ["ai", "ml", "deep learning"],
                "relevance_score": 0.8,
            }
            for i in range(5)
        ]
        await service.ingest_signals(signals_data)
        result = await service.cluster_trends(
            min_signals_per_topic=2,
            similarity_threshold=0.3,
            time_window_days=7,
        )
        assert result["topics_created"] >= 1

    @pytest.mark.asyncio
    async def test_score_trends(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": f"score-{i}",
                "title": f"Trending topic in AI {i}",
                "summary": "emerging technology trends",
                "keywords": ["ai", f"topic{i}"],
                "relevance_score": 0.7,
            }
            for i in range(5)
        ]
        await service.ingest_signals(signals_data)
        await service.cluster_trends(
            min_signals_per_topic=2,
            similarity_threshold=0.3,
            time_window_days=7,
        )
        results = await service.score_trends()
        assert len(results) >= 1
        assert "topic_id" in results[0]
        assert "score" in results[0]
        assert "status" in results[0]

    @pytest.mark.asyncio
    async def test_search_trends(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": f"search-{i}",
                "title": "AI and machine learning",
                "keywords": ["ai", "ml"],
                "relevance_score": 0.9,
            }
            for i in range(3)
        ]
        signals_data.append(
            {
                "source_type": "news",
                "source_id": "search-other",
                "title": "Weather report",
                "keywords": ["weather"],
                "relevance_score": 0.1,
            }
        )
        await service.ingest_signals(signals_data)
        results = await service.search_trends(query="AI", source_type="rss", min_relevance=0.5)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_trends_no_match(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        results = await service.search_trends(query="nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_generate_analysis(self, db) -> None:
        import uuid

        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": f"analysis-{i}",
                "title": f"Analysis topic AI {i}",
                "summary": "machine learning deep learning",
                "keywords": ["ai"],
                "relevance_score": 0.8,
            }
            for i in range(5)
        ]
        await service.ingest_signals(signals_data)
        await service.cluster_trends(
            min_signals_per_topic=2,
            similarity_threshold=0.3,
            time_window_days=7,
        )
        topics = await service.get_trending_topics(limit=10)
        assert len(topics) > 0

        topic_ids = [t.id.hex for t in topics[:2]]
        analysis = await service.generate_analysis(
            user_id=uuid.uuid4(),
            topic_ids=topic_ids,
            generated_for="weekly-brief",
        )
        assert analysis.id is not None
        assert len(analysis.insights) > 0
        assert analysis.confidence > 0.0

    @pytest.mark.asyncio
    async def test_generate_analysis_no_topics(self, db) -> None:
        import uuid

        from services.trend import TrendService

        service = TrendService(db=db)
        user_id = uuid.uuid4()
        with pytest.raises(ValueError, match="No valid topics found"):
            await service.generate_analysis(
                user_id=user_id,
                topic_ids=["nonexistent"],
            )

    @pytest.mark.asyncio
    async def test_get_trending_topics_empty(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        topics = await service.get_trending_topics()
        assert topics == []

    @pytest.mark.asyncio
    async def test_get_topic_details_not_found(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        topic = await service.get_topic_details("nonexistent")
        assert topic is None

    @pytest.mark.asyncio
    async def test_get_user_analyses_empty(self, db) -> None:
        import uuid

        from services.trend import TrendService

        service = TrendService(db=db)
        user_id = uuid.uuid4()
        analyses = await service.get_user_analyses(user_id=user_id)
        assert analyses == []

    @pytest.mark.asyncio
    async def test_get_signals_for_listing(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": f"listing-{i}",
                "title": f"Signal {i}",
                "relevance_score": 0.5,
            }
            for i in range(3)
        ]
        await service.ingest_signals(signals_data)
        signals = await service._get_signals_for_listing(limit=10, source_type="rss", days=30)
        assert len(signals) == 3

    @pytest.mark.asyncio
    async def test_fetch_and_ingest(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        result = await service.fetch_and_ingest([])
        assert result == {"created": 0, "updated": 0, "skipped": 0}

    @pytest.mark.asyncio
    async def test_trending_topics_after_cluster(self, db) -> None:
        from services.trend import TrendService

        service = TrendService(db=db)
        signals_data = [
            {
                "source_type": "rss",
                "source_id": f"trend-{i}",
                "title": f"Trending topic in tech {i}",
                "relevance_score": 0.6,
            }
            for i in range(5)
        ]
        await service.ingest_signals(signals_data)
        await service.cluster_trends(
            min_signals_per_topic=2,
            similarity_threshold=0.3,
            time_window_days=7,
        )
        topics = await service.get_trending_topics(limit=10)
        assert len(topics) >= 1
        for t in topics:
            assert t.name is not None


class TestTrendAPI:
    @pytest.mark.asyncio
    async def test_ingest_signals(self, client) -> None:
        response = await client.post(
            "/api/v1/trends/signals/ingest",
            json={
                "signals": [
                    {
                        "source_type": "rss",
                        "source_id": "api-test-1",
                        "title": "API test signal",
                        "summary": "Testing the API",
                        "keywords": ["test", "api"],
                        "relevance_score": 0.7,
                    },
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 1
        assert data["updated"] == 0

    @pytest.mark.asyncio
    async def test_list_signals_empty(self, client) -> None:
        response = await client.get("/api/v1/trends/signals")
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_topics_empty(self, client) -> None:
        response = await client.get("/api/v1/trends/topics")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_topic_not_found(self, client) -> None:
        response = await client.get("/api/v1/trends/topics/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_analyze_no_topics(self, client, auth_headers) -> None:
        response = await client.post(
            "/api/v1/trends/analyze",
            json={
                "topic_ids": [
                    "00000000-0000-0000-0000-000000000002",
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_cluster_empty(self, client) -> None:
        response = await client.post(
            "/api/v1/trends/cluster",
            json={
                "min_signals_per_topic": 3,
                "similarity_threshold": 0.7,
                "max_topics": 50,
                "time_window_days": 7,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["topics_created"] == 0

    @pytest.mark.asyncio
    async def test_score_empty(self, client) -> None:
        response = await client.post(
            "/api/v1/trends/score",
            json={},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_search_no_results(self, client) -> None:
        response = await client.post(
            "/api/v1/trends/search",
            json={"query": "nonexistent"},
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_analyses_empty(self, client, auth_headers) -> None:
        response = await client.get("/api/v1/trends/analyses", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_ingest_cluster_score_analyze_flow(self, client, auth_headers) -> None:
        signals = [
            {
                "source_type": "rss",
                "source_id": f"flow-{i}",
                "title": f"Flow test topic for AI trends {i}",
                "summary": "machine learning deep learning artificial intelligence",
                "keywords": ["ai", "ml", f"topic{i}"],
                "relevance_score": 0.9,
            }
            for i in range(5)
        ]
        resp = await client.post(
            "/api/v1/trends/signals/ingest",
            json={"signals": signals},
        )
        assert resp.status_code == 200

        resp = await client.post(
            "/api/v1/trends/cluster",
            json={
                "min_signals_per_topic": 2,
                "similarity_threshold": 0.3,
                "time_window_days": 7,
            },
        )
        assert resp.status_code == 200
        cluster_data = resp.json()
        assert cluster_data["topics_created"] >= 1

        resp = await client.post("/api/v1/trends/score", json={})
        assert resp.status_code == 200
        scores = resp.json()
        assert len(scores) >= 1

        resp = await client.get("/api/v1/trends/topics")
        assert resp.status_code == 200
        topics_data = resp.json()
        assert topics_data["total"] >= 1
        topic_id = topics_data["topics"][0]["id"]

        resp = await client.get(f"/api/v1/trends/topics/{topic_id}")
        assert resp.status_code == 200
        topic = resp.json()
        assert topic["name"] is not None

        resp = await client.patch(
            f"/api/v1/trends/topics/{topic_id}",
            json={"status": "peaking"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "peaking"

        resp = await client.post(
            "/api/v1/trends/analyze",
            json={
                "topic_ids": [topic_id],
                "generated_for": "test-flow",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        analysis = resp.json()
        assert analysis["id"] is not None
        assert len(analysis["insights"]) > 0

        resp = await client.get("/api/v1/trends/analyses", headers=auth_headers)
        assert resp.status_code == 200
        analyses = resp.json()
        assert len(analyses) >= 1
