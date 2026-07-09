"""The propose inbox — the ONE vault surface the agent may write (Q10)."""

from __future__ import annotations

import argparse

import pytest
import yaml

from learn_to_ship import inbox, propose
from learn_to_ship.__main__ import cmd_propose
from learn_to_ship.propose import Proposal, StubGapProposer

BLOCKS = [
    {
        "gap_id": 2,
        "priority": 2,
        "competency": "Data engineering & analytics",
        "freq": 0.55,
        "level": "partial",
        "proposals": [
            {
                "title": "Model a star schema for a toy shop",
                "tags": ["sql", "etl"],
                "route": "B-practice",
            }
        ],
    }
]


@pytest.fixture
def fake_vault(tmp_path, monkeypatch):
    (tmp_path / "pages").mkdir()
    monkeypatch.setenv("LTS_VAULT_PATH", str(tmp_path))
    return tmp_path


def test_first_write_creates_the_page_with_header(fake_vault):
    added, skipped, path = inbox.append_proposals(BLOCKS)
    assert (added, skipped) == (1, 0)
    assert path == fake_vault / "pages" / "Learning___inbox___propose.md"
    text = path.read_text()
    assert "Machine-appended inbox" in text  # the page explains itself
    assert "- Model a star schema for a toy shop" in text
    assert "route-hint:: B-practice" in text  # a HINT — never a real route::
    assert "route:: " not in text
    assert "LATER" not in text  # no task marker: pre-triage material
    assert "keywords:: sql, etl" in text
    assert "from:: propose · gap #2 Data engineering & analytics ·" in text


def test_rerun_is_deduplicated_and_append_only(fake_vault):
    inbox.append_proposals(BLOCKS)
    before = inbox.propose_inbox_path().read_text()
    added, skipped, _ = inbox.append_proposals(BLOCKS)
    assert (added, skipped) == (0, 1)
    assert inbox.propose_inbox_path().read_text() == before  # untouched

    # Same gap, NEW wording (an LLM re-run paraphrases): still skipped —
    # one batch per gap until the human triages or cancels it.
    paraphrase = [
        dict(
            BLOCKS[0],
            proposals=[{"title": "Ship an ETL job", "tags": ["etl"], "route": "B-practice"}],
        )
    ]
    added, skipped, _ = inbox.append_proposals(paraphrase)
    assert (added, skipped) == (0, 1)
    assert inbox.propose_inbox_path().read_text() == before

    # A different gap appends normally, and prior content stays byte-identical.
    other_gap = [
        dict(
            BLOCKS[0],
            priority=3,
            competency="Distributed systems",
            proposals=[{"title": "Ship an ETL job", "tags": ["etl"], "route": "B-practice"}],
        )
    ]
    added, skipped, _ = inbox.append_proposals(other_gap)
    assert (added, skipped) == (1, 0)
    text = inbox.propose_inbox_path().read_text()
    assert text.startswith(before)  # append-only


def test_page_name_env_override(fake_vault, monkeypatch):
    monkeypatch.setenv(inbox.PROPOSE_INBOX_ENV, "Learning/inbox/other")
    _, _, path = inbox.append_proposals(BLOCKS)
    assert path.name == "Learning___inbox___other.md"


def test_no_vault_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("LTS_VAULT_PATH", raising=False)
    with pytest.raises(ValueError, match="LTS_VAULT_PATH"):
        inbox.append_proposals(BLOCKS)


def test_cli_write_flag_appends_and_dedups_across_gaps(fake_vault, tmp_path, monkeypatch, capsys):
    # The stub returns the same title for every uncovered gap (4 of them with a
    # single flutter candidate) — the inbox must collapse that to one entry.
    stub = StubGapProposer(
        [Proposal(title="Build a warehouse demo", tags=("sql",), route="B-practice")]
    )
    monkeypatch.setattr(propose, "get_proposer", lambda: stub)
    lst = tmp_path / "one.yaml"
    lst.write_text(
        yaml.safe_dump({"candidates": [{"id": "a", "title": "Flutter app", "tags": ["flutter"]}]})
    )
    cmd_propose(argparse.Namespace(candidates=lst, queue=False, json=False, write=True))
    out = capsys.readouterr().out
    assert "Appended 1 draft(s) to [[Learning/inbox/propose]] (3 duplicate(s) skipped)." in out
    text = inbox.propose_inbox_path().read_text()
    assert text.count("- Build a warehouse demo") == 1
    # And only the propose-inbox page exists — no other vault file was touched.
    assert [p.name for p in (fake_vault / "pages").iterdir()] == ["Learning___inbox___propose.md"]
