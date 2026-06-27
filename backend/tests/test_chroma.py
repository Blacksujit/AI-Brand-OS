from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.chroma import ChromaService


def _run(coro):
    import asyncio
    return asyncio.run(coro)


class TestChromaService:
    @pytest.fixture
    def settings(self) -> MagicMock:
        s = MagicMock()
        s.chromadb_host = "localhost"
        s.chromadb_port = 8001
        s.chromadb_collection_kb = "kb_embeddings"
        return s

    def test_construction(self, settings: MagicMock) -> None:
        service = ChromaService(settings)
        assert service._settings == settings
        assert service._client is None
        assert service._collections == {}

    @patch("core.chroma.chromadb.AsyncHttpClient")
    def test_initialize_returns_false_when_chromadb_unreachable(
        self, mock_async_client: MagicMock, settings: MagicMock
    ) -> None:
        mock_async_client.side_effect = Exception("Connection refused")
        service = ChromaService(settings)
        actual = _run(service.initialize())
        assert actual is False
        assert service._client is None

    def test_health_check_not_initialized(self, settings: MagicMock) -> None:
        service = ChromaService(settings)
        assert service._client is None
        actual = _run(service.health_check())
        assert actual == {"status": "not_initialized"}

    def test_close_does_not_crash(self, settings: MagicMock) -> None:
        service = ChromaService(settings)
        _run(service.close())
