"""The eval harness CI gates on.

Runs the full compiled graph (MCP corpus fetch + ranking) against the golden
cases and asserts the exact ranked order plus the acceptance-criteria invariants.
A ranking regression makes `expected_order` mismatch and fails the build.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learn_to_ship.corpus import load_gaps
from learn_to_ship.graph import build_graph
from learn_to_ship.models import StudyItem

CASES = yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "evals" / "cases.yaml").read_text()
)


async def _run() -> list:
    graph = build_graph()
    candidates = [StudyItem.from_dict(c) for c in CASES["candidates"]]
    result = await graph.ainvoke({"candidates": candidates})
    return result["ranked"]


@pytest.mark.asyncio
async def test_ranking_matches_golden_order():
    ranked = await _run()
    assert [r["id"] for r in ranked] == CASES["expected_order"]


@pytest.mark.asyncio
async def test_every_item_cites_a_real_gap_or_none():
    ranked = await _run()
    valid_ids = {g.id for g in load_gaps()}
    gap_by_id = {g.id: g for g in load_gaps()}
    for r in ranked:
        if r["gap_id"] is not None:
            assert r["gap_id"] in valid_ids
            # Acceptance criterion: a cited gap is named in the rationale.
            assert gap_by_id[r["gap_id"]].competency.split()[0] in r["rationale"]


@pytest.mark.asyncio
async def test_top_pick_unblocks_the_number_one_gap():
    ranked = await _run()
    assert ranked[0]["gap_priority"] == 1


@pytest.mark.asyncio
async def test_scores_are_monotonically_non_increasing():
    ranked = await _run()
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_run_is_deterministic():
    assert [r["id"] for r in await _run()] == [r["id"] for r in await _run()]
