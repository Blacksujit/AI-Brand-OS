from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ingestion import IngestionPipeline, _html_to_text


class TestHTMLToText:
    def test_strips_tags(self) -> None:
        html = "<html><body><p>Hello world</p></body></html>"
        assert _html_to_text(html) == "Hello world"

    def test_removes_scripts(self) -> None:
        html = "<script>alert('xss')</script><p>Content</p>"
        assert _html_to_text(html) == "Content"

    def test_removes_styles(self) -> None:
        html = "<style>body { color: red; }</style><p>Visible</p>"
        assert _html_to_text(html) == "Visible"

    def test_preserves_paragraph_breaks(self) -> None:
        html = "<p>First para</p><p>Second para</p>"
        result = _html_to_text(html)
        assert "First para" in result
        assert "Second para" in result

    def test_empty_html(self) -> None:
        assert _html_to_text("") == ""

    def test_no_html_tags(self) -> None:
        assert _html_to_text("plain text") == "plain text"

    def test_line_breaks(self) -> None:
        html = "Line1<br>Line2<br/>Line3"
        result = _html_to_text(html)
        assert "Line1" in result
        assert "Line2" in result
        assert "Line3" in result


class TestIngestionPipeline:
    @pytest.fixture
    def pipeline(self) -> IngestionPipeline:
        db = MagicMock()
        kb = AsyncMock()
        llm = AsyncMock()
        llm.complete = AsyncMock()

        response = MagicMock()
        response.content = "test summary"
        llm.complete.return_value = response

        entry = MagicMock()
        entry.id = uuid.uuid4()
        kb.add_entry = AsyncMock(return_value=entry)

        return IngestionPipeline(db=db, kb_service=kb, llm=llm)

    @pytest.mark.asyncio
    async def test_ingest_markdown(self, pipeline: IngestionPipeline) -> None:
        user_id = uuid.uuid4()
        result = await pipeline.ingest_markdown(
            user_id=user_id,
            title="Test Doc",
            content="# Hello\nThis is test content.",
        )
        assert result.title == "Test Doc"
        assert result.entry_id is not None
        assert result.processing_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_ingest_markdown_with_tags(self, pipeline: IngestionPipeline) -> None:
        user_id = uuid.uuid4()
        result = await pipeline.ingest_markdown(
            user_id=user_id,
            title="Tagged Doc",
            content="Some content here.",
            tags=["manual-tag"],
        )
        assert "manual-tag" in result.tags

    @pytest.mark.asyncio
    async def test_ingest_markdown_with_source_id(self, pipeline: IngestionPipeline) -> None:
        user_id = uuid.uuid4()
        result = await pipeline.ingest_markdown(
            user_id=user_id,
            title="Sourced Doc",
            content="Content",
            source_id="src-123",
        )
        assert result.title == "Sourced Doc"

    @pytest.mark.asyncio
    async def test_ingest_url_fetch_failure(self, pipeline: IngestionPipeline) -> None:
        with patch("httpx.AsyncClient.get", side_effect=Exception("Network error")):
            with pytest.raises(ValueError, match="Failed to extract content"):
                await pipeline.ingest_url(
                    user_id=uuid.uuid4(),
                    url="https://example.com",
                )

    @pytest.mark.asyncio
    async def test_ingest_url_content_type_check(self, pipeline: IngestionPipeline) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Hello from example</p></body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await pipeline.ingest_url(
                user_id=uuid.uuid4(),
                url="https://example.com",
                title="Example",
                tags=["test"],
            )
            assert result.title == "Example"

    @pytest.mark.asyncio
    async def test_ingest_url_auto_title(self, pipeline: IngestionPipeline) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await pipeline.ingest_url(
                user_id=uuid.uuid4(),
                url="https://example.com/my-article",
            )
            assert "My Article" in result.title

    @pytest.mark.asyncio
    async def test_summary_on_llm_failure(self, pipeline: IngestionPipeline) -> None:
        pipeline._llm.complete = AsyncMock(side_effect=Exception("LLM down"))
        result = await pipeline.ingest_markdown(
            user_id=uuid.uuid4(),
            title="No Summary",
            content="Content here",
        )
        assert result.summary == ""

    @pytest.mark.asyncio
    async def test_content_truncation(self, pipeline: IngestionPipeline) -> None:
        long_content = "x" * 100_000
        user_id = uuid.uuid4()
        result = await pipeline.ingest_markdown(
            user_id=user_id,
            title="Long Content",
            content=long_content,
        )
        out_file = "backend/tests/test_ingestion.py"
        assert result.title == "Long Content"

    @pytest.mark.asyncio
    async def test_url_without_title_fallback(self, pipeline: IngestionPipeline) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await pipeline.ingest_url(
                user_id=uuid.uuid4(),
                url="https://example.com/article-name",
                tags=["tag1"],
            )
            assert "Article Name" in result.title

    def test_html_to_text_empty(self) -> None:
        assert _html_to_text("") == ""
