"""本地内容知识：账号支柱、平台规则、20 个开头结构。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parents[2] / "data"


def _load(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def pillars() -> list[dict[str, Any]]:
    return list(_load("account_pillars.json")["pillars"])


@lru_cache(maxsize=1)
def platforms() -> list[dict[str, Any]]:
    return list(_load("platform_rules.json")["platforms"])


@lru_cache(maxsize=1)
def structures() -> list[dict[str, Any]]:
    return list(_load("structures.json")["structures"])


def platform_by_id(pid: str) -> dict[str, Any]:
    for p in platforms():
        if p["id"] == pid or p["name"] == pid:
            return p
    return platforms()[0]


def structures_for(pillar: str) -> list[dict[str, Any]]:
    return [s for s in structures() if s["pillar"] == pillar] or structures()
