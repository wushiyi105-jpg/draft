from __future__ import annotations

from datetime import date

from draft.domain.models import Post, Slot
from draft.domain.rules.calendar import check, gaps
from draft.domain.rules.reuse import candidates
from draft.domain.rules.reuse import check as reuse_check


def test_posts_within_30_days_not_candidates():
    posts = [Post(1, "新", "p", date(2026, 11, 20), 999)]
    assert candidates(posts, date(2026, 11, 27)) == []


def test_old_posts_sorted_by_views():
    posts = [Post(1, "旧1", "p", date(2026, 10, 1), 10), Post(2, "旧2", "p", date(2026, 9, 1), 80)]
    assert [p.title for p in candidates(posts, date(2026, 11, 27))] == ["旧2", "旧1"]


def test_slot_reusing_recent_title_flagged():
    posts = [Post(1, "洗耳机", "p", date(2026, 11, 22), 100)]
    slots = [Slot(1, date(2026, 11, 27), "p", "洗耳机")]
    findings = reuse_check(slots, posts, date(2026, 11, 27))
    assert findings[0].rule_id == "reuse.window"
    assert len(findings) == 1


def test_slot_with_new_title_clean():
    posts = [Post(1, "洗耳机", "p", date(2026, 11, 22), 100)]
    assert reuse_check([Slot(1, date(2026, 11, 27), "p", "新题")], posts, date(2026, 11, 27)) == []


def test_calendar_gap_lists_missing_days():
    slots = [Slot(1, date(2026, 11, 27), "p", "x")]
    assert len(gaps(slots, date(2026, 11, 27))) == 6


def test_calendar_gap_finding_has_rule_id():
    findings = check([], date(2026, 11, 27))
    assert len(findings) == 7
    assert findings[0].rule_id == "calendar.gap"
