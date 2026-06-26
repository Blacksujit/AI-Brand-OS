from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal


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
    finish_reason: Literal["stop", "length", "tool_use"]
    usage: TokenUsage
    model: str
    latency_ms: int


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    model: str
    usage: TokenUsage


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        ...

    @abstractmethod
    async def complete_stream(
        self, request: CompletionRequest
    ) -> AsyncIterator[CompletionResponse]:
        ...

    @abstractmethod
    async def embed(self, input: str | list[str]) -> EmbeddingResponse:
        ...

    @abstractmethod
    async def estimate_cost(self, request: CompletionRequest) -> dict[str, Any]:
        ...
