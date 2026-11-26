from __future__ import annotations

import pytest

from draft.adapters.store import SqliteStore
from draft.config import Settings


@pytest.fixture()
def store(tmp_path) -> SqliteStore:
    return SqliteStore(tmp_path / "t.db")


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(db_path=tmp_path / "t.db", llm_api_key="", port=8013)


@pytest.fixture()
def pillars(store):
    return [store.add_pillar("选品测评", 0.4), store.add_pillar("使用教程", 0.35), store.add_pillar("幕后日常", 0.25)]
