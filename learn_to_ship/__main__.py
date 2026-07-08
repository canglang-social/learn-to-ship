"""CLI for learn-to-ship.

    uv run python -m learn_to_ship                       # rank (default)
    uv run python -m learn_to_ship --candidates list.yaml --json
    uv run python -m learn_to_ship recall --cards my.md [--material README.md]
    uv run python -m learn_to_ship recall --today        # today's vault journal
    uv run python -m learn_to_ship recall --journal 2026-07-07

`rank` (the default) runs the focus-director graph — ranks a study list by which
JD gap each item unblocks, reading the corpus over MCP. `recall` runs the
card-reviewer graph — you author flashcards, it checks them for complexity and
correctness (needs ANTHROPIC_API_KEY; the deterministic format checks don't).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from . import vault
from .graph import build_graph
from .models import StudyItem
from .recall_graph import build_recall_graph

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES = REPO_ROOT / "data" / "study-candidates.yaml"

# Load a gitignored .env (LTS_CORPUS_PATH, ANTHROPIC_API_KEY) before the graphs
# run, so settings propagate to the MCP server subprocess and the LLM checker.
load_dotenv(REPO_ROOT / ".env")

_SEV = {"error": "✗", "warn": "⚠"}


# --- rank ---------------------------------------------------------------------


def load_candidates(path: Path) -> list[StudyItem]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [StudyItem.from_dict(c) for c in data.get("candidates", [])]


async def _rank(candidates: list[StudyItem]):
    return (await build_graph().ainvoke({"candidates": candidates}))["ranked"]


def cmd_rank(args: argparse.Namespace) -> None:
    ranked = asyncio.run(_rank(load_candidates(args.candidates)))
    if args.json:
        print(json.dumps(ranked, indent=2, ensure_ascii=False))
        return
    print("Study this next — ranked by which JD gap it unblocks:\n")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. [{r['score']:.2f}] {r['title']}")
        print(f"   {r['rationale']}\n")


# --- recall -------------------------------------------------------------------


def _card_targets(args: argparse.Namespace) -> list[Path]:
    """Resolve --cards / --today / --journal into concrete card files."""
    if args.today:
        return [vault.journal_path()]
    if args.journal:
        return [vault.journal_path(args.journal)]
    return vault.card_files(args.cards)


def cmd_recall(args: argparse.Namespace) -> None:
    from .recall import has_api_key

    try:
        targets = _card_targets(args)
    except ValueError as e:
        raise SystemExit(f"error: {e}") from e

    material = args.material.read_text(encoding="utf-8") if args.material else None
    graph = build_recall_graph()
    results = [
        (
            f,
            graph.invoke({"cards_text": f.read_text(encoding="utf-8"), "material": material})[
                "reviews"
            ],
        )
        for f in targets
    ]

    if args.json:
        # One file keeps the original flat shape; a directory groups by file.
        if len(results) == 1:
            print(json.dumps(results[0][1], indent=2, ensure_ascii=False))
        else:
            grouped = [{"file": str(f), "reviews": r} for f, r in results]
            print(json.dumps(grouped, indent=2, ensure_ascii=False))
        return

    if not has_api_key():
        print(
            "(no ANTHROPIC_API_KEY — format checks only; set a key for complexity + correctness)\n"
        )

    if not any(r for _, r in results):
        print("No #card blocks found.")
        return
    for f, reviews in results:
        print(f"Reviewing {len(reviews)} card(s) from {f}:\n")
        for i, r in enumerate(reviews, 1):
            mark = "✓" if r["verdict"] == "ok" else "needs work"
            print(f"{i}. {r['front']}  [{mark}]")
            for issue in r["issues"]:
                print(f"   {_SEV.get(issue['severity'], '·')} [{issue['kind']}] {issue['message']}")
            print()


# --- entrypoint ---------------------------------------------------------------


def main() -> None:
    argv = sys.argv[1:]
    # Back-compat: no subcommand (or leading flags) means `rank`.
    if not argv or argv[0] not in {"rank", "recall"}:
        argv = ["rank", *argv]

    parser = argparse.ArgumentParser(prog="learn_to_ship", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    rank_p = sub.add_parser("rank", help="rank a study list by JD-gap leverage")
    rank_p.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    rank_p.add_argument("--json", action="store_true")
    rank_p.set_defaults(func=cmd_rank)

    recall_p = sub.add_parser("recall", help="check hand-written flashcards")
    recall_src = recall_p.add_mutually_exclusive_group(required=True)
    recall_src.add_argument("--cards", type=Path, help="file (or directory) of Logseq #card blocks")
    recall_src.add_argument(
        "--today",
        action="store_true",
        help="check today's vault journal (needs LTS_VAULT_PATH)",
    )
    recall_src.add_argument(
        "--journal",
        metavar="DATE",
        help="check the vault journal for DATE, e.g. 2026-07-07 (needs LTS_VAULT_PATH)",
    )
    recall_p.add_argument(
        "--material", type=Path, help="optional source to check correctness against"
    )
    recall_p.add_argument("--json", action="store_true")
    recall_p.set_defaults(func=cmd_recall)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
