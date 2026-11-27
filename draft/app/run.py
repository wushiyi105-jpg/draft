"""用例：统计 → 复用候选 → 模型出选题 → 守卫 → 排期。"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from ..config import Settings
from ..domain.engine import build, stats
from ..domain.guard import check
from ..domain.models import Finding, Plan
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "ideas.md").read_text(encoding="utf-8")


def parse_json(text: str) -> dict:
    """模型常把 JSON 包在 ```json 里；取出第一个完整对象再解析。"""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json object")
    return json.loads(text[start : end + 1])


def plan(store: StorePort, month: str, today: date | None = None) -> Plan:
    return build(
        month, store.list_posts(), store.list_pillars(), store.list_slots(), today or date.today()
    )


def generate(
    store: StorePort,
    settings: Settings,
    month: str,
    today: date | None = None,
    llm: LLMPort | None = None,
) -> tuple[Plan, list[dict], list[Finding]]:
    p = plan(store, month, today)
    if llm is None:
        return p, [], []
    pillars = [x.name for x in store.list_pillars()]
    top = [x.title for x in sorted(store.list_posts(), key=lambda x: x.views, reverse=True)[:5]]
    try:
        data = parse_json(llm.write(PROMPT, f"pillars={pillars}\ntop={top}\nstats={stats(store.list_posts(), store.list_pillars())}"))
    except Exception:  # noqa: BLE001
        return p, [], []
    ideas, findings = check(list(data.get("ideas", [])))
    for it in ideas:
        if it.get("pillar") not in pillars:
            findings.append(Finding("guard.claim", f"「{it.get('title')}」支柱不在库里", 8, str(it.get("title"))))
    return p, [i for i in ideas if i.get("pillar") in pillars], findings


def schedule(store: StorePort, p: Plan, days: int = 7, today: date | None = None) -> int:
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
