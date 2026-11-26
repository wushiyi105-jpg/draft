from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from draft.doctor import run_doctor
from draft.iface.cli import app
from draft.iface.web import create_app


def _seed(store):
    store.add_pillar("选品测评", 0.5)
    store.add_post("a", "选品测评", date(2026, 10, 2), 1000)
    store.add_idea("选题 A", "选品测评")
    store.add_slot(date(2026, 11, 27), "选品测评", "选题 A")


def test_web_index(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    assert client.get("/").status_code == 200
    assert "选题 A" in client.get("/").text


def test_web_health(store, settings):
    client = TestClient(create_app(settings, store))
    assert client.get("/health").json()["status"] == "ok"


def test_cli_plan_and_bad_month(tmp_path):
    runner = CliRunner()
    db = str(tmp_path / "c.db")
    assert runner.invoke(app, ["plan", "--db", db, "--month", "2026-11"]).exit_code == 0
    assert runner.invoke(app, ["plan", "--db", db, "--month", "2026-13"]).exit_code != 0


def test_doctor_green(settings):
    checks, ok = run_doctor(settings)
    assert ok is True
