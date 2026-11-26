"""生成项守卫：必须标未验证；声称效果一律丢弃。"""

from __future__ import annotations

from .models import Finding

PENALTY = 8
CLAIMS = ("爆了", "涨粉", "必火", "保证", "一定能", "转化率提升")


def check(items: list[dict]) -> tuple[list[dict], list[Finding]]:
    kept: list[dict] = []
    findings: list[Finding] = []
    for it in items:
        title = str(it.get("title", ""))
        claim = next((c for c in CLAIMS if c in title or c in str(it.get("rationale", ""))), None)
        if claim:
            findings.append(
                Finding("guard.claim", f"「{title}」声称效果（{claim}），丢弃", PENALTY, title)
            )
            continue
        it["verified"] = False
        kept.append(it)
    return kept, findings
