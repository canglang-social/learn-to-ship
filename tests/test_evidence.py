"""Usage-evidence capture: the JSONL trail, the summary, and the CLI hooks.

The autouse fixture in conftest.py points LTS_EVIDENCE_PATH at a per-test tmp
file, so every test here reads/writes a throwaway trail.
"""

from __future__ import annotations

import argparse

from learn_to_ship import evidence
from learn_to_ship.__main__ import DEFAULT_CANDIDATES, cmd_evidence, cmd_rank


def test_log_and_read_roundtrip():
    evidence.log_event("rank", candidates=3, top=["a", "b"])
    evidence.log_event("output", item="a", output="https://example.com")
    events = evidence.read_events()
    assert [e["kind"] for e in events] == ["rank", "output"]
    assert events[0]["top"] == ["a", "b"]
    assert all("ts" in e for e in events)


def test_read_skips_corrupt_lines():
    evidence.log_event("rank", candidates=1, top=["a"])
    path = evidence.evidence_path()
    path.write_text(path.read_text() + "not json\n", encoding="utf-8")
    evidence.log_event("output", item="a", output="x")
    assert [e["kind"] for e in evidence.read_events()] == ["rank", "output"]


def test_default_path_when_env_unset(monkeypatch):
    monkeypatch.delenv(evidence.EVIDENCE_PATH_ENV, raising=False)
    assert evidence.evidence_path() == evidence.DEFAULT_EVIDENCE_PATH


def test_summarize_empty_trail():
    assert "No usage evidence yet" in evidence.summarize([])


def test_summarize_counts_and_nudges():
    events = [
        {"ts": "2026-07-08T09:00:00", "kind": "rank", "candidates": 8, "top": ["a"]},
        {"ts": "2026-07-08T10:00:00", "kind": "recall", "source": "j.md", "cards": 3, "ok": 2},
        {"ts": "2026-07-08T11:00:00", "kind": "output", "item": "a", "output": "https://x"},
    ]
    text = evidence.summarize(events)
    assert "rank runs: 1" in text
    assert "3 card(s) checked, 2 ok" in text
    assert "a → https://x" in text
    assert "consider updating their levels" in text


def test_cli_records_an_output(capsys):
    cmd_evidence(argparse.Namespace(item="k8s-deploy", output="https://x", note="v1"))
    (event,) = evidence.read_events()
    assert event["kind"] == "output" and event["item"] == "k8s-deploy" and event["note"] == "v1"
    assert "Recorded" in capsys.readouterr().out


def test_cli_show_mode_prints_the_trail(capsys):
    evidence.log_event("output", item="a", output="https://x")
    cmd_evidence(argparse.Namespace(item=None, output=None, note=None))
    out = capsys.readouterr().out
    assert "Usage evidence" in out and "a → https://x" in out


def test_rank_cli_logs_a_rank_event(capsys):
    cmd_rank(argparse.Namespace(candidates=DEFAULT_CANDIDATES, queue=False, json=True))
    (event,) = evidence.read_events()
    assert event["kind"] == "rank"
    assert event["candidates"] == 8
    assert len(event["top"]) == 3
    assert event["source"].endswith("study-candidates.yaml")
