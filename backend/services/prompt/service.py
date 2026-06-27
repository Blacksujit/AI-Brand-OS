from __future__ import annotations

import os
from pathlib import Path

from core.logging import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file does not exist."""


class PromptService:
    """Loads and builds structured prompts for agents.

    Every prompt lives in ``backend/prompts/{agent_name}.md``.
    This service reads raw prompt text from disk and optionally
    interpolates keyword arguments into the template.
    """

    def __init__(self, prompts_dir: str | os.PathLike | None = None) -> None:
        self._prompts_dir = Path(prompts_dir) if prompts_dir else PROMPTS_DIR
        self._cache: dict[str, str] = {}

    def load_prompt(self, agent_name: str) -> str:
        """Load the prompt file for *agent_name*.

        Results are cached after the first read.
        """
        if agent_name in self._cache:
            return self._cache[agent_name]

        path = self._prompts_dir / f"{agent_name}.md"
        if not path.exists():
            msg = f"Prompt file not found: {path} — expected at {self._prompts_dir}/{agent_name}.md"
            raise PromptNotFoundError(msg)

        content = path.read_text(encoding="utf-8")
        self._cache[agent_name] = content
        return content

    def build_prompt(
        self,
        agent_name: str,
        *,
        system_vars: dict[str, str] | None = None,
        user_vars: dict[str, str] | None = None,
    ) -> tuple[str, str]:
        """Load *agent_name* prompt and separate system / user sections.

        Returns (system_prompt, user_prompt).

        The prompt file is expected to have sections like::

            SYSTEM:
            You are the Research Agent...

            USER:
            {scraped_topics_json}

        If ``---`` or ``SYSTEM:`` / ``USER:`` markers are absent the entire
        file is returned as the system prompt.
        """
        raw = self.load_prompt(agent_name)
        system_part = raw
        user_part = ""

        for sep in ("---", "SYSTEM:"):
            if sep in raw:
                parts = raw.split(sep, 1)
                system_part = parts[1] if sep == "SYSTEM:" else parts[0]
                break

        if "USER:" in raw:
            parts = raw.split("USER:", 1)
            system_part = parts[0].replace("SYSTEM:", "").strip()
            user_part = parts[1].strip()

        if system_vars:
            system_part = system_part.format(**system_vars)
        if user_vars:
            user_part = user_part.format(**user_vars)

        return system_part.strip(), user_part.strip()

    def reload(self, agent_name: str) -> None:
        """Clear cached prompt for *agent_name* (next load re-reads disk)."""
        self._cache.pop(agent_name, None)

    def reload_all(self) -> None:
        self._cache.clear()
