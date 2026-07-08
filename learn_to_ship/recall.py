"""The card checker — an injectable LLM seam.

You author the cards; the checker only critiques them, mirroring v0's stance
(agent advises, human decides). It flags exactly two things, and never rewrites:

- complexity  — does the card cram more than one idea / is the answer too compound?
- correctness — is the answer accurate and consistent with the source material?

Format problems (missing 中文, bad tags) are the deterministic linter's job
(logseq.lint_format), not the LLM's. `get_checker()` returns the LLM checker
when a key is configured (provider chosen in llm.py — DeepSeek or Anthropic);
tests monkeypatch it with `StubCardChecker` so CI stays hermetic.
"""

from __future__ import annotations

from typing import Protocol

from .llm import get_chat_model, has_llm_key
from .models import Card, CardIssue

_SYSTEM = """You review spaced-repetition flashcards that a learner wrote themselves.
You do NOT rewrite, author, or reword cards — the learner phrases them on purpose,
because phrasing the card is the studying. You only flag problems so they can fix them.

Check exactly two things, nothing else:
1. complexity — does the front test more than one idea, or is the back too compound
   to pull from memory in one go? Spaced repetition wants one atomic idea per card.
   If so, say what to split out. severity "warn".
2. correctness — is the answer accurate? If source material is provided, is the
   answer supported by it (not contradicted, not unsupported)? severity "error".

Do NOT comment on formatting, tags, bilingual layout, or wording style — those are
handled elsewhere. If the card is one atomic, correct idea, return no issues."""


class CardChecker(Protocol):
    def check(self, card: Card, material: str | None) -> list[CardIssue]: ...


class StubCardChecker:
    """Deterministic canned checker for hermetic tests."""

    def __init__(self, issues: list[CardIssue] | None = None) -> None:
        self._issues = issues or []

    def check(self, card: Card, material: str | None) -> list[CardIssue]:
        return list(self._issues)


class LLMCardChecker:
    """Content review via the configured LLM (llm.py), structured output."""

    def __init__(self) -> None:
        self._runnable = None  # built lazily so importing needs no API key

    def _get_runnable(self):
        if self._runnable is None:
            from typing import Literal

            from pydantic import BaseModel, Field

            class _Issue(BaseModel):
                kind: Literal["complexity", "correctness"]
                severity: Literal["warn", "error"]
                message: str = Field(
                    description="one sentence; what is wrong and, for complexity, what to split"
                )

            class _Result(BaseModel):
                issues: list[_Issue] = Field(default_factory=list)

            self._runnable = get_chat_model().with_structured_output(_Result)
        return self._runnable

    def check(self, card: Card, material: str | None) -> list[CardIssue]:
        human = f"Card front: {card.front}\nCard back: {card.back}\n"
        if material:
            human += f"\nSource material the card should be consistent with:\n{material}\n"

        result = self._get_runnable().invoke([("system", _SYSTEM), ("human", human)])
        return [
            CardIssue(kind=i.kind, severity=i.severity, message=i.message) for i in result.issues
        ]


def get_checker() -> CardChecker:
    """Factory — the LLM checker when a key is configured, else a no-op so the
    deterministic format lint still runs. Tests monkeypatch this."""
    return LLMCardChecker() if has_llm_key() else StubCardChecker([])
