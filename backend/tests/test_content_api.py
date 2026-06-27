from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from api.deps import get_current_user_id, get_history_service
from services.content_engine.stages.models import ContentIdea
from services.history import HistoryService

TEST_USER_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def _override_content_api_deps():
    from main import app

    history_service = HistoryService()

    overrides = {
        get_current_user_id: lambda: TEST_USER_ID,
        get_history_service: lambda: history_service,
    }
    app.dependency_overrides.update(overrides)
    yield history_service
    for dep in overrides:
        app.dependency_overrides.pop(dep, None)


class TestHistory:
    @pytest.mark.asyncio
    async def test_history_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/content/history")
        assert response.status_code == 200
        data = response.json()
        assert data["records"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_history_with_records(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        await _override_content_api_deps.record_generation(
            user_id=TEST_USER_ID,
            title="Test Post",
            body="Test body content",
            platform="linkedin",
        )

        response = await client.get("/api/v1/content/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["records"][0]["title"] == "Test Post"
        assert data["records"][0]["body"] == "Test body content"
        assert data["records"][0]["platform"] == "linkedin"
        assert data["records"][0]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_history_pagination(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        for i in range(5):
            await _override_content_api_deps.record_generation(
                user_id=TEST_USER_ID,
                title=f"Post {i}",
                body=f"Body {i}",
            )

        response = await client.get(
            "/api/v1/content/history",
            params={"page": 1, "page_size": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_history_platform_filter(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        await _override_content_api_deps.record_generation(
            user_id=TEST_USER_ID,
            title="LinkedIn Post",
            body="Body",
            platform="linkedin",
        )
        await _override_content_api_deps.record_generation(
            user_id=TEST_USER_ID,
            title="Twitter Post",
            body="Body",
            platform="twitter",
        )

        response = await client.get(
            "/api/v1/content/history",
            params={"platform": "linkedin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["records"][0]["platform"] == "linkedin"

    @pytest.mark.asyncio
    async def test_history_user_isolation(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        other_user = uuid.uuid4()
        await _override_content_api_deps.record_generation(
            user_id=other_user,
            title="Other User Post",
            body="Other body",
        )

        response = await client.get("/api/v1/content/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_status_not_found(self, client: AsyncClient) -> None:
        pipeline_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/content/pipeline/{pipeline_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Pipeline not found"

    @pytest.mark.asyncio
    async def test_pipeline_output_not_found(self, client: AsyncClient) -> None:
        pipeline_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/content/pipeline/{pipeline_id}/output",
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Pipeline not found"

    @pytest.mark.asyncio
    async def test_pipeline_status_found(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        pipeline_id = str(uuid.uuid4())
        _override_content_api_deps.store_pipeline_state(
            pipeline_id,
            {
                "pipeline_id": pipeline_id,
                "current_step": "review",
                "requires_human_approval": False,
                "errors": [],
                "draft_output": {"draft": {"body": "Draft body"}},
                "step_timing": {"total_ms": 1500},
            },
        )

        response = await client.get(f"/api/v1/content/pipeline/{pipeline_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == pipeline_id
        assert data["is_complete"] is True
        assert data["current_step"] == "review"
        assert data["errors"] == []

    @pytest.mark.asyncio
    async def test_pipeline_status_with_errors(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        pipeline_id = str(uuid.uuid4())
        _override_content_api_deps.store_pipeline_state(
            pipeline_id,
            {
                "pipeline_id": pipeline_id,
                "current_step": "writing",
                "requires_human_approval": True,
                "errors": ["research"],
                "draft_output": None,
                "step_timing": {"total_ms": 500},
            },
        )

        response = await client.get(f"/api/v1/content/pipeline/{pipeline_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == pipeline_id
        assert data["is_complete"] is False
        assert len(data["errors"]) == 1
        assert data["errors"][0]["step"] == "research"

    @pytest.mark.asyncio
    async def test_pipeline_output_found(
        self,
        client: AsyncClient,
        _override_content_api_deps: HistoryService,
    ) -> None:
        pipeline_id = str(uuid.uuid4())
        _override_content_api_deps.store_pipeline_state(
            pipeline_id,
            {
                "pipeline_id": pipeline_id,
                "current_step": "review",
                "requires_human_approval": False,
                "errors": [],
                "draft_output": {
                    "draft": {
                        "title": "AI Trends",
                        "body": "Content body",
                        "hook": "Did you know?",
                        "call_to_action": "Share now",
                        "hashtags": ["#AI"],
                    },
                },
                "review_output": {"score": 0.85, "feedback": "Great"},
                "strategy_output": {"strategy": {"platform": "linkedin"}},
                "step_timing": {"total_ms": 2000},
            },
        )

        response = await client.get(
            f"/api/v1/content/pipeline/{pipeline_id}/output",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == pipeline_id
        assert data["pipeline_type"] == "content_generation"
        assert data["draft"]["title"] == "AI Trends"
        assert data["draft"]["body"] == "Content body"
        assert data["review"]["score"] == 0.85
        assert data["total_duration_ms"] == 2000


class TestIdeas:
    @pytest.mark.asyncio
    async def test_generate_ideas(
        self,
        client: AsyncClient,
    ) -> None:
        mock_idea = ContentIdea(
            title="The Future of AI in Marketing",
            description="Explore how generative AI is transforming content marketing strategies in 2025.",
            angle="Unique perspective on AI marketing",
            relevance_score=0.92,
        )

        with patch("api.v1.content.ContentEngine") as mock_engine_cls:
            mock_instance = AsyncMock()
            mock_engine_cls.return_value = mock_instance
            mock_instance.generate_ideas = AsyncMock(return_value=[mock_idea])

            response = await client.post(
                "/api/v1/content/ideas",
                json={
                    "topic": "AI Marketing",
                    "platform": "linkedin",
                    "count": 5,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "The Future of AI in Marketing"
        assert data[0]["description"] == (
            "Explore how generative AI is transforming "
            "content marketing strategies in 2025."
        )
        assert data[0]["relevance_score"] == 0.92
        assert data[0]["platform"] == "linkedin"
        assert "id" in data[0]

    @pytest.mark.asyncio
    async def test_generate_ideas_empty_body(
        self,
        client: AsyncClient,
    ) -> None:
        with patch("api.v1.content.ContentEngine") as mock_engine_cls:
            mock_instance = AsyncMock()
            mock_engine_cls.return_value = mock_instance
            mock_instance.generate_ideas = AsyncMock(return_value=[])

            response = await client.post(
                "/api/v1/content/ideas",
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert data == []
