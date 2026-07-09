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
- [x] Become portfolio case study #2 — repo public; the post is live in both
      languages: <https://canglang.netlify.app/blog/2026-07-06-learning-to-ship/>
      (verified 2026-07-08 — the "[~] publish to complete" note was stale).
- [x] **v1: the recall loop, as a card *checker*.** You author the flashcards
      (phrasing them is the studying — never LLM-generated); a second LangGraph
      graph, `card-reviewer`, checks each card for **complexity** (atomicity) and
      **correctness** (via Claude), plus a deterministic Logseq-format lint.
      Local-only; hermetic CI (Claude behind an injectable stub).
- [x] **v1.1: dogfooding features** (see Resolved below) — vault-aware recall +
      the demo front page, both demanded via `QUESTIONS.md`.
- [x] **v1.2: usage-evidence capture** (QUESTIONS.md Q3) — a private local
      trail (rank runs → outputs shipped → recall sessions) that closes the
      loop into corpus updates, which stay human-made.

## Non-Goals (frozen scope)

- v0 does NOT do capture or `#inbox` triage — **`#inbox` capture is
  Felix-owned**; the agent never writes attention-capture lines. *Resolved in
  v1.4 (QUESTIONS.md Q6):* triage stays human permanently — the human routes
  `#inbox` onto the vault queue page; the agent only READS the already-triaged
  result (`rank --queue`). No agent-side triage is planned anymore.
  *Amended in v1.7 (Q10):* the agent may write exactly ONE vault surface —
  the machine-owned propose inbox (`[[Learning/inbox/propose]]`), append-only,
  on explicit `--write`, carrying pre-triage suggestions (no task marker, no
  `route::`). Capture lines, the queue, journals, and cards stay unwritable.
- v0 does NOT do focus-guardian (keep-session-on-rails) — v2.
- v1's recall loop is a card **checker**, not a generator: the human authors the
  cards; the agent only critiques (see Goals). The blog output stream stays out.
- No web UI / DB in v0. The one service layer is a thin FastAPI wrapper
  (`server.py`) that exposes the rank graph for the hosted deploy — no business
  logic of its own; recall stays local (needs a key + writes nothing hosted).
  *Amended in v1.1 (QUESTIONS.md Q4):* the wrapper now also serves ONE static
  demo front page at `GET /` — no build toolchain, no auth, no persistence, no
  DB; recall stays CLI/local. *Amended in v1.3 (Q5):* plus styled read-only
  renderings of the canonical `docs/*.md` at `GET /docs/*` (shared theme, no
  new content surface — the Markdown stays the source of truth). Anything
  beyond these read-only pages remains out.

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
- **Candidate study-list format.** A plain YAML list of `{id, title, tags}`;
  the agent picks up after `#inbox` capture. A Logseq-page → list transform is
  a v1 concern. *Renamed in Q9 (2026-07-09):* `study-candidates.stub.yaml`
  (committed example) / `study-candidates.real.yaml` (private), matching the
  corpus's `.stub`/`.real` scheme.
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

## Resolved during the v1.1 build (2026-07-08)

Both driven by dogfooding questions recorded in `QUESTIONS.md` (the
user-question log — demand signals live there; decisions land here).

- **Vault-aware recall (Q2).** The cards live in the Logseq vault, so recall
  now resolves them itself: `LTS_VAULT_PATH` in `.env` names the vault root,
  `--today` / `--journal DATE` map to `journals/yyyy_MM_dd.md`, and `--cards`
  accepts a directory (scanned for `#card` blocks). Read-path only — capture
  and authoring stay Felix-owned.
- **Front page (Q4).** The non-goal "no web UI in v0" was scoped to v0;
  amended above. `GET /` now serves one static, self-contained demo page over
  the existing `POST /rank`; health moved to `GET /health`. Hosted, it demos
  the fictional stub corpus; locally the same page ranks the private corpus.
  Explicitly still out: DB, auth, a hosted recall UI.

## Resolved during the v1.2 build (2026-07-08)

- **Usage-evidence capture (QUESTIONS.md Q3).** The middle of the loop was
  invisible; now the CLI keeps a private, append-only JSONL trail
  (`data/evidence.jsonl`, gitignored; override `LTS_EVIDENCE_PATH`): `rank`
  and `recall` auto-log their runs, `evidence --item X --output <url>` records
  a shipped output, and bare `evidence` shows the trail ending in a nudge to
  update corpus levels — the update itself stays human (advise around the
  middle, never perform it). Local-only: the hosted server never logs.
- **Goal 4 was already complete.** The case-study post has been live since
  2026-07-06 (en + zh); the spec's "publish to complete" note was stale.
  Lesson recorded: check the live artifact before trusting a status note.
- **Milestone convention hardened.** Each milestone now gets an annotated git
  tag (`vX.Y`) on the merge commit, alongside the LOG.md entry (`v1.1` tagged
  retroactively the same day).

## Resolved during the v1.3 build (2026-07-08)

- **Styled docs routes (QUESTIONS.md Q5).** The user liked the artifact-style
  doc pages, but GitHub doesn't render committed HTML — so the served app now
  renders the canonical `docs/*.md` as styled pages at `GET /docs/usage` and
  `GET /docs/development`: shared design tokens extracted to
  `static/theme.css` (front page + docs, the second use that justified
  extraction), python-`markdown` server-side, mermaid.js client-side for the
  atlas diagrams, OpenAPI UI moved to `/api-docs`. One source of truth, three
  faces: GitHub Markdown, styled pages on the Space, the same locally.

## Resolved during the v1.4 build (2026-07-08)

- **Rank straight from the vault queue (QUESTIONS.md Q6).** The "Logseq-page
  → list transform" flagged as a v1 concern is shipped: `rank --queue` parses
  the human-triaged queue page (`LTS_QUEUE_PAGE`, default `Learning/Queue`,
  under `LTS_VAULT_PATH`) into study candidates — task-marked bullets only,
  tags from #hashtags + [[refs]] + `route::`. Read-only; capture and triage
  remain human; `data/study-candidates.real.yaml` remains for ad-hoc lists.

## Resolved during the v1.5 build (2026-07-08)

- **Gap-driven candidates (QUESTIONS.md Q7).** The queue holds only *known*
  learning, so an uncovered gap was invisible to rank. Both stages shipped:
  *coverage* — `ranker.uncovered()` lists priority gaps no candidate
  unblocks, surfaced in every rank output (CLI, JSON, `/rank`, front page);
  *proposals* — a third graph, `gap_proposer`, drafts 2–3 study items per
  uncovered gap via an injectable Claude seam (`propose [--queue]`),
  printed as paste-ready queue bullets. Boundary held: the agent proposes
  in the terminal; the human triages onto the vault; nothing is written.

## Resolved during the v1.6 build (2026-07-08)

- **LLM provider switch (QUESTIONS.md Q8).** Both LLM seams (card checker,
  gap proposer) now build their model through `llm.py`: `LTS_LLM_PROVIDER =
  auto | deepseek | anthropic` (auto prefers DeepSeek — test cheap first),
  `LTS_LLM_MODEL` overrides the per-provider default. Switching back to
  Anthropic later is one `.env` line. CI unchanged — stubs never call out.

## Resolved during the v1.7 build (2026-07-09)

- **Propose-inbox (QUESTIONS.md Q10).** Propose output was queue-shaped
  (`LATER` + `route::`) — silently pre-performing the human's triage. Now it
  is inbox-shaped everywhere (plain bullets, `route-hint::`, provenance), and
  `propose --write` appends it to `[[Learning/inbox/propose]]`
  (`LTS_PROPOSE_INBOX_PAGE`) — the single vault surface the agent may write:
  append-only, dedup by title, self-explaining page header, implemented in
  `inbox.py` and nowhere else. The human triages entries per
  `docs/LEARNING-LOOP.md` (routes A–D, authored by the owner in PR #14).

## Open questions

- Hybrid matching fallback (QUESTIONS.md Q1): only if daily use shows the
  keyword matcher missing frequently — an LLM/embedding second pass for
  unmatched items, outside the golden-eval path. Watching, not building.
