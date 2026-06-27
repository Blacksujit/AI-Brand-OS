from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.deps import get_knowledge_service
from core.chroma import ChromaService
from core.embedding import EmbeddingService
from database.db import Database
from models.knowledge import KnowledgeEntry
from repositories.knowledge import KnowledgeEntryRepository, KnowledgeTagRepository
from schemas.knowledge import (
    AddKnowledgeEntryRequest,
    UpdateKnowledgeEntryRequest,
)
from services.knowledge import KnowledgeBaseService


@pytest.fixture
def mock_chroma() -> ChromaService:
    chroma = MagicMock(spec=ChromaService)
    chroma._client = None
    chroma.initialize = AsyncMock(return_value=False)
    return chroma


@pytest.fixture
def mock_embedding() -> EmbeddingService:
    embed = MagicMock(spec=EmbeddingService)
    embed.embed_text = AsyncMock(return_value=[0.1] * 384)
    embed.dimension = 384
    return embed


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture(name="kb_service")
async def fixture_kb_service(
    db: Database,
    mock_chroma: ChromaService,
    mock_embedding: EmbeddingService,
) -> KnowledgeBaseService:
    return KnowledgeBaseService(db=db, chroma=mock_chroma, embedding=mock_embedding)


class TestKnowledgeBaseService:
    async def test_add_entry(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Test Entry",
            content="This is test content for the knowledge base.",
            source_type="manual",
            tags=["test", "pytest"],
        )
        entry = await kb_service.add_entry(user_id, request)
        assert entry.title == "Test Entry"
        assert entry.content == "This is test content for the knowledge base."
        assert entry.source_type == "manual"
        assert entry.user_id == user_id

    async def test_get_entry(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Get Test",
            content="Content for get test.",
            tags=[],
        )
        created = await kb_service.add_entry(user_id, request)
        fetched = await kb_service.get_entry(user_id, created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "Get Test"

    async def test_get_entry_wrong_user(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Wrong User",
            content="Should not be visible.",
            tags=[],
        )
        created = await kb_service.add_entry(user_id, request)
        other_user = uuid.uuid4()
        fetched = await kb_service.get_entry(other_user, created.id)
        assert fetched is None

    async def test_get_entry_not_found(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        fetched = await kb_service.get_entry(user_id, uuid.uuid4())
        assert fetched is None

    async def test_update_entry(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Original Title",
            content="Original content.",
            tags=["original"],
        )
        created = await kb_service.add_entry(user_id, request)

        update = UpdateKnowledgeEntryRequest(title="Updated Title", tags=["updated"])
        updated = await kb_service.update_entry(user_id, created.id, update)
        assert updated is not None
        assert updated.title == "Updated Title"

    async def test_update_entry_wrong_user(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Not Mine",
            content="Content.",
            tags=[],
        )
        created = await kb_service.add_entry(user_id, request)
        result = await kb_service.update_entry(uuid.uuid4(), created.id, UpdateKnowledgeEntryRequest())
        assert result is None

    async def test_delete_entry(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Delete Me",
            content="To be deleted.",
            tags=[],
        )
        created = await kb_service.add_entry(user_id, request)
        deleted = await kb_service.delete_entry(user_id, created.id)
        assert deleted is True
        fetched = await kb_service.get_entry(user_id, created.id)
        assert fetched is None

    async def test_delete_entry_wrong_user(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        request = AddKnowledgeEntryRequest(
            title="Not Mine",
            content="Content.",
            tags=[],
        )
        created = await kb_service.add_entry(user_id, request)
        result = await kb_service.delete_entry(uuid.uuid4(), created.id)
        assert result is False

    async def test_list_entries(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        for i in range(3):
            request = AddKnowledgeEntryRequest(
                title=f"Entry {i}",
                content=f"Content {i}.",
                tags=[],
            )
            await kb_service.add_entry(user_id, request)

        result = await kb_service.list_entries(user_id)
        assert result.total == 3
        assert len(result.items) == 3
        assert result.page == 1
        assert result.has_more is False

    async def test_list_entries_pagination(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        for i in range(5):
            await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
                title=f"Page Entry {i}", content=f"Content {i}.", tags=[],
            ))

        result = await kb_service.list_entries(user_id, page=1, page_size=2)
        assert len(result.items) == 2
        assert result.total == 5
        assert result.has_more is True

    async def test_list_entries_with_tag(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="Tagged", content="Has a tag.", tags=["special"],
        ))
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="Plain", content="No tag.", tags=[],
        ))

        result = await kb_service.list_entries(user_id, tag="special")
        assert result.total == 1
        assert result.items[0].title == "Tagged"

    async def test_search_falls_back_to_keyword(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="Python Programming", content="Learn Python basics.", tags=[],
        ))
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="Rust Programming", content="Learn Rust basics.", tags=[],
        ))

        result = await kb_service.search(user_id, "Python")
        assert result.total >= 1
        assert any("Python" in r.item.title for r in result.results)

    async def test_search_returns_keyword_match_type_when_chroma_down(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="Search Test", content="This should be found via keyword fallback.", tags=[],
        ))

        result = await kb_service.search(user_id, "keyword fallback")
        assert result.total >= 1
        assert result.results[0].match_type == "keyword"

    async def test_get_tags(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="A", content="A.", tags=["tag1", "tag2"],
        ))
        await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
            title="B", content="B.", tags=["tag2"],
        ))

        tags = await kb_service.get_tags(user_id)
        tag_map = {t.name: t.count for t in tags}
        assert tag_map.get("tag1") == 1
        assert tag_map.get("tag2") == 2

    async def test_get_recent_context(
        self,
        kb_service: KnowledgeBaseService,
        user_id: uuid.UUID,
    ) -> None:
        for i in range(5):
            await kb_service.add_entry(user_id, AddKnowledgeEntryRequest(
                title=f"Recent {i}", content=f"Content {i}.", tags=[],
            ))

        items = await kb_service.get_recent_context(user_id, limit=3)
        assert len(items) == 3


class TestKnowledgeAPI:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self,
        db: Database,
        mock_chroma: ChromaService,
        mock_embedding: EmbeddingService,
    ) -> AsyncGenerator[None, None]:
        from main import app

        kb_service = KnowledgeBaseService(db=db, chroma=mock_chroma, embedding=mock_embedding)

        async def _override() -> KnowledgeBaseService:
            return kb_service

        app.dependency_overrides[get_knowledge_service] = _override
        yield
        app.dependency_overrides.clear()

    @pytest_asyncio.fixture(name="client")
    async def fixture_client(self, db: Database) -> AsyncGenerator[AsyncClient, None]:
        from main import app

        app.state.db = db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_list_entries_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        resp = await client.get("/api/v1/knowledge/entries", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_add_entry(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        payload = {
            "title": "API Test Entry",
            "content": "Added via API test.",
            "tags": ["api-test"],
        }
        resp = await client.post(
            "/api/v1/knowledge/entries",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "API Test Entry"

    async def test_get_entry_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        payload = {"title": "Get via API", "content": "Entry to fetch."}
        create = await client.post("/api/v1/knowledge/entries", json=payload, headers=auth_headers)
        entry_id = create.json()["id"]

        resp = await client.get(f"/api/v1/knowledge/entries/{entry_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get via API"

    async def test_get_entry_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        resp = await client.get(
            f"/api/v1/knowledge/entries/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_update_entry(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        payload = {"title": "Before Update", "content": "Original."}
        create = await client.post("/api/v1/knowledge/entries", json=payload, headers=auth_headers)
        entry_id = create.json()["id"]

        resp = await client.put(
            f"/api/v1/knowledge/entries/{entry_id}",
            json={"title": "After Update"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "After Update"

    async def test_delete_entry(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        payload = {"title": "Delete via API", "content": "To be removed."}
        create = await client.post("/api/v1/knowledge/entries", json=payload, headers=auth_headers)
        entry_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/knowledge/entries/{entry_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_search_entries(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        await client.post(
            "/api/v1/knowledge/entries",
            json={"title": "Django Framework", "content": "Web framework for Python."},
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/knowledge/search?q=Django",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_list_tags(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        await client.post(
            "/api/v1/knowledge/entries",
            json={"title": "Tagged Entry", "content": "Content.", "tags": ["alpha", "beta"]},
            headers=auth_headers,
        )

        resp = await client.get("/api/v1/knowledge/tags", headers=auth_headers)
        assert resp.status_code == 200
        tag_names = [t["name"] for t in resp.json()]
        assert "alpha" in tag_names

    async def test_context_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        for i in range(3):
            await client.post(
                "/api/v1/knowledge/entries",
                json={"title": f"Context {i}", "content": f"Content {i}."},
                headers=auth_headers,
            )

        resp = await client.get("/api/v1/knowledge/context", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 3

    async def test_unauthorized_access(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/knowledge/entries")
        assert resp.status_code == 401
