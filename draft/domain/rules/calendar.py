"""日历缺口：未来 7 天没有排期就是断更。"""

from __future__ import annotations

from datetime import date, timedelta

from ..models import Finding, Slot

PENALTY = 3
HORIZON = 7


def gaps(slots: list[Slot], today: date, horizon: int = HORIZON) -> list[date]:
    planned = {s.day for s in slots}
    return [
        today + timedelta(days=i)
        for i in range(horizon)
        if today + timedelta(days=i) not in planned
    ]


def check(slots: list[Slot], today: date) -> list[Finding]:
    out: list[Finding] = []
    for d in gaps(slots, today):
        out.append(Finding("calendar.gap", f"{d} 没有排期", PENALTY, d.isoformat()))
    return out
