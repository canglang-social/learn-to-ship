"""CLI: rank a candidate study list.

    uv run python -m learn_to_ship
    uv run python -m learn_to_ship --candidates path/to/list.yaml --json

Reads the study list, runs the focus-director graph (which pulls the JD-gap
corpus over MCP), and prints a ranked "study this next, because it unblocks
gap X" list.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .graph import build_graph
from .models import StudyItem

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES = REPO_ROOT / "data" / "study-candidates.yaml"

# Load a gitignored .env (e.g. LTS_CORPUS_PATH pointing at the private corpus)
# before the graph runs, so the setting propagates to the MCP server subprocess.
load_dotenv(REPO_ROOT / ".env")


def load_candidates(path: Path) -> list[StudyItem]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("candidates", [])
    return [StudyItem.from_dict(c) for c in raw]


async def run(candidates: list[StudyItem]):
    graph = build_graph()
    result = await graph.ainvoke({"candidates": candidates})
    return result["ranked"]


def main() -> None:
    parser = argparse.ArgumentParser(prog="learn_to_ship", description=__doc__)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
        help="YAML study list to rank (default: bundled example)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    ranked = asyncio.run(run(load_candidates(args.candidates)))

    if args.json:
        print(json.dumps(ranked, indent=2, ensure_ascii=False))
        return

    print("Study this next — ranked by which JD gap it unblocks:\n")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. [{r['score']:.2f}] {r['title']}")
        print(f"   {r['rationale']}\n")


if __name__ == "__main__":
    main()
