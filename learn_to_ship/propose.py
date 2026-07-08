"""Gap→study-item proposals — the second LLM seam (QUESTIONS.md Q7, stage 2).

For priority gaps the study list is silent about, draft candidate study items
the human can triage onto their queue page. The agent proposes text in the
terminal only — it never writes to the vault, and choosing stays human.
Proposing *directions* is the product's founding job (advise at entry), which
is why this is allowed while card generation never is: phrasing a card is the
studying; picking what to study is what the tool is for.

Mirrors recall.py: `get_proposer()` returns the Claude proposer when a key is
present, else an empty stub so the coverage report still prints; tests
monkeypatch it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Gap
from .recall import has_api_key

# Same model choice as the card checker: capable enough, cheap enough to run
# often, and it rejects a non-default temperature — so none is set.
_MODEL = "claude-sonnet-5"

_SYSTEM = """You draft study-item candidates for a learner's personal queue.
The learner studies by SHIPPING OUTPUTS: every item must be a concrete thing to
build, deploy, write, or measure — never "read about X" or "learn Y".

Rules:
- Propose 2–3 items for the ONE gap given. Each fits roughly a week of
  evenings and produces a showable artifact.
- Do NOT duplicate or lightly rephrase the existing queue titles provided.
- title: one line, imperative, specific (name the tool/tech where possible).
- tags: 3–5 lowercase keywords drawn from the gap's own vocabulary.
- route: 'B-practice' for build/apply items, 'C-material' for
  work-through-a-source items (the learner's routing convention)."""


@dataclass(frozen=True)
class Proposal:
    """One drafted study item, shaped like a queue entry."""

    title: str
    tags: tuple[str, ...]
    route: str


class GapProposer(Protocol):
    def propose(self, gap: Gap, existing_titles: list[str]) -> list[Proposal]: ...


class StubGapProposer:
    """Canned proposer for hermetic tests and the no-key degrade path."""

    def __init__(self, proposals: list[Proposal] | None = None) -> None:
        self._proposals = proposals or []

    def propose(self, gap: Gap, existing_titles: list[str]) -> list[Proposal]:
        return list(self._proposals)


class ClaudeGapProposer:
    """Drafts via Claude (langchain-anthropic), structured output."""

    def __init__(self, model: str = _MODEL) -> None:
        self._model = model
        self._runnable = None  # built lazily so importing needs no API key

    def _get_runnable(self):
        if self._runnable is None:
            from langchain_anthropic import ChatAnthropic
            from pydantic import BaseModel, Field

            class _Item(BaseModel):
                title: str = Field(description="one imperative line naming a shippable output")
                tags: list[str] = Field(description="3-5 lowercase keywords from the gap")
                route: str = Field(
                    description="'B-practice' (build/apply) or 'C-material' (work through a source)"
                )

            class _Result(BaseModel):
                items: list[_Item] = Field(description="2-3 proposed study items")

            llm = ChatAnthropic(model=self._model)
            self._runnable = llm.with_structured_output(_Result)
        return self._runnable

    def propose(self, gap: Gap, existing_titles: list[str]) -> list[Proposal]:
        pct = round(gap.freq * 100)
        human = (
            f"Gap to close: {gap.competency}\n"
            f"Asked in ~{pct}% of JDs; the learner's current level: '{gap.level}'.\n"
            f"Gap vocabulary: {', '.join(gap.keywords)}\n\n"
            "Existing queue titles (do not duplicate):\n"
            + "\n".join(f"- {t}" for t in existing_titles)
        )
        result = self._get_runnable().invoke([("system", _SYSTEM), ("human", human)])
        return [
            Proposal(title=i.title, tags=tuple(t.lower() for t in i.tags), route=i.route)
            for i in result.items
        ]


def get_proposer() -> GapProposer:
    """Claude when a key is present, else an empty stub (coverage still prints)."""
    return ClaudeGapProposer() if has_api_key() else StubGapProposer()
