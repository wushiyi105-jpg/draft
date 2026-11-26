"""用例：统计 → 复用候选 → 模型出选题 → 守卫 → 排期。"""

from __future__ import annotations

import json
from datetime import date, timedelta

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..config import Settings
from ..domain.engine import build, stats
from ..domain.guard import check
from ..domain.models import Finding, Plan

PROMPT = """基于账号支柱与近期表现，给 5 个选题，输出 JSON：
{"ideas": [{"title": "选题", "pillar": "支柱名", "rationale": "为什么"}]}
只能引用输入的支柱名与已发内容，不许承诺效果（不许写爆了、涨粉、必火）。"""


def plan(store: SqliteStore, month: str, today: date | None = None) -> Plan:
    return build(
        month, store.list_posts(), store.list_pillars(), store.list_slots(), today or date.today()
    )


def generate(store: SqliteStore, settings: Settings, month: str, today: date | None = None) -> tuple[Plan, list[dict], list[Finding]]:
    p = plan(store, month, today)
    if not settings.llm_enabled:
        return p, [], []
    pillars = [x.name for x in store.list_pillars()]
    top = [x.title for x in sorted(store.list_posts(), key=lambda x: x.views, reverse=True)[:5]]
    llm = build_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model, PROMPT)
    try:
        data = json.loads(llm.write(PROMPT, f"pillars={pillars}\ntop={top}\nstats={stats(store.list_posts(), store.list_pillars())}"))
    except Exception:  # noqa: BLE001
        return p, [], []
    ideas, findings = check(list(data.get("ideas", [])))
    for it in ideas:
        if it.get("pillar") not in pillars:
            findings.append(Finding("guard.claim", f"「{it.get('title')}」支柱不在库里", 8, str(it.get("title"))))
    return p, [i for i in ideas if i.get("pillar") in pillars], findings


def schedule(store: SqliteStore, p: Plan, days: int = 7, today: date | None = None) -> int:
    today = today or date.today()
    ideas = [i for i in store.list_ideas() if not i.used]
    n = 0
    for offset in range(days):
        day = today + timedelta(days=offset)
        if day in p.gaps and ideas:
            idea = ideas.pop(0)
            store.add_slot(day, idea.pillar, idea.title)
            n += 1
    return n
