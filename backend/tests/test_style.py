from __future__ import annotations

import pytest

from schemas.style import StyleParams


class TestLexicalAnalyzer:
    def test_basic_extraction(self) -> None:
        from services.style.analyzers import LexicalAnalyzer

        analyzer = LexicalAnalyzer()
        result = analyzer.extract("The quick brown fox jumps over the lazy dog.")
        assert result["word_count"] == 9
        assert result["unique_word_ratio"] == pytest.approx(8 / 9, rel=0.01)
        assert result["avg_word_length"] == pytest.approx(3.89, rel=0.01)

    def test_empty_text(self) -> None:
        from services.style.analyzers import LexicalAnalyzer

        analyzer = LexicalAnalyzer()
        result = analyzer.extract("")
        assert result["word_count"] == 0
        assert result["vocabulary_richness"] == pytest.approx(0.0)

    def test_scoring(self) -> None:
        from services.style.analyzers import LexicalAnalyzer

        analyzer = LexicalAnalyzer()
        params = StyleParams()
        features = {"vocabulary_richness": 5.0}
        score = analyzer.score(features, params)
        assert 0.0 <= score <= 1.0


class TestSyntacticAnalyzer:
    def test_basic_extraction(self) -> None:
        from services.style.analyzers import SyntacticAnalyzer

        analyzer = SyntacticAnalyzer()
        text = "First sentence. Second sentence. Third sentence."
        result = analyzer.extract(text)
        assert result["sentence_count"] == 3
        assert result["avg_sentence_length"] == pytest.approx(2.0, rel=0.01)

    def test_empty_text(self) -> None:
        from services.style.analyzers import SyntacticAnalyzer

        analyzer = SyntacticAnalyzer()
        result = analyzer.extract("")
        assert result["sentence_count"] == 0

    def test_long_sentence_ratio(self) -> None:
        from services.style.analyzers import SyntacticAnalyzer

        analyzer = SyntacticAnalyzer()
        text = "Short. " * 10 + "This is a very long sentence with many many words indeed."
        result = analyzer.extract(text)
        assert 0.0 <= result["long_sentence_ratio"] <= 1.0


class TestTonalAnalyzer:
    def test_formal_text(self) -> None:
        from services.style.analyzers import TonalAnalyzer

        analyzer = TonalAnalyzer()
        text = "Therefore, we must consider the aforementioned data."
        result = analyzer.extract(text)
        assert result["formality_score"] > 0.5

    def test_informal_text(self) -> None:
        from services.style.analyzers import TonalAnalyzer

        analyzer = TonalAnalyzer()
        text = "Hey guys, this is literally awesome stuff!"
        result = analyzer.extract(text)
        assert result["formality_score"] < 0.5

    def test_analogy_detection(self) -> None:
        from services.style.analyzers import TonalAnalyzer

        analyzer = TonalAnalyzer()
        text = "This is like a Swiss Army knife. It reminds me of a simpler time."
        result = analyzer.extract(text)
        assert result["analogy_frequency"] > 0

    def test_humor_detection(self) -> None:
        from services.style.analyzers import TonalAnalyzer

        analyzer = TonalAnalyzer()
        text = "Hot take: this is my unpopular opinion. Just kidding! 😂"
        result = analyzer.extract(text)
        assert result["humor_frequency"] > 0

    def test_scoring(self) -> None:
        from services.style.analyzers import TonalAnalyzer

        analyzer = TonalAnalyzer()
        params = StyleParams(formality=0.8)
        features = {"formality_score": 0.9}
        score = analyzer.score(features, params)
        assert 0.0 <= score <= 1.0


class TestStructuralAnalyzer:
    def test_hook_detection(self) -> None:
        from services.style.analyzers import StructuralAnalyzer

        analyzer = StructuralAnalyzer()
        text = "Here's why everything you know is wrong.\n\nSecond paragraph."
        result = analyzer.extract(text)
        assert result["has_hook"] == 1.0

    def test_cta_detection(self) -> None:
        from services.style.analyzers import StructuralAnalyzer

        analyzer = StructuralAnalyzer()
        text = "Lots of content here.\n\nWhat do you think? Share your thoughts."
        result = analyzer.extract(text)
        assert result["has_cta"] == 1.0

    def test_no_hook_or_cta(self) -> None:
        from services.style.analyzers import StructuralAnalyzer

        analyzer = StructuralAnalyzer()
        text = "Content without any special structure. Just plain text."
        result = analyzer.extract(text)
        assert result["has_hook"] == 0.0
        assert result["has_cta"] == 0.0


class TestStyleAnalyzer:
    def test_analyze(self) -> None:
        from services.style.analyzers import StyleAnalyzer

        analyzer = StyleAnalyzer()
        params = StyleParams()
        text = (
            "Here's why this matters.\n\n"
            "This is a test paragraph with enough content to be meaningful. "
            "It has multiple sentences and should produce reasonable analysis. "
            "The quick brown fox jumps over the lazy dog."
        )
        result = analyzer.analyze(text, params)
        assert "lexical" in result
        assert "syntactic" in result
        assert "tonal" in result
        assert "structural" in result
        assert "overall" in result
        assert 0.0 <= result["overall"] <= 1.0

    def test_extract_signal_data(self) -> None:
        from services.style.analyzers import StyleAnalyzer

        analyzer = StyleAnalyzer()
        text = "This is a sample text for signal extraction."
        result = analyzer.extract_signal_data(text)
        assert result["word_count"] == 8
        assert "vocabulary_richness" in result
        assert "avg_sentence_length" in result
        assert "formality_score" in result


class TestEMASignalProcessor:
    def test_update_ema(self) -> None:
        from services.style.ema_signal import EMASignalProcessor

        processor = EMASignalProcessor(learning_rate=0.5)
        current = {"value": 10.0}
        new = {"value": 20.0}
        result = processor.update_ema(current, new)
        assert result["value"] == pytest.approx(15.0)

    def test_update_ema_single(self) -> None:
        from services.style.ema_signal import EMASignalProcessor

        processor = EMASignalProcessor(learning_rate=0.5)
        result = processor.update_ema_single(10.0, 20.0)
        assert result == pytest.approx(15.0)

    def test_confidence_computation(self) -> None:
        from services.style.ema_signal import EMASignalProcessor

        processor = EMASignalProcessor(learning_rate=0.1)
        c0 = processor.compute_confidence(0)
        c10 = processor.compute_confidence(10)
        c100 = processor.compute_confidence(100)
        assert c0 == pytest.approx(0.0, abs=0.01)
        assert 0.0 < c10 < 1.0
        assert c100 == pytest.approx(1.0, abs=0.01)

    def test_merge_signals(self) -> None:
        from services.style.ema_signal import EMASignalProcessor

        processor = EMASignalProcessor()
        signals = [{"a": 1.0}, {"a": 3.0}]
        result = processor.merge_signals(signals, [0.5, 0.5])
        assert result["a"] == pytest.approx(2.0)

    def test_merge_lists(self) -> None:
        from services.style.ema_signal import EMASignalProcessor

        processor = EMASignalProcessor()
        result = processor.merge_signals(
            [{"list_field": ["a", "b"]}, {"list_field": ["b", "c"]}],
            [0.5, 0.5],
        )
        merged = result.get("list_field", [])
        assert "a" in merged
        assert "b" in merged
        assert "c" in merged


class TestStyleFingerprint:
    def test_compute_fingerprint_empty(self) -> None:
        from services.style.fingerprint import StyleFingerprint

        fp = StyleFingerprint()
        metrics = fp.compute_fingerprint([])
        assert metrics.signal_count == 0

    def test_compute_fingerprint_with_signals(self) -> None:
        from services.style.fingerprint import StyleFingerprint

        fp = StyleFingerprint()
        signals = [
            {
                "vocabulary_richness": 5.0,
                "avg_sentence_length": 20.0,
                "formality_score": 0.7,
                "humor_frequency": 0.2,
                "analogy_frequency": 0.3,
                "unique_word_ratio": 0.6,
                "avg_word_length": 4.5,
                "long_sentence_ratio": 0.1,
                "_timestamp": i,
            }
            for i in range(10)
        ]
        metrics = fp.compute_fingerprint(signals)
        assert metrics.signal_count == 10
        assert metrics.formality_avg == pytest.approx(0.7, abs=0.1)

    def test_is_stable_requirements(self) -> None:
        from services.style.fingerprint import StyleFingerprint

        fp = StyleFingerprint()
        assert fp.is_stable(0, 0.0) is False
        assert fp.is_stable(3, 0.5) is False
        assert fp.is_stable(5, 0.9) is True
        assert fp.is_stable(60, 0.5) is True
        assert fp.is_stable(50, 0.86) is True

    def test_compute_profile_params(self) -> None:
        from services.style.fingerprint import FingerprintMetrics, StyleFingerprint

        fp = StyleFingerprint()
        metrics = FingerprintMetrics(
            lexical_richness_avg=5.0,
            avg_sentence_length_avg=20.0,
            formality_avg=0.7,
            humor_frequency_avg=0.2,
            analogy_frequency_avg=0.3,
            hook_rate=0.5,
            cta_rate=0.3,
            unique_word_ratio_avg=0.6,
            avg_word_length_avg=4.5,
            long_sentence_ratio_avg=0.1,
        )
        params = fp.compute_profile_params(metrics)
        assert params["avg_sentence_length"] == 20.0
        assert params["formality"] == 0.7

    def test_fingerprint_similarity(self) -> None:
        from services.style.fingerprint import StyleFingerprint

        fp = StyleFingerprint()
        a = {"formality": 0.7, "avg_sentence_length": 20.0}
        b = {"formality": 0.7, "avg_sentence_length": 20.0}
        assert fp.fingerprint_similarity(a, b) == pytest.approx(1.0)

    def test_fingerprint_similarity_different(self) -> None:
        from services.style.fingerprint import StyleFingerprint

        fp = StyleFingerprint()
        a = {"formality": 0.1, "avg_sentence_length": 5.0}
        b = {"formality": 0.9, "avg_sentence_length": 40.0}
        similarity = fp.fingerprint_similarity(a, b)
        assert 0.0 <= similarity < 1.0


class TestStyleService:
    @pytest.mark.asyncio
    async def test_get_profile_creates_new(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        result = await service.get_profile(user_id)
        assert result.user_id == str(user_id)
        assert result.confidence == 0.0
        assert result.is_stable is False

    @pytest.mark.asyncio
    async def test_get_profile_returns_existing(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        await service.get_profile(user_id)
        result = await service.get_profile(user_id)
        assert result.user_id == str(user_id)

    @pytest.mark.asyncio
    async def test_analyze_returns_all_scores(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        await service.get_profile(user_id)
        result = await service.analyze(
            user_id,
            "Here's why this matters so much for our industry. "
            "The data clearly shows that we need to adapt. "
            "Therefore, let's consider the evidence.",
        )
        assert "vocabulary_match" in result
        assert "sentence_structure_match" in result
        assert "tone_alignment" in result
        assert "overall_similarity" in result
        assert 0.0 <= result["overall_similarity"] <= 100.0

    @pytest.mark.asyncio
    async def test_import_content_creates_signals(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        posts = [
            "Here's a great post about AI. The technology is amazing.",
            "I think we need to focus on quality. This is important.",
        ]
        result = await service.import_content(user_id, posts)
        assert result["signals_created"] == 2
        assert result["profile_confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_rate_draft_updates_profile(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        draft_id = str(uuid.uuid4())
        profile = await service.rate_draft(
            user_id,
            draft_id,
            4,
            "Great draft!",
        )
        assert profile.total_ratings >= 1
        assert profile.confidence > 0.0

    @pytest.mark.asyncio
    async def test_get_insights_empty(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        result = await service.get_insights(user_id)
        assert result["signals_collected"] == 0
        assert result["is_stable"] is False

    @pytest.mark.asyncio
    async def test_get_learning_progress(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        result = await service.get_learning_progress(user_id)
        assert result["signals_collected"] == 0

    @pytest.mark.asyncio
    async def test_update_profile(self, db) -> None:
        import uuid

        from services.style import StyleService

        service = StyleService(db=db)
        user_id = uuid.uuid4()
        profile = await service.update_profile(user_id, {"learning_rate": 0.2})
        assert profile.learning_rate == 0.2


class TestStyleAPI:
    @pytest.mark.asyncio
    async def test_get_profile(self, client) -> None:
        response = await client.get("/api/v1/style/profile")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "style_params" in data

    @pytest.mark.asyncio
    async def test_update_profile(self, client) -> None:
        response = await client.put(
            "/api/v1/style/profile",
            json={"learning_rate": 0.15},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["learning_rate"] == 0.15

    @pytest.mark.asyncio
    async def test_analyze_text(self, client) -> None:
        response = await client.post(
            "/api/v1/style/analyze",
            json={
                "text": "This is a comprehensive test text for style analysis that exceeds the minimum length requirement of fifty characters by a sufficient margin."
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "vocabulary_match" in data
        assert "overall_similarity" in data

    @pytest.mark.asyncio
    async def test_import_content(self, client) -> None:
        response = await client.post(
            "/api/v1/style/import",
            json={"posts": ["Post one.", "Post two."]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["signals_created"] == 2

    @pytest.mark.asyncio
    async def test_rate_draft(self, client) -> None:
        import uuid

        draft_id = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/style/rate",
            json={
                "draft_id": draft_id,
                "score": 4,
                "comment": "Nice tone",
                "dimension_scores": {
                    "authenticity": 4,
                    "technical_depth": 3,
                    "readability": 5,
                    "relevance": 4,
                    "tone": 4,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_ratings"] >= 1

    @pytest.mark.asyncio
    async def test_get_insights(self, client) -> None:
        response = await client.get("/api/v1/style/insights")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_progress(self, client) -> None:
        response = await client.get("/api/v1/style/progress")
        assert response.status_code == 200
