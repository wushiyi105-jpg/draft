"""FastAPI + Jinja2：日历与选题。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..app.run import PROMPT, generate, plan, stats
from ..config import Settings

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Draft", version="1.0.0")
    store = store or SqliteStore(settings.db_path)
    llm = build_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model, PROMPT) if settings.llm_enabled else None

    def render(request: Request) -> HTMLResponse:
        today = date.today()
        p = plan(store, today.strftime("%Y-%m"), today)
        return TEMPLATES.TemplateResponse(
            request, "index.html",
            {"p": p, "today": today.isoformat(), "slots": store.list_slots(),
             "ideas": store.list_ideas(), "stats": stats(store.list_posts(), store.list_pillars()),
             "top": sorted(store.list_posts(), key=lambda x: x.views, reverse=True)[:4]},
        )

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return render(request)

    @app.get("/ideas.txt", response_class=PlainTextResponse)
    def ideas_text() -> PlainTextResponse:
        _, rows, findings = generate(store, settings, date.today().strftime("%Y-%m"), llm=llm)
        text = "\n".join(f"- [{r.get('pillar')}] {r.get('title')}（未验证）" for r in rows)
        if findings:
            text += "\n" + "\n".join(f.rule_id + " " + f.message for f in findings)
        return PlainTextResponse(text or "没有生成项", media_type="text/plain; charset=utf-8")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "posts": len(store.list_posts())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)
