"""Usage-evidence capture — make the middle visible without entering it.

rank says what to study; recall checks the cards; this module records that it
actually happened: rank runs, outputs shipped per study item, recall sessions.
The trail closes the loop rank → learn → recall → corpus update (QUESTIONS.md
Q3): the agent *reports* the evidence, and updating corpus levels stays a human
decision — advise around the middle, never perform it.

The log is a private, append-only JSONL file written only by the CLI (the
hosted server never imports this module). Default location is gitignored;
override with LTS_EVIDENCE_PATH.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVIDENCE_PATH = REPO_ROOT / "data" / "evidence.jsonl"

# Env override, sibling to LTS_CORPUS_PATH / LTS_VAULT_PATH.
EVIDENCE_PATH_ENV = "LTS_EVIDENCE_PATH"


def evidence_path() -> Path:
    override = os.environ.get(EVIDENCE_PATH_ENV)
    if not override:
        return DEFAULT_EVIDENCE_PATH
    path = Path(override).expanduser()
    # Relative overrides resolve against the repo root, like the corpus path.
    return (path if path.is_absolute() else REPO_ROOT / path).resolve()


def log_event(kind: str, **fields) -> None:
    """Append one event. Bookkeeping must never break the main flow, so a
    failed write is silently dropped rather than raised."""
    event = {"ts": datetime.now().isoformat(timespec="seconds"), "kind": kind, **fields}
    try:
        path = evidence_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


def read_events(path: Path | None = None) -> list[dict]:
    """All events, oldest first. A corrupt line loses one event, not the log."""
    src = path or evidence_path()
    if not src.exists():
        return []
    events: list[dict] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def summarize(events: list[dict]) -> str:
    """Human summary of the trail, ending in the corpus-update nudge."""
    if not events:
        return "No usage evidence yet — rank, ship an output, check cards; the trail builds itself."

    ranks = [e for e in events if e.get("kind") == "rank"]
    recalls = [e for e in events if e.get("kind") == "recall"]
    outputs = [e for e in events if e.get("kind") == "output"]

    lines: list[str] = []
    if ranks:
        lines.append(f"rank runs: {len(ranks)} (last {ranks[-1].get('ts', '?')[:10]})")
    if recalls:
        cards = sum(e.get("cards", 0) for e in recalls)
        ok = sum(e.get("ok", 0) for e in recalls)
        lines.append(f"recall sessions: {len(recalls)} — {cards} card(s) checked, {ok} ok")
    if outputs:
        lines.append("outputs shipped:")
        for e in outputs:
            note = f" — {e['note']}" if e.get("note") else ""
            lines.append(
                f"  {e.get('item', '?')} → {e.get('output', '?')} ({e.get('ts', '?')[:10]}){note}"
            )
        items = sorted({e["item"] for e in outputs if e.get("item")})
        lines.append("")
        lines.append("Items with shipped outputs — consider updating their levels in your corpus:")
        lines.extend(f"  {item}" for item in items)
    return "\n".join(lines)
