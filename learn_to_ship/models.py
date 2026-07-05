"""Typed data shapes shared across the agent.

Kept as plain dataclasses (not the graph state) so the pure ranker and the MCP
corpus layer can be unit-tested without importing LangGraph.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Gap:
    """One JD competency and how much closing it unblocks the job hunt."""

    id: int
    competency: str
    freq: float
    level: str
    priority: int | None
    leverage: float
    keywords: tuple[str, ...]

    @classmethod
    def from_dict(cls, d: dict) -> "Gap":
        return cls(
            id=int(d["id"]),
            competency=str(d["competency"]),
            freq=float(d["freq"]),
            level=str(d["level"]),
            priority=None if d.get("priority") is None else int(d["priority"]),
            leverage=float(d["leverage"]),
            keywords=tuple(str(k).lower() for k in d.get("keywords", [])),
        )


@dataclass(frozen=True)
class StudyItem:
    """A candidate the learner might study next. Felix owns capture; the agent
    picks up after."""

    id: str
    title: str
    tags: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, d: dict) -> "StudyItem":
        return cls(
            id=str(d["id"]),
            title=str(d["title"]),
            tags=tuple(str(t).lower() for t in d.get("tags", [])),
        )


@dataclass(frozen=True)
class RankedItem:
    """A study item scored and tied to the gap it unblocks."""

    item: StudyItem
    score: float
    gap: Gap | None
    rationale: str

    def to_dict(self) -> dict:
        return {
            "id": self.item.id,
            "title": self.item.title,
            "score": round(self.score, 4),
            "gap_id": None if self.gap is None else self.gap.id,
            "gap": None if self.gap is None else self.gap.competency,
            "gap_priority": None if self.gap is None else self.gap.priority,
            "rationale": self.rationale,
        }
