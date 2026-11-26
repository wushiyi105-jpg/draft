"""支柱占比：实际与目标差超过 10 个百分点就提醒。"""

from __future__ import annotations

from datetime import date

from ..models import Finding, Pillar, Post

TOLERANCE = 0.10
PENALTY = 4


def shares(posts: list[Post], pillars: list[Pillar]) -> dict[str, float]:
    total = len(posts)
    out: dict[str, float] = {}
    for p in pillars:
        n = len([x for x in posts if x.pillar == p.name])
        out[p.name] = n / total if total else 0.0
    return out


def check(posts: list[Post], pillars: list[Pillar]) -> list[Finding]:
    if not posts:
        return []
    actual = shares(posts, pillars)
    return [
        Finding(
            "pillar.balance",
            f"{p.name} 占比 {actual[p.name]:.0%}，目标 {p.target:.0%}，差超过 10 个百分点",
            PENALTY,
            p.name,
        )
        for p in pillars
        if abs(actual[p.name] - p.target) > TOLERANCE
    ]


def month_posts(posts: list[Post], month: str) -> list[Post]:
    return [p for p in posts if p.published_on.strftime("%Y-%m") == month]


def best(posts: list[Post], limit: int = 3) -> list[Post]:
    return sorted(posts, key=lambda p: p.views, reverse=True)[:limit]


def today() -> date:
    return date.today()
