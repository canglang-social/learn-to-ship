# CLAUDE.md — learn-to-ship

## Overview

Output-driven learning agent: I learn in order to ship an output, and v0's
output is closing a specific job-role gap. It is the deployable-agent form of
my existing `learning-loop` — a LangGraph agent, cloud-deployed with a CI eval
harness, doubling as a portfolio artifact. v0 is a thin agent whose one node
(`focus-director`) ranks a candidate study list by which JD gap each item
unblocks, reading the JD-gap corpus through an MCP tool. It is NOT a capture
tool — `#inbox` capture is Felix-owned; the agent picks up after capture. v1
adds a second graph, `card-reviewer`, that checks flashcards I author (format +
complexity + correctness); it never generates cards. Keep `spec.md` the source
of truth for scope.

## Tech stack

- Python 3.11+, managed with uv.

## Commands

- Env: uv sync
- Run (rank): uv run python -m learn_to_ship
- Run (recall): uv run python -m learn_to_ship recall --today | --journal <date> | --cards <file|dir>  [--material <file>]
- Evidence: uv run python -m learn_to_ship evidence [--item <id> --output <url>]
- Serve: uv run langgraph dev   (or the FastAPI server — see DEPLOY.md)
- Test: uv run pytest           (add -m live for the real-Claude card checks)
- Lint: uv run ruff check . && uv run ruff format .

## Conventions

- Small, single-purpose modules; no framework until a second use demands it.
- Type hints on public functions; docstrings state intent, not mechanics.
- Conventional commits (feat:, fix:, docs:, chore:).

## Build in public (agent public / career data private)

This project is built in public — it dogfoods its own output-driven thesis and
builds a dated, public trail of actually shipping an agent end to end.

- HARD RULE: the agent goes public, the career data stays private. This repo
  consumes a private career corpus via MCP. The public eval harness runs on a
  STUB/fictional fixture (fake JD gaps); the real corpus is read only from a
  local/private MCP. Bake this split in from commit one — never commit real
  JD-gap / career data.
- Publish at milestones, not on a clock: skeleton runs → stub graph ranks →
  CI eval green → deployed → real MCP wired. Each is one `LOG.md` entry, an
  annotated git tag (`vX.Y`) on the merge commit, and optionally one post to
  the `blog` project.
- README is written for a stranger (what / why / status), not for me.

## Do / Do-NOT

- DO update spec.md when scope shifts.
- DO NOT expand scope beyond spec.md non-goals without discussing first.
- DO NOT commit real career-corpus data — use the stub fixture (see above).
