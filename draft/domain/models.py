"""领域对象：支柱、选题、已发内容、排期。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Pillar:
    id: int
    name: str
    target: float


@dataclass(frozen=True)
class Post:
    id: int
    title: str
    pillar: str
    published_on: date
    views: int


@dataclass(frozen=True)
class Idea:
    id: int
    title: str
    pillar: str
    used: bool = False
    verified: bool = False
    source: str = "manual"


@dataclass(frozen=True)
class Slot:
    id: int
    day: date
    pillar: str
    title: str


@dataclass
class Finding:
    rule_id: str
    message: str
    penalty: int
    target: str = ""


@dataclass
class Plan:
    month: str
    shares: dict[str, float] = field(default_factory=dict)
    reuse: list[tuple[str, date]] = field(default_factory=list)
    gaps: list[date] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def penalty_total(self) -> int:
        return sum(f.penalty for f in self.findings)
