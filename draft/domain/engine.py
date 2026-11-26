"""本地核算：支柱占比、复用候选、日历缺口、统计。"""

from __future__ import annotations

from datetime import date

from .models import Finding, Pillar, Plan, Post, Slot
from .rules.calendar import check as calendar_check
from .rules.calendar import gaps
from .rules.pillars import best, month_posts, shares
from .rules.pillars import check as pillar_check
from .rules.reuse import candidates


def build(
    month: str, posts: list[Post], pillars: list[Pillar], slots: list[Slot], today: date
) -> Plan:
    current = month_posts(posts, month)
    plan = Plan(month=month)
    plan.shares = shares(current, pillars)
    plan.reuse = [(p.title, p.published_on) for p in candidates(posts, today)[:5]]
    plan.gaps = gaps(slots, today)
    findings: list[Finding] = []
    findings += pillar_check(current, pillars)
    findings += calendar_check(slots, today)
    from .rules.reuse import check as reuse_check

    findings += reuse_check(slots, posts, today)
    plan.findings = findings
    return plan


def stats(posts: list[Post], pillars: list[Pillar]) -> dict[str, int]:
    out = {p.name: 0 for p in pillars}
    for post in posts:
        out[post.pillar] = out.get(post.pillar, 0) + post.views
    return out


def top(posts: list[Post]) -> list[Post]:
    return best(posts)
