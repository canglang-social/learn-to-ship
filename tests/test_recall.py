"""The recall graph combines deterministic format lint + the (stubbed) LLM check.

Hermetic: the Claude checker is monkeypatched with StubCardChecker, so no API key
and no network are needed — CI stays green.
"""

from __future__ import annotations

import learn_to_ship.recall as recall
from learn_to_ship.models import CardIssue
from learn_to_ship.recall_graph import build_recall_graph

CARDS = (
    "- Good question? 好问题？ #card #x #x/y #q/why\n"
    "\t- Good answer. 好答案。\n"
    "- English only? #card #x #x/y #q/how\n"  # missing 中文 → format error
    "\t- English only.\n"
)


def test_reviews_merge_format_and_content_issues(monkeypatch):
    stub = recall.StubCardChecker(
        [CardIssue(kind="complexity", severity="warn", message="two ideas — split it")]
    )
    monkeypatch.setattr(recall, "get_checker", lambda: stub)

    reviews = build_recall_graph().invoke({"cards_text": CARDS, "material": None})["reviews"]
    assert len(reviews) == 2

    # Every card gets the stubbed content issue...
    for r in reviews:
        assert any(i["kind"] == "complexity" for i in r["issues"])
    # ...and the second card also gets deterministic format errors (missing 中文).
    assert reviews[0]["verdict"] == "needs_work"  # (from the stubbed complexity warn)
    assert any(i["kind"] == "format" for i in reviews[1]["issues"])


def test_clean_card_with_empty_checker_is_ok(monkeypatch):
    monkeypatch.setattr(recall, "get_checker", lambda: recall.StubCardChecker([]))
    good = "- Q? 问？ #card #x #x/y #q/why\n\t- A. 答。\n"
    reviews = build_recall_graph().invoke({"cards_text": good, "material": None})["reviews"]
    assert reviews[0]["verdict"] == "ok"
    assert reviews[0]["issues"] == []
