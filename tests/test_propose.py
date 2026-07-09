"""The gap-proposer graph and CLI (Q7 stage 2) — hermetic via the stub seam."""

from __future__ import annotations

import argparse

import pytest
import yaml

from learn_to_ship import evidence, propose
from learn_to_ship.__main__ import cmd_propose
from learn_to_ship.propose import Proposal, StubGapProposer
from learn_to_ship.propose_graph import build_propose_graph
from learn_to_ship.models import StudyItem


@pytest.fixture
def stub_proposer(monkeypatch):
    stub = StubGapProposer(
        [
            Proposal(
                title="Model a star schema for a toy shop", tags=("sql", "etl"), route="B-practice"
            )
        ]
    )
    monkeypatch.setattr(propose, "get_proposer", lambda: stub)
    return stub


async def test_graph_drafts_only_for_uncovered_gaps(stub_proposer):
    # One candidate covers stub gap #1 → drafts appear for priorities 2–5 only.
    candidates = [StudyItem("a", "Ship a Flutter app", ("flutter",))]
    result = await build_propose_graph().ainvoke({"candidates": candidates})
    blocks = result["proposals"]
    assert [b["priority"] for b in blocks] == [2, 3, 4, 5]
    assert all(len(b["proposals"]) == 1 for b in blocks)
    assert blocks[0]["proposals"][0]["route"] == "B-practice"


async def test_graph_is_quiet_when_the_ladder_is_covered(stub_proposer):
    candidates = [
        StudyItem("m", "Flutter app", ("flutter",)),
        StudyItem("d", "ETL job", ("etl",)),
        StudyItem("s", "OAuth login", ("oauth",)),
        StudyItem("w", "Write a tutorial", ("writing",)),
        StudyItem("b", "Worker queue", ("queue",)),
    ]
    result = await build_propose_graph().ainvoke({"candidates": candidates})
    assert result["proposals"] == []


def test_cli_prints_paste_ready_queue_bullets(stub_proposer, tmp_path, capsys):
    lst = tmp_path / "one.yaml"
    lst.write_text(
        yaml.safe_dump({"candidates": [{"id": "a", "title": "Flutter app", "tags": ["flutter"]}]})
    )
    cmd_propose(argparse.Namespace(candidates=lst, queue=False, json=False, write=False))
    out = capsys.readouterr().out
    assert "- Model a star schema for a toy shop" in out
    assert "route-hint:: B-practice" in out  # pre-triage: a hint, not a route
    assert "LATER" not in out
    assert "nothing reaches the queue except by your hand" in out
    # And the run left a usage-evidence event behind.
    (event,) = [e for e in evidence.read_events() if e["kind"] == "propose"]
    assert event["gaps"] == 4 and event["drafts"] == 4


def test_cli_no_key_still_reports_uncovered(monkeypatch, tmp_path, capsys):
    # Default proposer with no key = empty stub → coverage prints, no drafts.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    lst = tmp_path / "one.yaml"
    lst.write_text(
        yaml.safe_dump({"candidates": [{"id": "a", "title": "Flutter app", "tags": ["flutter"]}]})
    )
    cmd_propose(argparse.Namespace(candidates=lst, queue=False, json=False, write=False))
    out = capsys.readouterr().out
    assert "no LLM key" in out
    assert "Gap #2" in out and "(no drafts)" in out
