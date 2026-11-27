"""命令行：seed / plan / stats / ideas / schedule / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console

from ..adapters.llm import build_llm
from ..adapters.notify import WebhookNotifier
from ..adapters.store import SqliteStore
from ..app.run import PROMPT, generate, plan, schedule, stats
from ..app.weekly import build_week
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main

app = typer.Typer(help="内容运营：今天发什么", no_args_is_help=True)
console = Console()


def _settings(db: Path | None, port: int | None = None) -> Settings:
    s = default_settings.model_copy(deep=True)
    if db:
        s.db_path = db
    if port:
        s.port = port
    return s


def _store(settings: Settings) -> SqliteStore:
    return SqliteStore(settings.db_path)


def _notify(settings: Settings, text: str) -> None:
    if not text or not settings.webhook_url:
        return
    ok = WebhookNotifier(settings.webhook_url).send(text)
    console.print(f"[dim]webhook {'ok' if ok else 'failed'}[/]")


@app.command()
def seed(db: Path = typer.Option(None)) -> None:
    """写入支柱、历史内容、选题与排期。"""
    s = _settings(db)
    store = _store(s)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seed.json").read_text(encoding="utf-8")
    )
    for p in data["pillars"]:
        store.add_pillar(p["name"], p["target"])
    for post in data["posts"]:
        store.add_post(post["title"], post["pillar"], date.fromisoformat(post["on"]), post["views"])
    for idea in data["ideas"]:
        store.add_idea(idea["title"], idea["pillar"], idea.get("used", False), idea.get("verified", False))
    for slot in data.get("slots", []):
        store.add_slot(date.fromisoformat(slot["on"]), slot["pillar"], slot.get("title", ""))
    console.print(f"已写入 {len(data['pillars'])} 个支柱、{len(data['posts'])} 条内容、{len(data['ideas'])} 个选题")


@app.command("plan")
def plan_cmd(month: str = typer.Option("", help="2026-11"), db: Path = typer.Option(None)) -> None:
    """看占比、缺口与复用候选。"""
    s = _settings(db)
    m = month or date.today().strftime("%Y-%m")
    try:
        datetime.strptime(m + "-01", "%Y-%m-%d")
    except ValueError:
        console.print(f"[red]月份格式不对：{m}，应该像 2026-11[/]")
        raise typer.Exit(code=2)
    p = plan(_store(s), m)
    console.print(f"支柱占比：{p.shares}")
    console.print(f"未来 7 天缺口：{len(p.gaps)} 天")
    for title, day in p.reuse:
        console.print(f"可复用：{title}（{day}）")
    for f in p.findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")


@app.command()
def weekly(
    start: str = typer.Option("", help="起始日期 YYYY-MM-DD，默认今天"),
    platform: str = typer.Option("xhs", help="xhs / dy / sph"),
    days: int = typer.Option(7, help="排几天"),
    out: Path = typer.Option(None, help="输出 Markdown；不填打印到终端"),
    db: Path = typer.Option(None),
) -> None:
    """一周选题表 + 每条开头三句，一次成文。"""
    s = _settings(db)
    try:
        d = date.fromisoformat(start) if start else date.today()
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    try:
        body = build_week(_store(s), d, platform, days)
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        console.print(f"[green]已写出[/] {out}（{len(body.splitlines())} 行）")
    else:
        console.print(body)


@app.command("stats")
def stats_cmd(db: Path = typer.Option(None)) -> None:
    """按支柱看播放量。"""
    store = _store(_settings(db))
    console.print(stats(store.list_posts(), store.list_pillars()))


@app.command()
def ideas(month: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """模型出选题（无 key 时只列库存）。"""
    s = _settings(db)
    store = _store(s)
    m = month or date.today().strftime("%Y-%m")
    llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model, PROMPT) if s.llm_enabled else None
    p, rows, findings = generate(store, s, m, llm=llm)
    body: list[str] = []
    for r in rows:
        line = f"- [{r.get('pillar')}] {r.get('title')}（未验证）"
        console.print(line)
        body.append(line)
    for f in findings:
        line = f"  {f.rule_id} -{f.penalty} {f.message}"
        console.print(line)
        body.append(line)
    if not rows:
        for i in store.list_ideas():
            line = f"- [{i.pillar}] {i.title}{'（已用）' if i.used else ''}"
            console.print(line)
            body.append(line)
    _notify(s, "\n".join(body))


@app.command("schedule")
def schedule_cmd(day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """把库存选题填进未来 7 天缺口。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    store = _store(s)
    p = plan(store, d.strftime("%Y-%m"), d)
    console.print(f"排入 {schedule(store, p, 7, d)} 条")


@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """四项体检。"""
    raise typer.Exit(code=doctor_main(_settings(db)))


@app.command()
def serve(port: int = typer.Option(None), db: Path = typer.Option(None)) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host="127.0.0.1", port=s.port)


if __name__ == "__main__":
    app()
