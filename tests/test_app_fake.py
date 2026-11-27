"""真实内存 Store 跑 plan：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from datetime import date

from draft.app.run import plan
from draft.domain.models import Idea, Pillar, Post, Slot
from draft.ports import StorePort


class InMemoryStore:
    def list_posts(self) -> list[Post]:
        return []

    def list_pillars(self) -> list[Pillar]:
        return []

    def list_slots(self) -> list[Slot]:
        return []

    def list_ideas(self) -> list[Idea]:
        return []

    def add_slot(self, day: date, pillar: str, title: str) -> int:
        return 1


def test_plan_with_memory_store() -> None:
    store: StorePort = InMemoryStore()
    out = plan(store, "2026-01", date(2026, 1, 5))
    assert out.month == "2026-01"
