"""SQLite：pillars / ideas / posts / slots。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Boolean, Date, Integer, String, inspect, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from ...domain.models import Idea, Pillar, Post, Slot
from .base import Base, make_engine, make_session


class PillarRow(Base):
    __tablename__ = "pillars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    target: Mapped[float] = mapped_column(default=0.33)


class PostRow(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    pillar: Mapped[str] = mapped_column(String(40))
    published_on: Mapped[date] = mapped_column(Date)
    views: Mapped[int] = mapped_column(Integer, default=0)


class IdeaRow(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    pillar: Mapped[str] = mapped_column(String(40))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(20), default="manual")


class SlotRow(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date)
    pillar: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(160), default="")


def _upgrade_schema(engine) -> None:
    root = next(p for p in Path(__file__).resolve().parents if (p / "alembic.ini").exists())
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{engine.url.database}")
    command.upgrade(cfg, "head")


class SqliteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.engine = make_engine(self.path)
        self.session: sessionmaker[Session] = make_session(self.engine)
        self.init_schema()

    def init_schema(self) -> None:
        _upgrade_schema(self.engine)

    def schema_ok(self) -> bool:
        return {"pillars", "ideas", "posts", "slots"} <= set(inspect(self.engine).get_table_names())

    def summary(self) -> str:
        return f"{len(self.list_posts())} 条已发、{len(self.list_ideas())} 个选题"

    def add_pillar(self, name: str, target: float) -> int:
        with self.session() as s:
            row = PillarRow(name=name, target=target)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_pillars(self) -> list[Pillar]:
        with self.session() as s:
            rows = s.scalars(select(PillarRow)).all()
        return [Pillar(r.id, r.name, float(r.target)) for r in rows]

    def add_post(self, title: str, pillar: str, published_on: date, views: int) -> int:
        if views < 0:
            raise ValueError("播放量不能为负")
        with self.session() as s:
            row = PostRow(title=title, pillar=pillar, published_on=published_on, views=views)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_posts(self) -> list[Post]:
        with self.session() as s:
            rows = s.scalars(select(PostRow)).all()
        return [Post(r.id, r.title, r.pillar, r.published_on, r.views) for r in rows]

    def add_idea(self, title: str, pillar: str, used: bool = False, verified: bool = False, source: str = "manual") -> int:
        with self.session() as s:
            row = IdeaRow(title=title, pillar=pillar, used=used, verified=verified, source=source)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_ideas(self) -> list[Idea]:
        with self.session() as s:
            rows = s.scalars(select(IdeaRow)).all()
        return [Idea(r.id, r.title, r.pillar, r.used, r.verified, r.source) for r in rows]

    def add_slot(self, day: date, pillar: str, title: str = "") -> int:
        with self.session() as s:
            row = SlotRow(day=day, pillar=pillar, title=title)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_slots(self) -> list[Slot]:
        with self.session() as s:
            rows = s.scalars(select(SlotRow).order_by(SlotRow.day)).all()
        return [Slot(r.id, r.day, r.pillar, r.title) for r in rows]

