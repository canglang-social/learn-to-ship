"""Vault resolution: recall's --today / --journal flags and directory --cards."""

from __future__ import annotations

from datetime import date

import pytest

from learn_to_ship import vault


@pytest.fixture
def fake_vault(tmp_path, monkeypatch):
    (tmp_path / "journals").mkdir()
    monkeypatch.setenv(vault.VAULT_PATH_ENV, str(tmp_path))
    return tmp_path


def _journal(fake_vault, name: str, text: str = "- q? 问？ #card #t #t/s #q/why\n\t- a. 答。\n"):
    f = fake_vault / "journals" / name
    f.write_text(text, encoding="utf-8")
    return f


def test_journal_path_accepts_both_date_separators(fake_vault):
    f = _journal(fake_vault, "2026_07_07.md")
    assert vault.journal_path("2026-07-07") == f
    assert vault.journal_path("2026_07_07") == f


def test_journal_path_defaults_to_today(fake_vault):
    f = _journal(fake_vault, f"{date.today():%Y_%m_%d}.md")
    assert vault.journal_path() == f


def test_journal_path_missing_journal_is_loud(fake_vault):
    with pytest.raises(ValueError, match="no journal for 2026-01-01"):
        vault.journal_path("2026-01-01")


def test_journal_path_rejects_a_non_date(fake_vault):
    with pytest.raises(ValueError, match="expected a date"):
        vault.journal_path("last tuesday")


def test_vault_path_unset_is_a_clear_error(monkeypatch):
    monkeypatch.delenv(vault.VAULT_PATH_ENV, raising=False)
    with pytest.raises(ValueError, match="LTS_VAULT_PATH is not set"):
        vault.vault_path()


def test_vault_path_must_be_a_directory(monkeypatch, tmp_path):
    f = tmp_path / "not-a-dir"
    f.write_text("x")
    monkeypatch.setenv(vault.VAULT_PATH_ENV, str(f))
    with pytest.raises(ValueError, match="not a directory"):
        vault.vault_path()


def test_card_files_takes_a_file_as_is(tmp_path):
    f = tmp_path / "cards.md"
    f.write_text("no cards here")
    assert vault.card_files(f) == [f]


def test_card_files_scans_a_directory_for_card_blocks(fake_vault):
    with_cards = _journal(fake_vault, "2026_07_01.md")
    _journal(fake_vault, "2026_07_02.md", text="- just a note, no cards\n")
    assert vault.card_files(fake_vault) == [with_cards]


def test_card_files_directory_without_cards_is_loud(tmp_path):
    (tmp_path / "note.md").write_text("nothing")
    with pytest.raises(ValueError, match="contains a #card block"):
        vault.card_files(tmp_path)


def test_card_files_missing_path_is_loud(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        vault.card_files(tmp_path / "nope.md")


# --- the triaged queue page (rank --queue) --------------------------------

# Mirrors the real page shape: an untasked header bullet, then LATER-marked
# items with route::/from:: property lines.
QUEUE_TEXT = """\
- Triaged learning topics waiting for a session — routes A–C only. Pull oldest first.
- LATER How big labs evaluate model capability — benchmarks and model cards #learn
  route:: C-material
  from:: [[2026-07-05]] "i want to learn Claude"
- LATER How to dev WITH Claude — API, tool use, agents #learn
  route:: B-practice
  note:: behind the one-topic lock ([[Learning/Incubation]] holds Route D)
- someday maybe a bare bullet without a task marker
"""


def test_parse_queue_takes_only_task_marked_bullets():
    items = vault.parse_queue(QUEUE_TEXT)
    assert len(items) == 2
    assert items[0].title.startswith("How big labs evaluate model capability")
    assert "#learn" not in items[0].title


def test_parse_queue_collects_tags_and_route():
    first, second = vault.parse_queue(QUEUE_TEXT)
    assert "learn" in first.tags and "c-material" in first.tags
    assert "b-practice" in second.tags


def test_parse_queue_ids_are_stable_slugs():
    first, second = vault.parse_queue(QUEUE_TEXT)
    assert first.id.startswith("how-big-labs-evaluate-model-capability")
    assert second.id.startswith("how-to-dev-with-claude")
    # Same input, same ids — determinism extends to the queue parser.
    assert [i.id for i in vault.parse_queue(QUEUE_TEXT)] == [first.id, second.id]


def test_queue_page_path_resolves_logseq_name_encoding(fake_vault, monkeypatch):
    (fake_vault / "pages").mkdir()
    page = fake_vault / "pages" / "Learning___Queue.md"
    page.write_text(QUEUE_TEXT, encoding="utf-8")
    assert vault.queue_page_path() == page  # default page name
    monkeypatch.setenv(vault.QUEUE_PAGE_ENV, "My/Other Queue")
    with pytest.raises(ValueError, match=r"\[\[My/Other Queue\]\] not found"):
        vault.queue_page_path()


def test_recall_all_sweeps_the_configured_vault(fake_vault):
    from argparse import Namespace

    from learn_to_ship.__main__ import _card_targets

    with_cards = _journal(fake_vault, "2026_07_01.md")
    _journal(fake_vault, "2026_07_02.md", text="- no cards here\n")
    targets = _card_targets(Namespace(today=False, journal=None, all=True, cards=None))
    assert targets == [with_cards]
