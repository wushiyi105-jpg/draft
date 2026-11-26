from __future__ import annotations

from datetime import date

from draft.domain.engine import build, stats
from draft.domain.guard import check


def test_claim_word_dropped():
    kept, findings = check([{"title": "这条一定爆了", "pillar": "选品测评"}])
    assert kept == []
    assert findings[0].rule_id == "guard.claim"


def test_generated_item_marked_unverified():
    kept, _ = check([{"title": "普通选题", "pillar": "使用教程"}])
    assert kept[0]["verified"] is False


def test_stats_sum_by_pillar(store, pillars):
    store.add_post("a", "选品测评", date(2026, 11, 2), 300)
    store.add_post("b", "使用教程", date(2026, 11, 3), 200)
    s = stats(store.list_posts(), store.list_pillars())
    assert s["选品测评"] == 300
    assert s["幕后日常"] == 0


def test_build_reports_gaps_and_shares(store, pillars):
    store.add_post("a", "选品测评", date(2026, 11, 2), 300)
    p = build("2026-11", store.list_posts(), store.list_pillars(), [], date(2026, 11, 27))
    assert p.gaps[0] == date(2026, 11, 27)
    assert p.shares["选品测评"] == 1.0
