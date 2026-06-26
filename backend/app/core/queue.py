from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class Job:
    id: str
    function: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    scheduled_at: datetime | None = None
    max_retries: int = 3
    retry_delay: int = 60


@dataclass
class JobResult:
    job_id: str
    success: bool
    result: Any = None
    error: str | None = None


class JobQueue(ABC):
    @abstractmethod
    async def enqueue(self, job: Job) -> str:
        ...

    @abstractmethod
    async def enqueue_at(self, job: Job, when: datetime) -> str:
        ...

    @abstractmethod
    async def dequeue(
        self, queue: str = "default", timeout: int = 5
    ) -> Job | None:
        ...

    @abstractmethod
    async def acknowledge(self, job_id: str) -> None:
        ...

    @abstractmethod
    async def fail(self, job_id: str, error: str) -> None:
        ...

    @abstractmethod
    async def length(self, queue: str = "default") -> int:
        ...

    @abstractmethod
    async def iter_jobs(
        self, queue: str = "default", limit: int = 100
    ) -> AsyncIterator[Job]:
        ...
        yield  # pragma: no cover
