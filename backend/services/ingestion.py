from __future__ import annotations

import time
import uuid

from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from database.db import Database
from schemas.knowledge import AddKnowledgeEntryRequest, IngestResponse
from services.knowledge import KnowledgeBaseService

logger = get_logger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        db: Database,
        kb_service: KnowledgeBaseService,
        llm: LLMClient,
        default_model: str = "gemini-2.0-flash",
    ) -> None:
        self._db = db
        self._kb = kb_service
        self._llm = llm
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
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                response = await client.get(url, headers={"User-Agent": "BrandOS/1.0"})
                response.raise_for_status()
                return response.text
        except Exception as exc:
            logger.exception("url_fetch_failed", url=url, error=str(exc))
            return None

    async def _generate_summary(self, text: str) -> str:
        content_preview = text[:2000]
        prompt = "Summarize the following content in 1-3 sentences:\n\n" + content_preview
        request = CompletionRequest(
            model=self._default_model,
            messages=[ChatMessage(role="user", content=prompt)],
            system_prompt="You are a precise summarizer. Keep summaries concise and factual.",
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
        combined = f"{title}\n\n{content[:1000]}"
        prompt = (
            "Extract 3-5 lowercase, hyphen-separated tags from this content. "
            "Return only the tags as a comma-separated list:\n\n" + combined
        )
        request = CompletionRequest(
            model=self._default_model,
            messages=[ChatMessage(role="user", content=prompt)],
            system_prompt=(
                "You are a tag extraction system. Return only comma-separated tags, nothing else."
            ),
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
