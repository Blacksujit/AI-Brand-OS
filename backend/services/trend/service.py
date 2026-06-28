from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.logging import get_logger
from database.db import Database
from models.trend import TrendAnalysis, TrendSignal, TrendTopic

logger = get_logger(__name__)
from repositories.trend import (
    TrendAnalysisRepository,
    TrendSignalRepository,
    TrendTopicRepository,
)


class TrendScorer:
    """Scores trend topics based on velocity, relevance, and recency."""

    def __init__(
        self,
        recency_weight: float = 0.5,
        velocity_weight: float = 0.3,
        relevance_weight: float = 0.2,
        half_life_hours: float = 72.0,
    ) -> None:
        self.recency_weight = recency_weight
        self.velocity_weight = velocity_weight
        self.relevance_weight = relevance_weight
        self.half_life_hours = half_life_hours

    def compute_recency_score(self, created_at: datetime | None) -> float:
        """Exponential decay based on age."""
        created_at = _ensure_aware(created_at)
        if created_at is None:
            return 0.0
        age_hours = (_now() - created_at).total_seconds() / 3600
        return math.exp(-age_hours / self.half_life_hours)

    def compute_velocity_score(self, topic: TrendTopic, signals: list[TrendSignal]) -> float:
        """Compute velocity based on signal growth rate."""
        if not signals:
            return 0.0
        _now()
        recent_signals = [
            s for s in signals if s.created_at and (_now() - _ensure_aware(s.created_at)).days <= 7
        ]
        if len(recent_signals) < 2:
            return 0.0
        time_span_hours = (
            max(_ensure_aware(s.created_at) for s in recent_signals)
            - min(_ensure_aware(s.created_at) for s in recent_signals)
        ).total_seconds() / 3600
        if time_span_hours <= 0:
            return 1.0
        rate = len(recent_signals) / max(time_span_hours, 1)
        return min(rate / 10.0, 1.0)

    def compute_relevance_score(self, signals: list[TrendSignal]) -> float:
        """Average relevance of signals in topic."""
        if not signals:
            return 0.0
        return sum(s.relevance_score for s in signals) / len(signals)

    def compute_topic_score(self, topic: TrendTopic, signals: list[TrendSignal]) -> float:
        """Composite score for a topic."""
        recency = self.compute_recency_score(topic.created_at)
        velocity = self.compute_velocity_score(topic, signals)
        relevance = self.compute_relevance_score(signals)
        return (
            self.recency_weight * recency
            + self.velocity_weight * velocity
            + self.relevance_weight * relevance
        )

    def classify_status(self, topic: TrendTopic, signals: list[TrendSignal]) -> str:
        """Classify topic lifecycle status."""
        score = self.compute_topic_score(topic, signals)
        if score >= 0.7:
            return "peaking"
        if score >= 0.4:
            return "trending"
        if score >= 0.2:
            return "emerging"
        return "declining"


class TrendClusterer:
    """Clusters trend signals into topics using TF-IDF + DBSCAN."""

    def __init__(
        self,
        min_signals_per_topic: int = 3,
        similarity_threshold: float = 0.7,
        max_topics: int = 50,
    ) -> None:
        self.min_signals_per_topic = min_signals_per_topic
        self.similarity_threshold = similarity_threshold
        self.max_topics = max_topics

    def _extract_text(self, signal: TrendSignal) -> str:
        parts = [signal.title]
        if signal.summary:
            parts.append(signal.summary)
        if signal.keywords:
            parts.extend(signal.keywords)
        return " ".join(parts)

    def cluster(
        self, signals: list[TrendSignal]
    ) -> tuple[list[TrendTopic], dict[str, list[TrendSignal]]]:
        """Cluster signals into topics. Returns (topics, signal_groups)."""
        if len(signals) < self.min_signals_per_topic:
            return [], {}

        texts = [self._extract_text(s) for s in signals]
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
        )
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
        except ValueError:
            return [], {}

        similarity_matrix = cosine_similarity(tfidf_matrix)
        distance_matrix = np.maximum(1 - similarity_matrix, 0)

        eps = 1 - self.similarity_threshold
        clustering = DBSCAN(
            eps=eps,
            min_samples=self.min_signals_per_topic,
            metric="precomputed",
        ).fit(distance_matrix)

        labels = clustering.labels_
        unique_labels = set(labels) - {-1}

        if len(unique_labels) > self.max_topics:
            label_counts = {l: list(labels).count(l) for l in unique_labels}
            top_labels = sorted(label_counts, key=label_counts.get, reverse=True)[: self.max_topics]
            labels = [l if l in top_labels else -1 for l in labels]
            unique_labels = set(top_labels)

        topics = []
        signal_groups = {}

        for label in unique_labels:
            cluster_signals = [signals[i] for i, l in enumerate(labels) if l == label]
            if len(cluster_signals) < self.min_signals_per_topic:
                continue

            keywords = self._extract_cluster_keywords(cluster_signals, vectorizer)
            centroid = self._compute_centroid(
                cluster_signals, tfidf_matrix, vectorizer, labels == label
            )

            topic_id = uuid4()
            topic = TrendTopic(
                id=topic_id,
                name=f"Topic {label}: {keywords[0] if keywords else 'unnamed'}",
                signal_count=len(cluster_signals),
                keywords=keywords[:10],
                representative_signals=[(s.id or uuid4()).hex for s in cluster_signals[:3]],
                centroid_embedding=centroid,
                status="emerging",
            )
            topics.append(topic)
            signal_groups[topic_id.hex] = cluster_signals

        return topics, signal_groups

    def _extract_cluster_keywords(
        self, signals: list[TrendSignal], vectorizer: TfidfVectorizer
    ) -> list[str]:
        texts = [self._extract_text(s) for s in signals]
        tfidf = vectorizer.transform(texts)
        mean_tfidf = tfidf.mean(axis=0).A1
        feature_names = vectorizer.get_feature_names_out()
        top_indices = mean_tfidf.argsort()[-20:][::-1]
        return [feature_names[i] for i in top_indices if mean_tfidf[i] > 0]

    def _compute_centroid(
        self,
        signals: list[TrendSignal],
        tfidf_matrix,
        vectorizer: TfidfVectorizer,
        mask: np.ndarray,
    ) -> list[float] | None:
        indices = np.where(mask)[0]
        if len(indices) == 0:
            return None
        centroid = tfidf_matrix[indices].mean(axis=0).A1
        return centroid.tolist()


class TrendService:
    """Main service for trend detection, clustering, and analysis."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._scorer = TrendScorer()
        self._clusterer = TrendClusterer()

    async def ingest_signals(self, signals_data: list[dict]) -> dict:
        """Ingest raw trend signals from external sources."""
        created = 0
        updated = 0
        skipped = 0

        async with self._db.session() as session:
            signal_repo = TrendSignalRepository(session)
            for data in signals_data:
                signal = TrendSignal(**data)
                existing = await signal_repo.get_by_source(signal.source_type, signal.source_id)
                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.now(UTC)
                    updated += 1
                else:
                    await signal_repo.add(signal)
                    created += 1
            await session.commit()

        return {"created": created, "updated": updated, "skipped": skipped}

    async def fetch_and_ingest(self, sources: list[dict]) -> dict:
        """Fetch content from URLs and ingest as trend signals."""
        import httpx

        from services.ingestion import _html_to_text

        created = 0
        updated = 0
        skipped = 0

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            for source in sources:
                url = source.get("url", "")
                if not url:
                    skipped += 1
                    continue
                try:
                    response = await client.get(url, headers={"User-Agent": "BrandOS/2.0"})
                    response.raise_for_status()
                    text = _html_to_text(response.text)[:5000]
                    signal_data = {
                        "source_type": source.get("source_type", "web"),
                        "source_id": source.get("source_id", url),
                        "source_url": url,
                        "title": source.get("title", url.rstrip("/").split("/")[-1].replace("-", " ").title()),
                        "summary": text[:500] if text else "",
                        "raw_content": text,
                        "keywords": source.get("keywords", []),
                        "relevance_score": float(source.get("relevance", 0.5)),
                    }
                    result = await self.ingest_signals([signal_data])
                    created += result.get("created", 0)
                    updated += result.get("updated", 0)
                except Exception as exc:
                    logger.warning("fetch_and_ingest_failed", url=url, error=str(exc))
                    skipped += 1

        return {"created": created, "updated": updated, "skipped": skipped}

    async def cluster_trends(
        self,
        min_signals_per_topic: int = 3,
        similarity_threshold: float = 0.7,
        max_topics: int = 50,
        time_window_days: int = 7,
    ) -> dict:
        """Cluster recent signals into trend topics."""
        async with self._db.session() as session:
            signal_repo = TrendSignalRepository(session)
            topic_repo = TrendTopicRepository(session)

            cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=time_window_days)
            signals = await signal_repo.list_recent(limit=500, days=time_window_days)
            signals = [s for s in signals if s.created_at and s.created_at >= cutoff]

            if len(signals) < min_signals_per_topic:
                return {"topics_created": 0, "topics_updated": 0, "signals_clustered": 0}

            self._clusterer = TrendClusterer(
                min_signals_per_topic=min_signals_per_topic,
                similarity_threshold=similarity_threshold,
                max_topics=max_topics,
            )
            topics, signal_groups = self._clusterer.cluster(signals)

            created = 0
            updated = 0
            for topic in topics:
                existing = await topic_repo.get_by_name(topic.name)
                if existing:
                    existing.signal_count = topic.signal_count
                    existing.keywords = topic.keywords
                    existing.representative_signals = topic.representative_signals
                    existing.centroid_embedding = topic.centroid_embedding
                    existing.updated_at = datetime.now(UTC)
                    updated += 1
                else:
                    await topic_repo.add(topic)
                    created += 1
            await session.commit()

        return {
            "topics_created": created,
            "topics_updated": updated,
            "signals_clustered": sum(len(g) for g in signal_groups.values()),
        }

    async def score_trends(
        self,
        topic_ids: list | None = None,
        recency_weight: float = 0.5,
        velocity_weight: float = 0.3,
        relevance_weight: float = 0.2,
    ) -> list[dict]:
        """Score and rank trend topics."""
        async with self._db.session() as session:
            topic_repo = TrendTopicRepository(session)
            signal_repo = TrendSignalRepository(session)

            if topic_ids:
                topics = []
                for tid in topic_ids:
                    try:
                        tid_uuid = UUID(tid) if isinstance(tid, str) else tid
                    except (ValueError, TypeError):
                        continue
                    topic = await topic_repo.get_by_id(tid_uuid)
                    if topic:
                        topics.append(topic)
            else:
                topics = await topic_repo.list_trending(limit=100)

            self._scorer = TrendScorer(
                recency_weight=recency_weight,
                velocity_weight=velocity_weight,
                relevance_weight=relevance_weight,
            )

            results = []
            for topic in topics:
                signals = await signal_repo.list_recent(limit=200, days=30)
                topic_signals = [
                    s for s in signals if s.id.hex in (topic.representative_signals or [])
                ]
                score = self._scorer.compute_topic_score(topic, topic_signals)
                status = self._scorer.classify_status(topic, topic_signals)
                topic.status = status
                topic.velocity = score
                topic.updated_at = datetime.now(UTC)
                results.append(
                    {
                        "topic_id": topic.id.hex,
                        "name": topic.name,
                        "score": score,
                        "status": status,
                        "signal_count": topic.signal_count,
                    }
                )
            await session.commit()

        return sorted(results, key=lambda x: x["score"], reverse=True)

    async def search_trends(
        self,
        query: str,
        limit: int = 20,
        source_type: str | None = None,
        min_relevance: float = 0.0,
    ) -> list[TrendSignal]:
        """Search trend signals by query."""
        async with self._db.session() as session:
            signal_repo = TrendSignalRepository(session)
            signals = await signal_repo.list_recent(limit=500, days=30)
            if source_type:
                signals = [s for s in signals if s.source_type == source_type]
            if min_relevance > 0:
                signals = [s for s in signals if s.relevance_score >= min_relevance]

            query_lower = query.lower()
            matched = [
                s
                for s in signals
                if query_lower in s.title.lower()
                or (s.summary and query_lower in s.summary.lower())
                or (s.keywords and any(query_lower in k.lower() for k in s.keywords))
            ]
            return matched[:limit]

    async def generate_analysis(
        self,
        user_id: str | UUID,
        topic_ids: list[str],
        generated_for: str | None = None,
    ) -> TrendAnalysis:
        """Generate trend analysis for a user."""
        async with self._db.session() as session:
            topic_repo = TrendTopicRepository(session)
            analysis_repo = TrendAnalysisRepository(session)

            topics = []
            for tid in topic_ids:
                try:
                    tid_uuid = UUID(tid) if isinstance(tid, str) else tid
                except (ValueError, TypeError):
                    continue
                topic = await topic_repo.get_by_id(tid_uuid)
                if topic:
                    topics.append(topic)

            if not topics:
                msg = "No valid topics found"
                raise ValueError(msg)

            insights = self._generate_insights(topics)
            recommendations = self._generate_recommendations(topics)
            confidence = self._compute_confidence(topics)

            analysis = TrendAnalysis(
                user_id=user_id,
                topic_ids=topic_ids,
                insights=insights,
                recommendations=recommendations,
                confidence=confidence,
                generated_for=generated_for,
            )
            await analysis_repo.add(analysis)
            await session.commit()
            return analysis

    def _generate_insights(self, topics: list[TrendTopic]) -> str:
        if not topics:
            return "No trends detected."
        top = sorted(topics, key=lambda t: t.velocity, reverse=True)[:5]
        names = [t.name for t in top]
        return (
            f"Top emerging trends: {', '.join(names)}. "
            f"Total {len(topics)} topics tracked. "
            f"Highest velocity: {top[0].name} ({top[0].velocity:.2f})."
        )

    def _generate_recommendations(self, topics: list[TrendTopic]) -> list[str]:
        recs = []
        for topic in sorted(topics, key=lambda t: t.velocity, reverse=True)[:3]:
            if topic.status in ["emerging", "trending"]:
                recs.append(
                    f"Create content around '{topic.name}' (velocity: {topic.velocity:.2f})"
                )
        if not recs:
            recs.append("No high-velocity trends to act on currently.")
        return recs

    def _compute_confidence(self, topics: list[TrendTopic]) -> float:
        if not topics:
            return 0.0
        avg_velocity = sum(t.velocity for t in topics) / len(topics)
        avg_signals = sum(t.signal_count for t in topics) / len(topics)
        return min(0.5 * avg_velocity + 0.3 * min(avg_signals / 10, 1.0) + 0.2, 1.0)

    async def _get_signals_for_listing(
        self,
        limit: int = 50,
        source_type: str | None = None,
        days: int = 30,
    ) -> list[TrendSignal]:
        async with self._db.session() as session:
            signal_repo = TrendSignalRepository(session)
            signals = await signal_repo.list_recent(limit=limit, days=days)
            if source_type:
                signals = [s for s in signals if s.source_type == source_type]
            return signals

    async def get_trending_topics(self, limit: int = 20) -> list[TrendTopic]:
        async with self._db.session() as session:
            topic_repo = TrendTopicRepository(session)
            return await topic_repo.list_trending(limit=limit)

    async def get_topic_details(self, topic_id: str) -> TrendTopic | None:
        async with self._db.session() as session:
            topic_repo = TrendTopicRepository(session)
            try:
                topic_id_uuid = UUID(topic_id) if isinstance(topic_id, str) else topic_id
            except (ValueError, TypeError):
                return None
            return await topic_repo.get_by_id(topic_id_uuid)

    async def get_user_analyses(
        self, user_id: str | UUID, limit: int = 20
    ) -> list[TrendAnalysis]:
        async with self._db.session() as session:
            analysis_repo = TrendAnalysisRepository(session)
            return await analysis_repo.list_by_user(user_id, limit=limit)
