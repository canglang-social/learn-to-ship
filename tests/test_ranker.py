"""Unit tests for the deterministic ranking core."""

from __future__ import annotations

from learn_to_ship.models import Gap, StudyItem
from learn_to_ship.ranker import rank

# Synthetic fixtures. Only `leverage` and `keywords` matter to these tests;
# `freq` and `level` are dummy placeholders (0.0 / "example") on purpose, so the
# fixture carries no real JD-frequency or self-assessment data.
GAPS = [
    Gap(4, "Cloud + CI/CD", 0.0, "example", 1, 1.00, ("cloud", "docker", "ci")),
    Gap(1, "Orchestration", 0.0, "example", 2, 0.80, ("langgraph", "agent")),
    Gap(3, "RAG", 0.0, "example", None, 0.05, ("rag", "retrieval")),
    Gap(7, "Fine-tuning", 0.0, "example", None, 0.00, ("lora",)),
]


def test_ranks_by_leverage_descending():
    items = [
        StudyItem("rag", "Improve retrieval", ("rag",)),
        StudyItem("cloud", "Deploy to cloud", ("cloud",)),
        StudyItem("agent", "Build a langgraph agent", ("agent",)),
    ]
    ranked = rank(items, GAPS)
    assert [r.item.id for r in ranked] == ["cloud", "agent", "rag"]
    assert ranked[0].gap.id == 4
    assert ranked[0].score == 1.00


def test_highest_leverage_gap_wins_on_multi_match():
    # Hits both cloud (1.00) and rag (0.05); the cited gap is the higher-leverage one.
    item = StudyItem("mix", "Deploy the rag service to cloud", ("cloud", "rag"))
    ranked = rank([item], GAPS)
    assert ranked[0].gap.id == 4


def test_unmatched_item_scores_zero_and_cites_no_gap():
    ranked = rank([StudyItem("x", "Bake bread", ("cooking",))], GAPS)
    assert ranked[0].score == 0.0
    assert ranked[0].gap is None
    assert "No JD gap" in ranked[0].rationale


def test_deterministic_and_stable_across_runs():
    items = [StudyItem(f"i{i}", "Deploy to cloud", ("cloud",)) for i in range(5)]
    first = [r.item.id for r in rank(items, GAPS)]
    second = [r.item.id for r in rank(items, GAPS)]
    # Identical scores → original order preserved, repeatably.
    assert first == second == ["i0", "i1", "i2", "i3", "i4"]
