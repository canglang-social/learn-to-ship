"""Locate card files in the Logseq vault.

Read-path convenience for the recall CLI: turn "today" or a date into the
vault journal file to check (journals/yyyy_MM_dd.md), and expand a directory
into the .md files that actually contain cards. This module only ever reads —
capture and authoring stay human-owned (spec.md non-goal).
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

from .logseq import has_card

# Env override, sibling to LTS_CORPUS_PATH: point at the Logseq vault root
# (the folder that contains journals/). Set it in .env for daily use.
VAULT_PATH_ENV = "LTS_VAULT_PATH"

_DATE = re.compile(r"(\d{4})[-_](\d{1,2})[-_](\d{1,2})")


def vault_path() -> Path:
    """The vault root from LTS_VAULT_PATH; raises ValueError if unusable."""
    raw = os.environ.get(VAULT_PATH_ENV)
    if not raw:
        raise ValueError(
            f"{VAULT_PATH_ENV} is not set — point it at your Logseq vault "
            "(the folder that contains journals/), e.g. in .env"
        )
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise ValueError(f"{VAULT_PATH_ENV}={raw} is not a directory")
    return path


def journal_path(day: str | None = None) -> Path:
    """The vault journal for a date ('2026-07-08' or '2026_07_08'; None = today).

    Logseq names journal pages yyyy_MM_dd.md; this maps a calendar date to that
    file and insists it exists — "no journal today" should say so, not silently
    review zero cards.
    """
    if day is None:
        d = date.today()
    else:
        m = _DATE.fullmatch(day.strip())
        if not m:
            raise ValueError(f"expected a date like 2026-07-08, got {day!r}")
        d = date(*map(int, m.groups()))
    path = vault_path() / "journals" / f"{d:%Y_%m_%d}.md"
    if not path.is_file():
        raise ValueError(f"no journal for {d:%Y-%m-%d} at {path}")
    return path


def card_files(target: Path) -> list[Path]:
    """Expand a --cards argument into concrete files.

    A file is taken as-is; a directory becomes every .md beneath it that
    contains at least one #card block (so pointing at journals/ — or the whole
    vault — just works).
    """
    if target.is_file():
        return [target]
    if target.is_dir():
        found = [p for p in sorted(target.rglob("*.md")) if has_card(p.read_text(encoding="utf-8"))]
        if not found:
            raise ValueError(f"no .md file under {target} contains a #card block")
        return found
    raise ValueError(f"{target} does not exist")
