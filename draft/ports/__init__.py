"""端口：app 实际调用的方法集合，实现见 adapters。"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from ..domain.models import Idea, Pillar, Post, Slot


@runtime_checkable
class StorePort(Protocol):
    def list_posts(self) -> list[Post]: ...

    def list_pillars(self) -> list[Pillar]: ...

    def list_slots(self) -> list[Slot]: ...

    def list_ideas(self) -> list[Idea]: ...

    def add_slot(self, day: date, pillar: str, title: str) -> int: ...


@runtime_checkable
class LLMPort(Protocol):
    def write(self, system: str, facts: str) -> str: ...
