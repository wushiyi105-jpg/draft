"""一周选题表：7 天排期 + 每条开头三句 + 平台规则。"""

from __future__ import annotations

from datetime import date, timedelta

from ..domain.catalog import pillars as account_pillars
from ..domain.catalog import platform_by_id, structures_for
from ..domain.models import Idea
from ..domain.rules.reuse import WINDOW_DAYS
from ..ports import StorePort

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _recent_titles(store: StorePort, start: date) -> set[str]:
    cutoff = start - timedelta(days=WINDOW_DAYS)
    return {
        p.title.strip()
        for p in store.list_posts()
        if p.published_on >= cutoff
    }


def build_week(
    store: StorePort,
    start: date,
    platform: str = "xhs",
    days: int = 7,
) -> str:
    p = platform_by_id(platform)
    recent = _recent_titles(store, start)
    slots = {s.day: s for s in store.list_slots()}
    ideas: list[Idea] = [i for i in store.list_ideas() if not i.used and i.title.strip() not in recent]
    pillars = [x.name for x in store.list_pillars()]

    rows: list[tuple[date, str, str]] = []
    used_titles = set(recent)
    for offset in range(days):
        day = start + timedelta(days=offset)
        slot = slots.get(day)
        if slot and (slot.title or "").strip() and slot.title.strip() not in used_titles:
            rows.append((day, slot.pillar, slot.title.strip()))
            used_titles.add(slot.title.strip())
            continue
        while ideas and ideas[0].title.strip() in used_titles:
            ideas.pop(0)
        if not ideas:
            rows.append((day, pillars[offset % len(pillars)], f"{pillars[offset % len(pillars)]}：本周补位选题"))
            continue
        idea = ideas.pop(0)
        rows.append((day, idea.pillar, idea.title.strip()))
        used_titles.add(idea.title.strip())

    lines = [
        f"# 一周选题表 · {start.isoformat()} 起",
        "",
        f"> 平台：**{p['name']}**；标题 ≤{p['title_max']} 字，正文 ≤{p['body_max']} 字；"
        f"最佳发布时间 {p['best_time']}。30 天内用过的标题不再推荐。",
        "",
        "## 排期总表",
        "",
        "| 日期 | 星期 | 支柱 | 选题 | 结构 |",
        "| --- | --- | --- | --- | --- |",
    ]
    chosen = []
    for offset, (day, pillar, title) in enumerate(rows):
        structs = structures_for(pillar)
        s = structs[offset % len(structs)]
        chosen.append((day, pillar, title, s))
        flag = " ⚠" if len(title) > p["title_max"] else ""
        lines.append(
            f"| {day.isoformat()} | {WEEKDAYS[day.weekday()]} | {pillar} | {title}{flag} | {s['name']} |"
        )

    lines += ["", "## 每条的开头三句（直接复制）", ""]
    for day, pillar, title, s in chosen:
        lines += [
            f"### {day.isoformat()} · {WEEKDAYS[day.weekday()]} · {pillar}",
            f"**{title}**",
            "",
            "```text",
            *[line.format(topic=title) for line in s["lines"]],
            "```",
            "",
        ]

    lines += [
        "## 平台规则（发之前对一遍）",
        "",
        f"- 标题上限 {p['title_max']} 字，正文上限 {p['body_max']} 字；话题 {p['hashtags']}",
    ]
    lines += [f"- {r}" for r in p["rules"]]
    lines += [
        "",
        "## 账号支柱（3 类，别混着写）",
        "",
        "| 支柱 | 这一栏解决什么 | 结尾怎么引导 | 拿什么作证 |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        f"| {x['name']} | {x['goal']} | {x['cta']} | {x['proof']} |" for x in account_pillars()
    ]
    lines += [
        "",
        "---",
        "",
        "说明：选题只从本地库存和未用过的标题里挑；30 天内发过的标题自动排除。"
        "开头三句由本地结构模板生成，不调用模型。",
        "",
    ]
    return "\n".join(lines)
