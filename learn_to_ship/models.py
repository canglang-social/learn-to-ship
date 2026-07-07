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


# --- v1: recall-card checker --------------------------------------------------
# You author the cards (phrasing them is the studying); learn-to-ship only checks
# them. A card is a Logseq #card block with a bilingual front/back.

QTYPES = ("why", "how", "apply")


@dataclass(frozen=True)
class Card:
    """One human-authored flashcard, parsed from a Logseq #card block.

    front/back are the whole bilingual strings as written (EN + 中文 together).
    We deliberately do NOT split them into language halves — the vault pairs key
    terms inline as `term (中文)`, which no split heuristic survives, and nothing
    downstream needs the halves (the lint checks that both scripts are present;
    Claude reads bilingual text directly).
    """

    front: str
    back: str
    topic: str  # broad slug, e.g. "agent-kit"
    subtopic: str  # hierarchical slug, e.g. "profile-delivery"
    qtype: str  # one of QTYPES
    raw: str  # the original block text, for error reporting

    @property
    def tags(self) -> str:
        return f"#card #{self.topic} #{self.topic}/{self.subtopic} #q/{self.qtype}"


@dataclass(frozen=True)
class CardIssue:
    """One problem found with a card. kind = format | complexity | correctness."""

    kind: str
    severity: str  # "warn" | "error"
    message: str

    def to_dict(self) -> dict:
        return {"kind": self.kind, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class CardReview:
    """A card plus the issues found in it."""

    card: Card
    issues: tuple[CardIssue, ...]

    @property
    def verdict(self) -> str:
        return "ok" if not self.issues else "needs_work"

    def to_dict(self) -> dict:
        return {
            "front": self.card.front,
            "verdict": self.verdict,
            "issues": [i.to_dict() for i in self.issues],
        }
