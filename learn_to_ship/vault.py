"""Read from the Logseq vault: card files, and the triaged study queue.

Read-path convenience for the CLI: turn "today" or a date into the vault
journal file recall should check, expand a directory into the .md files that
contain cards, and parse the human-triaged queue page into study candidates
for rank. This module only ever reads — capture, triage, and authoring stay
human-owned (spec.md non-goal).
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

from .logseq import has_card
from .models import StudyItem

# Env override, sibling to LTS_CORPUS_PATH: point at the Logseq vault root
# (the folder that contains journals/). Set it in .env for daily use.
VAULT_PATH_ENV = "LTS_VAULT_PATH"

# The Logseq page holding the human-triaged study queue ("Learning/Queue").
# The human triages #inbox into it; rank --queue only reads the result.
QUEUE_PAGE_ENV = "LTS_QUEUE_PAGE"
DEFAULT_QUEUE_PAGE = "Learning/Queue"

_DATE = re.compile(r"(\d{4})[-_](\d{1,2})[-_](\d{1,2})")

# Queue items are task-marked top-level bullets ("- LATER <title> #tag …");
# the page's untasked header/description bullets are not items.
_TASK_MARKER = re.compile(r"^(LATER|TODO|NOW|DOING)\s+")
_HASHTAG = re.compile(r"(?<!\S)#([\w/-]+)")
_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
_ROUTE_PROP = re.compile(r"^\s+route::\s*(\S+)")
_SLUG = re.compile(r"[^a-z0-9]+")


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


def queue_page_path() -> Path:
    """The triaged-queue page file (LTS_QUEUE_PAGE, default Learning/Queue).

    Logseq encodes '/' in page names as '___' in filenames, so the page
    [[Learning/Queue]] lives at pages/Learning___Queue.md.
    """
    name = os.environ.get(QUEUE_PAGE_ENV, DEFAULT_QUEUE_PAGE)
    path = vault_path() / "pages" / f"{name.replace('/', '___')}.md"
    if not path.is_file():
        raise ValueError(f"queue page [[{name}]] not found at {path} (set {QUEUE_PAGE_ENV})")
    return path


def _slug(title: str, taken: set[str]) -> str:
    base = _SLUG.sub("-", title.lower()).strip("-")[:48].rstrip("-") or "item"
    slug, n = base, 1
    while slug in taken:
        n += 1
        slug = f"{base}-{n}"
    return slug


def parse_queue(text: str) -> list[StudyItem]:
    """Parse the triaged queue page into study candidates.

    An item is a top-level bullet with a task marker (LATER/TODO/NOW/DOING);
    untasked bullets are page prose. The title keeps its wording (wiki-link
    brackets unwrapped); tags collect inline #hashtags, [[page]] refs, and the
    item's `route::` property value, all lowercased for the keyword matcher.
    """
    items: list[StudyItem] = []
    taken: set[str] = set()
    pending: dict | None = None

    def flush() -> None:
        nonlocal pending
        if pending is None:
            return
        slug = _slug(pending["title"], taken)
        taken.add(slug)
        items.append(StudyItem(id=slug, title=pending["title"], tags=tuple(pending["tags"])))
        pending = None

    for line in text.splitlines():
        if line.startswith("- "):
            flush()
            m = _TASK_MARKER.match(line[2:].strip())
            if not m:
                continue
            body = line[2:].strip()[m.end() :].strip()
            tags = [t.lower() for t in _HASHTAG.findall(body)]
            tags += [w.lower() for w in _WIKILINK.findall(body)]
            title = _HASHTAG.sub("", _WIKILINK.sub(r"\1", body)).strip(" -—")
            pending = {"title": title, "tags": tags}
        elif pending is not None and (rm := _ROUTE_PROP.match(line)):
            pending["tags"].append(rm.group(1).lower())
    flush()
    return items


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
