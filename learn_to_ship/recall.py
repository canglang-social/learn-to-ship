"""The card checker — an injectable LLM seam.

You author the cards; the checker only critiques them, mirroring v0's stance
(agent advises, human decides). It flags exactly two things, and never rewrites:

- complexity  — does the card cram more than one idea / is the answer too compound?
- correctness — is the answer accurate and consistent with the source material?

Format problems (missing 中文, bad tags) are the deterministic linter's job
(logseq.lint_format), not the LLM's. `get_checker()` returns the Claude checker
by default; tests monkeypatch it with `StubCardChecker` so CI stays hermetic.
"""

from __future__ import annotations

from typing import Protocol

import os

from .models import Card, CardIssue

# Sonnet 5: capable enough to judge atomicity + correctness, cheap enough to run
# often. Note: it rejects a non-default `temperature` (400), so we don't set one.
_MODEL = "claude-sonnet-5"

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


class ClaudeCardChecker:
    """Content review via Claude (langchain-anthropic), structured output."""

    def __init__(self, model: str = _MODEL) -> None:
        self._model = model
        self._runnable = None  # built lazily so importing needs no API key

    def _get_runnable(self):
        if self._runnable is None:
            from langchain_anthropic import ChatAnthropic
            from pydantic import BaseModel, Field

            class _Issue(BaseModel):
                kind: str = Field(description="'complexity' or 'correctness'")
                severity: str = Field(description="'warn' or 'error'")
                message: str = Field(
                    description="one sentence; what is wrong and, for complexity, what to split"
                )

            class _Result(BaseModel):
                issues: list[_Issue] = Field(default_factory=list)

            # No temperature — Sonnet 5 rejects a non-default value.
            llm = ChatAnthropic(model=self._model)
            self._runnable = llm.with_structured_output(_Result)
        return self._runnable

    def check(self, card: Card, material: str | None) -> list[CardIssue]:
        human = (
            f"Front (EN): {card.front_en}\nFront (中文): {card.front_zh}\n"
            f"Back (EN): {card.back_en}\nBack (中文): {card.back_zh}\n"
        )
        if material:
            human += f"\nSource material the card should be consistent with:\n{material}\n"

        result = self._get_runnable().invoke([("system", _SYSTEM), ("human", human)])
        return [
            CardIssue(kind=i.kind, severity=i.severity, message=i.message) for i in result.issues
        ]


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_checker() -> CardChecker:
    """Factory — the Claude checker when a key is present, else a no-op so the
    deterministic format lint still runs. Tests monkeypatch this."""
    return ClaudeCardChecker() if has_api_key() else StubCardChecker([])
