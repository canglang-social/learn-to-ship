# spec.md — learn-to-ship

Created 2026-07-05 from the `agent-project` template (forge).
Pre-spec rationale: `forge/career/decisions/learn-to-ship.md` (the "why").
This spec is the source of truth for scope once the decision doc is
scaffolded.

## Problem / Goal

A personal **output-driven learning agent**: I learn *in order to ship an
output*, and v0's output is **closing a specific job-role gap**. It is the
deployable-agent form of my existing `learning-loop` (agent-kit `learn`
skill + Logseq) — a shipped LangGraph agent, cloud-deployed with a CI eval
harness, so it doubles as a portfolio artifact.

Why now: my private job-hunt analysis flags two high-value gaps to close — a
*shipped agent on a named framework* (LangGraph) and a *cloud-deployed +
CI/eval-tracked artifact*. This project closes both in one build while
generating real daily-usage evidence (I use it every day to decide what to
study next).

## Goals

- [x] v0: a thin **LangGraph** agent whose one node is **focus-director** —
      rank a candidate study list by which JD gap each item unblocks.
- [x] Consume a **JD-gap corpus via an MCP tool** (wrap the private career
      corpus as MCP) — closes the "consumes-an-MCP-tool" JD gap authentically.
- [x] **Cloud-deploy** the agent with a **GitHub Actions CI eval harness**
      (deployed free to Hugging Face Spaces; CI eval gates every push).
- [~] Become portfolio case study #2 — repo public + blog post drafted; publish
      the post to complete.
- [x] **v1: the recall loop, as a card *checker*.** You author the flashcards
      (phrasing them is the studying — never LLM-generated); a second LangGraph
      graph, `card-reviewer`, checks each card for **complexity** (atomicity) and
      **correctness** (via Claude), plus a deterministic Logseq-format lint.
      Local-only; hermetic CI (Claude behind an injectable stub).

## Non-Goals (frozen scope)

- v0 does NOT do capture or `#inbox` triage — **`#inbox` capture is
  Felix-owned**; the agent never writes attention-capture lines. Triage lands
  in v1.1.
- v0 does NOT do focus-guardian (keep-session-on-rails) — v2.
- v1's recall loop is a card **checker**, not a generator: the human authors the
  cards; the agent only critiques (see Goals). The blog output stream stays out.
- No web UI / DB in v0. The one service layer is a thin FastAPI wrapper
  (`server.py`) that exposes the rank graph for the hosted deploy — no business
  logic of its own; recall stays local (needs a key + writes nothing hosted).

## Requirements / User stories

- **First story (v0, eval-harness target):** As Felix, I run the agent and it
  reads my JD-gap corpus (via MCP) plus a candidate study list, then returns a
  **ranked "study this next, because it unblocks gap X"** with a one-line
  rationale per item.
- As Felix, I never hand it `#inbox` capture — it picks up *after* capture.

## Acceptance criteria

- Given the JD-gap corpus + a candidate study list, focus-director returns a
  deterministic ranked list where each item cites the gap it unblocks.
- The agent runs as a LangGraph graph (not an ad-hoc script) and reads the
  corpus through an MCP tool call, not a hardcoded file read.
- CI (GitHub Actions) runs the eval harness on push; a failing eval fails the
  build.
- The agent is reachable as a cloud-deployed endpoint/run, not local-only.

## Constraints

- Python 3.11+, managed with uv.
- LangGraph as the agent framework (named-framework JD gap is the point).
- MCP for the corpus read (JD gap is the point) — no direct file read in v0.
- **Built in public — agent public / career data private.** This repo is
  public and consumes a PRIVATE career corpus (via MCP). The public eval
  harness runs on a stub/redacted fixture (fake JD
  gaps); real corpus reads only from a local/private MCP. Never commit real
  JD-gap or career data. Publish at milestones (skeleton → stub graph ranks →
  CI green → deployed → real MCP wired), not on a clock.

## Reused assets (from forge)

- `agent-project` template (forge) — scaffold. [used]
- **MCP tool over the JD-gap corpus** — built in-repo for v0
  (`learn_to_ship/mcp_server.py`, tool `get_jd_gaps`). Serves the synthetic stub
  publicly; the real corpus is wired via `LTS_CORPUS_PATH` / a private MCP.
  [done — v0] Corpus source is a private competency map, not the raw skills
  inventory (see Decisions).
- **bilingual `#card` convention** (from the agent-kit `learn` skill + ragx
  `/card`) — reused by v1's card-reviewer. There is no importable code component:
  it's a Logseq-format convention + a review approach, reproduced in
  `learn_to_ship/logseq.py` (parse/lint) and `recall.py` (the Claude check).
  [done — v1]

## Decisions taken during the v0 build (2026-07-05)

- **Gap corpus source (spec correction).** The spec pointed at the raw skills
  inventory, but that is the *skills* side. The actual JD-*gap* data is a private
  competency map (competencies clustered from logged JDs × frequency × my current
  level, with an explicit gap-ranking) — focus-director ranks against that.
- **Candidate study-list format.** A plain YAML list of `{id, title, tags}`
  (`data/study-candidates.yaml`); the agent picks up after `#inbox` capture. A
  Logseq-page → list transform is a v1 concern.
- **MCP server home.** Built in *this* repo for v0 (self-contained, testable,
  deployable together). May migrate to the private corpus repo later; the agent
  only depends on the `get_jd_gaps` MCP-tool contract.

## Resolved during the deploy + v1 build (2026-07-06/07)

- **Cloud target — Hugging Face Spaces (free).** LangGraph Platform Cloud costs
  $39/mo, so v0 deploys a thin FastAPI container to a free HF Docker Space
  instead. `langgraph.json` is kept for `langgraph dev` and the paid/Lite
  LangGraph Platform path (see `DEPLOY.md`). Live:
  <https://vegekiwi-learn-to-ship.hf.space>.
- **Real private corpus — a gitignored file in the sibling `job_hunting` repo**
  (`../job_hunting/data/jd-gaps.real.yaml`), wired via `LTS_CORPUS_PATH` (relative
  paths resolve against the repo root). A private MCP server remains an option;
  the agent only needs `LTS_CORPUS_PATH` to point somewhere.

## Open questions

- Publish the case-study blog post (drafted in the `blog` repo) to close Goal 4.
- Add usage-evidence capture (I run it daily; nothing records that yet).
