"""一周选题表：7 天、不重复、30 天内用过的标题排除。"""

from __future__ import annotations

from datetime import date

from draft.adapters.store import SqliteStore
from draft.app.weekly import build_week


def _seed(store: SqliteStore) -> None:
    store.add_pillar("选品测评", 0.4)
    store.add_pillar("使用教程", 0.35)
    store.add_pillar("幕后日常", 0.25)
    store.add_post("刚发过的旧题", "选品测评", date(2026, 11, 20), 1000)
    for title, pillar in [
        ("新题一", "选品测评"),
        ("新题二", "使用教程"),
        ("新题三", "幕后日常"),
        ("新题四", "选品测评"),
        ("新题五", "使用教程"),
        ("新题六", "幕后日常"),
    ]:
        store.add_idea(title, pillar)


def test_week_has_seven_distinct_days(tmp_path) -> None:
    store = SqliteStore(tmp_path / "w.db")
    _seed(store)
    text = build_week(store, date(2026, 11, 28))
    assert "| 日期 | 星期 | 支柱 | 选题 | 结构 |" in text
    days = [line for line in text.splitlines() if line.startswith("| 2026-")]
    assert len(days) == 7
    titles = [line.split("|")[4].strip().split(" ⚠")[0] for line in days]
    assert len(set(titles)) == 7
    assert "刚发过的旧题" not in text


def test_week_uses_slot_title_when_valid(tmp_path) -> None:
    store = SqliteStore(tmp_path / "w2.db")
    _seed(store)
    store.add_slot(date(2026, 11, 29), "使用教程", "排好的题")
    text = build_week(store, date(2026, 11, 28))
    assert "排好的题" in text


def test_week_rejects_bad_platform_falls_back(tmp_path) -> None:
    store = SqliteStore(tmp_path / "w3.db")
    _seed(store)
    text = build_week(store, date(2026, 11, 28), platform="不存在")
    assert "小红书" in text


def test_week_opening_three_lines(tmp_path) -> None:
    store = SqliteStore(tmp_path / "w4.db")
    _seed(store)
    text = build_week(store, date(2026, 11, 28))
    assert text.count("```text") == 7
    assert text.count("```") == 14
