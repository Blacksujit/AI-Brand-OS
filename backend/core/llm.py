from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from core.config import Settings
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class CompletionRequest:
    model: str
    messages: list[ChatMessage]
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    stop_sequences: list[str] = field(default_factory=list)
    response_format: Literal["text", "json_object"] = "text"


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class CompletionResponse:
    content: str
    finish_reason: Literal["stop", "length"]
    usage: TokenUsage
    model: str
    latency_ms: int


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._clients: dict[str, ChatGoogleGenerativeAI] = {}

    def _get_client(self, model: str) -> ChatGoogleGenerativeAI:
        if model not in self._clients:
            self._clients[model] = ChatGoogleGenerativeAI(
                model=model,
                api_key=self._settings.gemini_api_key,
                temperature=0.7,
                max_tokens=2048,
            )
        return self._clients[model]

    def _to_langchain_messages(
        self, request: CompletionRequest
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = []
        if request.system_prompt:
            messages.append(SystemMessage(content=request.system_prompt))
        for msg in request.messages:
            if msg.role == "system":
                messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        return messages

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        import time

        client = self._get_client(request.model)
        langchain_messages = self._to_langchain_messages(request)

        start = time.monotonic()
        response = await client.ainvoke(langchain_messages)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        content = response.content if isinstance(response.content, str) else ""
        finish_reason: Literal["stop", "length"] = "stop"
        if response.response_metadata:
            finish_reason = response.response_metadata.get(
                "finish_reason", "stop"
            )

        usage = TokenUsage(
            prompt_tokens=response.usage_metadata.get("input_tokens", 0)
            if response.usage_metadata
            else 0,
            completion_tokens=response.usage_metadata.get("output_tokens", 0)
            if response.usage_metadata
            else 0,
            total_tokens=(
                response.usage_metadata.get("input_tokens", 0)
                + response.usage_metadata.get("output_tokens", 0)
            )
            if response.usage_metadata
            else 0,
        )

        logger.info(
            "llm_complete",
            model=request.model,
            latency_ms=elapsed_ms,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )

        return CompletionResponse(
            content=content,
            finish_reason=finish_reason,
            usage=usage,
            model=request.model,
            latency_ms=elapsed_ms,
        )

    async def complete_stream(
        self, request: CompletionRequest
    ) -> AsyncIterator[CompletionResponse]:
        client = self._get_client(request.model)
        langchain_messages = self._to_langchain_messages(request)
        full_content: list[str] = []

        async for chunk in client.astream(langchain_messages):
            content = chunk.content if isinstance(chunk.content, str) else ""
            if content:
                full_content.append(content)
                yield CompletionResponse(
                    content=content,
                    finish_reason="stop",
                    usage=TokenUsage(0, 0, 0),
                    model=request.model,
                    latency_ms=0,
                )

    async def estimate_cost(self, request: CompletionRequest) -> dict[str, Any]:
        client = self._get_client(request.model)
        langchain_messages = self._to_langchain_messages(request)
        token_count = client.get_num_tokens_from_messages(langchain_messages)
        return {
            "model": request.model,
            "estimated_tokens": token_count,
            "estimated_cost_usd": token_count * 0.0000005,
        }
