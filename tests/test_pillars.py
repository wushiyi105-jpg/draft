from __future__ import annotations

from datetime import date

from draft.domain.rules.pillars import best, check, month_posts, shares


def test_shares_sum_to_one(store, pillars):
    store.add_post("a", "选品测评", date(2026, 11, 2), 100)
    store.add_post("b", "使用教程", date(2026, 11, 9), 100)
    posts = store.list_posts()
    s = shares(posts, store.list_pillars())
    assert abs(sum(s.values()) - 1.0) < 1e-9


def test_imbalance_flagged_with_rule_id(store, pillars):
    for i in range(4):
        store.add_post(f"a{i}", "选品测评", date(2026, 11, 2 + i), 100)
    store.add_post("b", "使用教程", date(2026, 11, 9), 100)
    findings = check(store.list_posts(), store.list_pillars())
    assert findings[0].rule_id == "pillar.balance"
    assert any(f.target == "幕后日常" for f in findings)


def test_balanced_no_finding(store, pillars):
    store.add_post("a", "选品测评", date(2026, 11, 2), 100)
    store.add_post("b", "使用教程", date(2026, 11, 9), 100)
    store.add_post("c", "幕后日常", date(2026, 11, 16), 100)
    assert check(store.list_posts(), store.list_pillars()) == []


def test_month_filter():
    posts = [__import__("draft.domain.models", fromlist=["Post"]).Post(1, "x", "p", date(2026, 10, 1), 1)]
    assert month_posts(posts, "2026-11") == []


def test_best_orders_by_views(store):
    store.add_post("low", "p", date(2026, 10, 1), 10)
    store.add_post("high", "p", date(2026, 10, 2), 900)
    assert best(store.list_posts())[0].title == "high"
