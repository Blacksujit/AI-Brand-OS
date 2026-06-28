from __future__ import annotations

import re
import time
import uuid
from html.parser import HTMLParser

from core.llm import LLMClient
from core.logging import get_logger
from database.db import Database
from schemas.knowledge import AddKnowledgeEntryRequest, IngestResponse
from services.knowledge import KnowledgeBaseService
from services.prompt import PromptService

logger = get_logger(__name__)

_MAX_CONTENT_LENGTH = 50_000
_MAX_URL_FETCH_TIMEOUT = 30


class _HTMLStripper(HTMLParser):
    """Minimal HTML-to-text converter using stdlib only."""

    def __init__(self) -> None:
        super().__init__()
        self._text: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False
        if tag in ("p", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self._text.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._text.append(stripped + " ")

    def get_text(self) -> str:
        raw = "".join(self._text)
        return re.sub(r"\n{3,}", "\n\n", raw).strip()


def _html_to_text(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


class IngestionPipeline:
    def __init__(
        self,
        db: Database,
        kb_service: KnowledgeBaseService,
        llm: LLMClient,
        prompt_service: PromptService | None = None,
        default_model: str = "gemini-2.0-flash",
    ) -> None:
        self._db = db
        self._kb = kb_service
        self._llm = llm
        self._prompt_service = prompt_service or PromptService()
        self._default_model = default_model

    async def ingest_markdown(
        self,
        user_id: uuid.UUID,
        title: str,
        content: str,
        source_id: str | None = None,
        tags: list[str] | None = None,
    ) -> IngestResponse:
        start = time.monotonic()
        content = content[:_MAX_CONTENT_LENGTH]
        summary = await self._generate_summary(content)
        auto_tags = await self._suggest_tags(title, content)
        all_tags = list(set((tags or []) + auto_tags))

        entry = await self._kb.add_entry(
            user_id,
            AddKnowledgeEntryRequest(
                title=title,
                content=content,
                source_type="import",
                source_id=source_id or "",
                summary=summary,
                tags=all_tags,
            ),
        )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info("ingested_markdown", entry_id=str(entry.id), duration_ms=elapsed_ms)
        return IngestResponse(
            entry_id=str(entry.id),
            title=title,
            summary=summary,
            tags=all_tags,
            processing_duration_ms=elapsed_ms,
        )

    async def ingest_url(
        self,
        user_id: uuid.UUID,
        url: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> IngestResponse:
        start = time.monotonic()
        extracted_text = await self._fetch_url_content(url)
        if not extracted_text:
            msg = f"Failed to extract content from {url}"
            raise ValueError(msg)

        extracted_text = extracted_text[:_MAX_CONTENT_LENGTH]
        final_title = (
            title
            or url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
            or url
        )

        summary = await self._generate_summary(extracted_text[:3000])
        auto_tags = await self._suggest_tags(final_title, extracted_text[:1500])
        all_tags = list(set((tags or []) + auto_tags))

        entry = await self._kb.add_entry(
            user_id,
            AddKnowledgeEntryRequest(
                title=final_title,
                content=extracted_text,
                source_type="url",
                source_id=url,
                summary=summary,
                tags=all_tags,
            ),
        )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info("ingested_url", url=url, entry_id=str(entry.id), duration_ms=elapsed_ms)
        return IngestResponse(
            entry_id=str(entry.id),
            title=final_title,
            summary=summary,
            tags=all_tags,
            processing_duration_ms=elapsed_ms,
        )

    async def _fetch_url_content(self, url: str) -> str | None:
        import httpx

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=_MAX_URL_FETCH_TIMEOUT) as client:
                response = await client.get(url, headers={"User-Agent": "BrandOS/1.0"})
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if "text/" not in content_type and "html" not in content_type:
                    logger.warning("url_non_text_content", url=url, content_type=content_type)
                return _html_to_text(response.text)
        except Exception as exc:
            logger.exception("url_fetch_failed", url=url, error=str(exc))
            return None

    async def _generate_summary(self, text: str) -> str:
        system_prompt, user_prompt = self._prompt_service.build_prompt(
            "summary_generator",
            user_vars={"content": text[:2000]},
        )
        from core.llm import ChatMessage, CompletionRequest

        request = CompletionRequest(
            model=self._default_model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=200,
        )
        try:
            response = await self._llm.complete(request)
            return response.content.strip()
        except Exception as exc:
            logger.warning("summary_generation_failed", error=str(exc))
            return ""

    async def _suggest_tags(self, title: str, content: str) -> list[str]:
        system_prompt, user_prompt = self._prompt_service.build_prompt(
            "tag_generator",
            user_vars={
                "title": title,
                "content": content[:1000],
            },
        )
        from core.llm import ChatMessage, CompletionRequest

        request = CompletionRequest(
            model=self._default_model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=100,
        )
        try:
            response = await self._llm.complete(request)
            raw = response.content.strip()
            tags = [t.strip().lower().replace(" ", "-") for t in raw.split(",") if t.strip()]
            return tags[:8]
        except Exception as exc:
            logger.warning("tag_suggestion_failed", error=str(exc))
            return []
