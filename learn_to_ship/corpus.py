"""Load the JD-gap corpus.

This is the *server-side* read: the MCP server calls into here to serve gaps.
The agent itself never imports this module — it reaches the corpus only through
the MCP tool (see mcp_server.py / mcp_client.py), per the v0 constraint that the
corpus is read via MCP, not a direct file read.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .models import Gap

REPO_ROOT = Path(__file__).resolve().parent.parent

# Public default is the SYNTHETIC stub (this repo is built in public; real
# career data stays private — see CLAUDE.md "Build in public"). Point at the
# real, private corpus with LTS_CORPUS_PATH; never commit that file.
DEFAULT_CORPUS_PATH = REPO_ROOT / "data" / "jd-gaps.stub.yaml"

# Env override lets a deploy point at the real/private corpus without a code change.
CORPUS_PATH_ENV = "LTS_CORPUS_PATH"


def corpus_path() -> Path:
    override = os.environ.get(CORPUS_PATH_ENV)
    if not override:
        return DEFAULT_CORPUS_PATH
    path = Path(override)
    # Resolve a relative override against the repo root (not the CWD), so a path
    # like ../private-corpus/jd-gaps.real.yaml works from anywhere; .resolve()
    # collapses the ../ into a clean absolute path.
    return (path if path.is_absolute() else REPO_ROOT / path).resolve()


def load_gaps(path: Path | None = None) -> list[Gap]:
    """Parse the gap corpus into Gap records, ordered by the file.

    Raises FileNotFoundError if the corpus is missing and ValueError if it is
    structurally wrong — a broken corpus should fail loudly, not rank on nothing.
    """
    src = path or corpus_path()
    if not src.exists():
        raise FileNotFoundError(f"JD-gap corpus not found at {src}")

    data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    raw_gaps = data.get("gaps")
    if not isinstance(raw_gaps, list) or not raw_gaps:
        raise ValueError(f"corpus at {src} has no 'gaps' list")

    return [Gap.from_dict(g) for g in raw_gaps]
