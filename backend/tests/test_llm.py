from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.llm import (
    LLMClient,
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    TokenUsage,
)


class TestChatMessage:
    def test_system_role(self) -> None:
        msg = ChatMessage(role="system", content="You are a helpful assistant")
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant"

    def test_user_role(self) -> None:
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_assistant_role(self) -> None:
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"


class TestCompletionRequest:
    def test_defaults(self) -> None:
        req = CompletionRequest(model="gemini-2.0-flash", messages=[])
        assert req.model == "gemini-2.0-flash"
        assert req.messages == []
        assert req.system_prompt is None
        assert req.temperature == 0.7
        assert req.max_tokens == 2048
        assert req.stop_sequences == []
        assert req.response_format == "text"

    def test_with_all_fields(self) -> None:
        msgs = [ChatMessage(role="user", content="Hi")]
        req = CompletionRequest(
            model="gemini-2.5-pro",
            messages=msgs,
            system_prompt="Be concise",
            temperature=0.1,
            max_tokens=512,
            stop_sequences=["\n"],
            response_format="json_object",
        )
        assert req.model == "gemini-2.5-pro"
        assert req.messages == msgs
        assert req.system_prompt == "Be concise"
        assert req.temperature == 0.1
        assert req.max_tokens == 512
        assert req.stop_sequences == ["\n"]
        assert req.response_format == "json_object"


class TestTokenUsage:
    def test_construction(self) -> None:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30


class TestCompletionResponse:
    def test_construction(self) -> None:
        usage = TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20)
        resp = CompletionResponse(
            content="Hello!",
            finish_reason="stop",
            usage=usage,
            model="gemini-2.0-flash",
            latency_ms=123,
        )
        assert resp.content == "Hello!"
        assert resp.finish_reason == "stop"
        assert resp.usage == usage
        assert resp.model == "gemini-2.0-flash"
        assert resp.latency_ms == 123


class TestLLMClient:
    @pytest.fixture
    def settings(self) -> MagicMock:
        s = MagicMock()
        s.gemini_api_key = "test-key"
        return s

    def test_construction(self, settings: MagicMock) -> None:
        client = LLMClient(settings)
        assert client._settings == settings
        assert client._clients == {}

    def test_to_langchain_messages_with_system_prompt(
        self, settings: MagicMock
    ) -> None:
        client = LLMClient(settings)
        request = CompletionRequest(
            model="gemini-2.0-flash",
            messages=[
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi"),
                ChatMessage(role="system", content="Be polite"),
            ],
            system_prompt="You are a helpful assistant",
        )
        result = client._to_langchain_messages(request)
        assert len(result) == 4
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "You are a helpful assistant"
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "Hello"
        assert isinstance(result[2], AIMessage)
        assert result[2].content == "Hi"
        assert isinstance(result[3], SystemMessage)
        assert result[3].content == "Be polite"

    def test_to_langchain_messages_no_system_prompt(
        self, settings: MagicMock
    ) -> None:
        client = LLMClient(settings)
        request = CompletionRequest(
            model="gemini-2.0-flash",
            messages=[
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi"),
            ],
        )
        result = client._to_langchain_messages(request)
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"
        assert isinstance(result[1], AIMessage)
        assert result[1].content == "Hi"

    def test_to_langchain_messages_empty(self, settings: MagicMock) -> None:
        client = LLMClient(settings)
        request = CompletionRequest(model="gemini-2.0-flash", messages=[])
        result = client._to_langchain_messages(request)
        assert result == []

    @pytest.mark.asyncio
    async def test_estimate_cost_returns_expected_shape(self, settings: MagicMock) -> None:
        client = LLMClient(settings)
        mock_langchain_client = MagicMock()
        mock_langchain_client.get_num_tokens_from_messages.return_value = 42
        client._get_client = MagicMock(return_value=mock_langchain_client)
        request = CompletionRequest(
            model="gemini-2.0-flash",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        result = await client.estimate_cost(request)
        assert isinstance(result, dict)
        assert result["model"] == "gemini-2.0-flash"
        assert result["estimated_tokens"] == 42
        assert result["estimated_cost_usd"] == 42 * 0.0000005

    @pytest.mark.asyncio
    async def test_complete_fallback_to_next_model(self, settings: MagicMock) -> None:
        client = LLMClient(settings)
        request = CompletionRequest(
            model="gemini-2.5-pro",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        call_count = 0
        expected_usage = TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15)

        async def attempt_complete(model: str, req: CompletionRequest) -> CompletionResponse:
            nonlocal call_count
            call_count += 1
            if model == "gemini-2.5-pro":
                raise ConnectionError("API unavailable")
            return CompletionResponse(
                content=f"Response from {model}",
                finish_reason="stop",
                usage=expected_usage,
                model=model,
                latency_ms=50,
            )

        client._attempt_complete = attempt_complete
        result = await client.complete(request)
        assert result.model == "gemini-2.0-flash"
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_complete_all_models_fail_raises(self, settings: MagicMock) -> None:
        client = LLMClient(settings)
        request = CompletionRequest(
            model="gemini-2.5-pro",
            messages=[ChatMessage(role="user", content="Hello")],
        )

        async def always_fail(model: str, req: CompletionRequest) -> CompletionResponse:
            raise RuntimeError(f"{model} failed")

        client._attempt_complete = always_fail
        with pytest.raises(RuntimeError, match="gemini-1.5-flash failed|No LLM models succeeded"):
            await client.complete(request)

    @pytest.mark.asyncio
    async def test_complete_retries_then_falls_through(self, settings: MagicMock) -> None:
        client = LLMClient(settings)
        request = CompletionRequest(
            model="gemini-2.0-flash",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        attempt_count = 0
        expected_usage = TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3)

        async def succeed_on_third_retry(model: str, req: CompletionRequest) -> CompletionResponse:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise TimeoutError(f"Attempt {attempt_count} timed out")
            return CompletionResponse(
                content="Got it",
                finish_reason="stop",
                usage=expected_usage,
                model=model,
                latency_ms=30,
            )

        client._attempt_complete = succeed_on_third_retry
        result = await client.complete(request)
        assert result.model == "gemini-2.0-flash"
        assert attempt_count == 3
