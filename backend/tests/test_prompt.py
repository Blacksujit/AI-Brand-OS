from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from services.prompt.service import PromptNotFoundError, PromptService


class TestPromptService:
    def test_load_prompt(self) -> None:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        if not prompts_dir.exists():
            pytest.skip("No prompts directory found")
        service = PromptService(prompts_dir=str(prompts_dir))
        writer_prompt = service.load_prompt("writing_agent")
        assert writer_prompt is not None
        assert len(writer_prompt) > 50

    def test_load_nonexistent_prompt(self) -> None:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        if not prompts_dir.exists():
            pytest.skip("No prompts directory found")
        service = PromptService(prompts_dir=str(prompts_dir))
        with pytest.raises(PromptNotFoundError):
            service.load_prompt("nonexistent_agent")

    def test_build_prompt(self) -> None:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        if not prompts_dir.exists():
            pytest.skip("No prompts directory found")
        service = PromptService(prompts_dir=str(prompts_dir))
        system_prompt, _user_prompt = service.build_prompt(
            agent_name="writing_agent",
            system_vars={
                "topic": "AI in marketing",
                "headline": "test",
                "hook": "test",
                "angle": "test",
                "format": "linkedin_post",
                "platform": "linkedin",
                "knowledge_context": "",
                "voice_profile": "professional",
                "word_count": "300",
                "structure": "list",
                "key_points": "point 1",
                "data_points": "",
                "examples": "",
                "cta": "Share",
                "keywords": "AI, marketing",
            },
        )
        assert isinstance(system_prompt, str)

    def test_cache_hit(self) -> None:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        if not prompts_dir.exists():
            pytest.skip("No prompts directory found")
        service = PromptService(prompts_dir=str(prompts_dir))
        first = service.load_prompt("writing_agent")
        second = service.load_prompt("writing_agent")
        assert first == second
        assert "writing_agent" in service._cache

    def test_build_prompt_without_variables(self) -> None:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        if not prompts_dir.exists():
            pytest.skip("No prompts directory found")
        service = PromptService(prompts_dir=str(prompts_dir))
        system_prompt, _user_prompt = service.build_prompt(agent_name="writing_agent")
        assert isinstance(system_prompt, str)

    def test_build_prompt_nonexistent(self) -> None:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        if not prompts_dir.exists():
            pytest.skip("No prompts directory found")
        service = PromptService(prompts_dir=str(prompts_dir))
        with pytest.raises(PromptNotFoundError):
            service.build_prompt(agent_name="missing_agent")

    def test_invalid_directory(self) -> None:
        fake_path = f"/tmp/nonexistent_{uuid.uuid4().hex}"
        service = PromptService(prompts_dir=fake_path)
        assert service._prompts_dir == Path(fake_path)
