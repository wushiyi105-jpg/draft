"""复用：30 天内不重复推荐；排期里出现 30 天内发过的标题就算冲突。"""

from __future__ import annotations

from datetime import date

from ..models import Finding, Post, Slot

WINDOW_DAYS = 30
PENALTY = 5


def candidates(posts: list[Post], today: date) -> list[Post]:
    return sorted(
        [p for p in posts if (today - p.published_on).days > WINDOW_DAYS],
        key=lambda p: p.views,
        reverse=True,
    )


def conflicts(slots: list[Slot], posts: list[Post], today: date) -> list[tuple[Slot, Post]]:
    recent = {p.title: p for p in posts if (today - p.published_on).days <= WINDOW_DAYS}
    return [(s, recent[s.title]) for s in slots if s.title in recent]


def check(slots: list[Slot], posts: list[Post], today: date) -> list[Finding]:
    out: list[Finding] = []
    for slot, post in conflicts(slots, posts, today):
        days = (today - post.published_on).days
        out.append(
            Finding(
                "reuse.window",
                f"{slot.day} 排的是《{slot.title}》，{days} 天前刚发过，30 天内不重复",
                PENALTY,
                slot.title,
            )
        )
    return out
