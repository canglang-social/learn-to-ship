"""CLI for learn-to-ship.

    uv run python -m learn_to_ship                       # rank (default)
    uv run python -m learn_to_ship --candidates list.yaml --json
    uv run python -m learn_to_ship rank --queue          # rank the vault queue page
    uv run python -m learn_to_ship recall --cards my.md [--material README.md]
    uv run python -m learn_to_ship recall --today        # today's vault journal
    uv run python -m learn_to_ship recall --journal 2026-07-07
    uv run python -m learn_to_ship evidence              # the usage trail
    uv run python -m learn_to_ship evidence --item k8s-deploy --output <url>

`rank` (the default) runs the focus-director graph — ranks a study list by which
JD gap each item unblocks, reading the corpus over MCP. `recall` runs the
card-reviewer graph — you author flashcards, it checks them for complexity and
correctness (needs an LLM key — DeepSeek or Anthropic, see llm.py; the
deterministic format checks don't).
`evidence` shows the local usage trail (rank runs, outputs shipped, recall
sessions) and records outputs; corpus updates stay yours.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from . import evidence, vault
from .graph import build_graph
from .models import StudyItem
from .recall_graph import build_recall_graph

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES = REPO_ROOT / "data" / "study-candidates.stub.yaml"

# Load a gitignored .env (LTS_* settings, LLM API keys) before the graphs
# run, so settings propagate to the MCP server subprocess and the LLM checker.
load_dotenv(REPO_ROOT / ".env")

_SEV = {"error": "✗", "warn": "⚠"}


# --- rank ---------------------------------------------------------------------


def load_candidates(path: Path) -> list[StudyItem]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [StudyItem.from_dict(c) for c in data.get("candidates", [])]


async def _rank(candidates: list[StudyItem]) -> dict:
    return await build_graph().ainvoke({"candidates": candidates})


def cmd_rank(args: argparse.Namespace) -> None:
    if args.queue:
        try:
            page = vault.queue_page_path()
            candidates = vault.parse_queue(page.read_text(encoding="utf-8"))
            source = str(page)
        except ValueError as e:
            raise SystemExit(f"error: {e}") from e
        if not candidates:
            raise SystemExit(f"error: no task-marked queue items found in {page}")
    else:
        candidates = load_candidates(args.candidates)
        source = str(args.candidates)
    result = asyncio.run(_rank(candidates))
    ranked, missing = result["ranked"], result.get("uncovered", [])
    # Usage evidence: the fact that you ranked (and what led) is part of the loop.
    evidence.log_event(
        "rank",
        candidates=len(ranked),
        top=[r["id"] for r in ranked[:3]],
        source=source,
        uncovered=len(missing),
    )
    if args.json:
        print(json.dumps({"ranked": ranked, "uncovered": missing}, indent=2, ensure_ascii=False))
        return
    print("Study this next — ranked by which JD gap it unblocks:\n")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. [{r['score']:.2f}] {r['title']}")
        print(f"   {r['rationale']}\n")
    if missing:
        print("Uncovered priority gaps — nothing in this list unblocks them:")
        for g in missing:
            pct = round(g["freq"] * 100)
            print(
                f"  #{g['priority']} {g['competency']} (asked in ~{pct}% of JDs, you are '{g['level']}')"
            )
        print("  → capture study ideas for these, or run `propose` for drafts.")


# --- recall -------------------------------------------------------------------


def _card_targets(args: argparse.Namespace) -> list[Path]:
    """Resolve --cards / --today / --journal into concrete card files."""
    if args.today:
        return [vault.journal_path()]
    if args.journal:
        return [vault.journal_path(args.journal)]
    return vault.card_files(args.cards)


def cmd_recall(args: argparse.Namespace) -> None:
    from .llm import has_llm_key

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
    for f, reviews in results:
        if reviews:
            ok = sum(1 for r in reviews if r["verdict"] == "ok")
            evidence.log_event("recall", source=str(f), cards=len(reviews), ok=ok)

    if args.json:
        # One file keeps the original flat shape; a directory groups by file.
        if len(results) == 1:
            print(json.dumps(results[0][1], indent=2, ensure_ascii=False))
        else:
            grouped = [{"file": str(f), "reviews": r} for f, r in results]
            print(json.dumps(grouped, indent=2, ensure_ascii=False))
        return

    if not has_llm_key():
        print(
            "(no LLM key — format checks only; set DEEPSEEK_API_KEY or "
            "ANTHROPIC_API_KEY for complexity + correctness)\n"
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


# --- propose ------------------------------------------------------------------


def _rank_candidates(args: argparse.Namespace) -> tuple[list[StudyItem], str]:
    """Resolve --queue / --candidates into study items (shared by rank/propose)."""
    if args.queue:
        page = vault.queue_page_path()
        return vault.parse_queue(page.read_text(encoding="utf-8")), str(page)
    return load_candidates(args.candidates), str(args.candidates)


def cmd_propose(args: argparse.Namespace) -> None:
    from . import inbox
    from .llm import has_llm_key

    try:
        candidates, source = _rank_candidates(args)
    except ValueError as e:
        raise SystemExit(f"error: {e}") from e

    from .propose_graph import build_propose_graph

    result = asyncio.run(build_propose_graph().ainvoke({"candidates": candidates}))
    blocks = result["proposals"]

    written = skipped = 0
    if args.write and any(b["proposals"] for b in blocks):
        try:
            written, skipped, _ = inbox.append_proposals(blocks)
        except ValueError as e:
            raise SystemExit(f"error: {e}") from e

    evidence.log_event(
        "propose",
        gaps=len(blocks),
        drafts=sum(len(b["proposals"]) for b in blocks),
        source=source,
        written=written,
    )

    if args.json:
        print(json.dumps(blocks, indent=2, ensure_ascii=False))
        return

    if not blocks:
        print("No uncovered priority gaps — your list already addresses the whole ladder.")
        return
    if not has_llm_key():
        print(
            "(no LLM key — listing uncovered gaps only; set DEEPSEEK_API_KEY "
            "or ANTHROPIC_API_KEY for drafts)\n"
        )
    print(
        "Drafts per uncovered gap — PRE-TRIAGE suggestions (route A–D is your\n"
        "call). Use --write to deliver them to your vault propose inbox;\n"
        "nothing reaches the queue except by your hand:\n"
    )
    for b in blocks:
        pct = round(b["freq"] * 100)
        print(f"Gap #{b['priority']} — {b['competency']} (~{pct}% of JDs, you are '{b['level']}')")
        if not b["proposals"]:
            print("  (no drafts)")
        for p in b["proposals"]:
            print(f"  - {p['title']}")
            print(f"    route-hint:: {p['route']} · keywords: {', '.join(p['tags'])}")
        print()
    if args.write:
        import os

        name = os.environ.get(inbox.PROPOSE_INBOX_ENV, inbox.DEFAULT_PROPOSE_INBOX)
        print(f"Appended {written} draft(s) to [[{name}]] ({skipped} duplicate(s) skipped).")


# --- evidence -----------------------------------------------------------------


def cmd_evidence(args: argparse.Namespace) -> None:
    if args.item or args.output:
        if not (args.item and args.output):
            raise SystemExit("error: recording an output needs both --item and --output")
        extra = {"note": args.note} if args.note else {}
        evidence.log_event("output", item=args.item, output=args.output, **extra)
        print(f"Recorded: {args.item} → {args.output}")
        return
    print(f"Usage evidence ({evidence.evidence_path()}):\n")
    print(evidence.summarize(evidence.read_events()))


# --- entrypoint ---------------------------------------------------------------


def main() -> None:
    argv = sys.argv[1:]
    # Back-compat: no subcommand (or leading flags) means `rank`.
    if not argv or argv[0] not in {"rank", "recall", "evidence", "propose"}:
        argv = ["rank", *argv]

    parser = argparse.ArgumentParser(prog="learn_to_ship", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    rank_p = sub.add_parser("rank", help="rank a study list by JD-gap leverage")
    rank_src = rank_p.add_mutually_exclusive_group()
    rank_src.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    rank_src.add_argument(
        "--queue",
        action="store_true",
        help="rank the triaged vault queue page (LTS_QUEUE_PAGE, needs LTS_VAULT_PATH)",
    )
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

    prop_p = sub.add_parser(
        "propose", help="draft study items for uncovered priority gaps (needs a key)"
    )
    prop_src = prop_p.add_mutually_exclusive_group()
    prop_src.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    prop_src.add_argument(
        "--queue",
        action="store_true",
        help="coverage against the triaged vault queue page (LTS_QUEUE_PAGE)",
    )
    prop_p.add_argument(
        "--write",
        action="store_true",
        help="append drafts to the vault propose inbox (LTS_PROPOSE_INBOX_PAGE) for YOUR triage",
    )
    prop_p.add_argument("--json", action="store_true")
    prop_p.set_defaults(func=cmd_propose)

    ev_p = sub.add_parser(
        "evidence", help="see the usage trail, or record a shipped output for a study item"
    )
    ev_p.add_argument("--item", help="study-item id that produced an output")
    ev_p.add_argument("--output", help="the shipped output (URL or path)")
    ev_p.add_argument("--note", help="optional one-line context")
    ev_p.set_defaults(func=cmd_evidence)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
