"""The recall-card-checker graph.

One node, `card_reviewer`: parse the human-authored cards, run the deterministic
format lint + the LLM content check on each, return per-card reviews. Compiled as
`recall_graph` for langgraph.json. Thin, like graph.py.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from . import recall
from .logseq import lint_format, parse_cards
from .models import CardReview


class RecallState(TypedDict, total=False):
    cards_text: Annotated[str, "your hand-written Logseq #card blocks"]
    material: Annotated[str | None, "optional source to check correctness against"]
    reviews: Annotated[list[dict], "per-card format + content review"]


def card_reviewer(state: RecallState) -> RecallState:
    """Review each authored card: deterministic format lint + LLM content check."""
    cards = parse_cards(state.get("cards_text", ""))
    material = state.get("material")
    checker = recall.get_checker()  # module-level lookup so tests can monkeypatch

    reviews = []
    for card in cards:
        issues = (*lint_format(card), *checker.check(card, material))
        reviews.append(CardReview(card=card, issues=tuple(issues)).to_dict())
    return {"reviews": reviews}


def build_recall_graph():
    builder = StateGraph(RecallState)
    builder.add_node("card_reviewer", card_reviewer)
    builder.add_edge(START, "card_reviewer")
    builder.add_edge("card_reviewer", END)
    return builder.compile()


recall_graph = build_recall_graph()
