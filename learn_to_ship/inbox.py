"""The ONE vault surface the agent may write: the propose inbox.

Everything else in the vault stays read-only forever (docs/LEARNING-LOOP.md;
spec.md non-goals). `propose --write` appends drafts here as PRE-TRIAGE
material — plain bullets with a `route-hint::`, never a task marker or a real
`route::`, because routing is triage and triage is human (QUESTIONS.md Q10).

Contract: append-only (existing lines are never edited or deleted), ONE batch
per gap (a gap whose drafts already await triage is skipped — LLM re-runs
paraphrase rather than repeat, so title-dedup alone can't stop pile-up),
duplicate titles are skipped, the page is created with a header explaining
itself, and no other page can be written through this module.
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

from .vault import vault_path

PROPOSE_INBOX_ENV = "LTS_PROPOSE_INBOX_PAGE"
DEFAULT_PROPOSE_INBOX = "Learning/inbox/propose"

_HEADER = (
    "- Machine-appended inbox — drafts from `propose --write` for uncovered JD\n"
    "  gaps. Triage like any inbox: pick a route (A–D) or mark CANCELED. These\n"
    "  are suggestions, not capture — the agent only appends here; it never\n"
    "  edits, deletes, or touches any other page.\n"
)


def propose_inbox_path() -> Path:
    """The propose-inbox page file (LTS_PROPOSE_INBOX_PAGE, Logseq /→___)."""
    name = os.environ.get(PROPOSE_INBOX_ENV, DEFAULT_PROPOSE_INBOX)
    return vault_path() / "pages" / f"{name.replace('/', '___')}.md"


def _existing_titles(text: str) -> set[str]:
    return {line[2:].strip() for line in text.splitlines() if line.startswith("- ")}


_GAP_MARK = re.compile(r"from:: propose · gap #(\d+) ")


def _gaps_awaiting_triage(text: str) -> set[int]:
    return {int(m) for m in _GAP_MARK.findall(text)}


def append_proposals(blocks: list[dict]) -> tuple[int, int, Path]:
    """Append drafts as pre-triage entries; returns (added, skipped, path).

    One batch per gap: if the page already holds drafts for a gap, that gap's
    new drafts are skipped — once suggestions exist, the ball is in the
    human's court until they triage or cancel them. Identical titles are
    skipped too (same-run duplicates).
    """
    path = propose_inbox_path()
    text = path.read_text(encoding="utf-8") if path.exists() else _HEADER
    seen = _existing_titles(text)
    gaps_present = _gaps_awaiting_triage(text)
    today = f"{date.today():%Y-%m-%d}"

    added = skipped = 0
    parts = [text if text.endswith("\n") else text + "\n"]
    for b in blocks:
        if b["priority"] in gaps_present:
            skipped += len(b["proposals"])
            continue
        for p in b["proposals"]:
            title = p["title"].strip()
            if title in seen:
                skipped += 1
                continue
            seen.add(title)
            added += 1
            parts.append(
                f"- {title}\n"
                f"  route-hint:: {p['route']}\n"
                f"  keywords:: {', '.join(p['tags'])}\n"
                f"  from:: propose · gap #{b['priority']} {b['competency']} · {today}\n"
            )

    if added:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(parts), encoding="utf-8")
    return added, skipped, path
