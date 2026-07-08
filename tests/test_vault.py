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
