# LOG — build-in-public trail

Dated milestones for learn-to-ship. Newest first. Each entry marks a real
shipping step (skeleton → stub graph ranks → CI eval green → deployed → real
corpus wired), per the build-in-public rule in CLAUDE.md.

## 2026-07-06 — v1 recall loop: a card *checker*, not a generator

Closed the learning loop's other half — study → produce an output → recall —
without defeating the point of recall. Active recall works because *you* phrase
the card; an LLM-written card is one you won't remember. So v1 does **not**
generate cards. You author them (canonical Logseq `#card` format); a second
LangGraph graph, `card-reviewer`, checks each:

- **format** — deterministic lint (bilingual EN+中文, tag order, valid `#q/*`),
  no key, CI-testable.
- **complexity + correctness** — Claude (Sonnet 5) flags cards that cram >1 idea
  or whose answer is wrong / unsupported by the source. It critiques; never rewrites.

The LLM sits behind an injectable checker, so CI runs a deterministic stub and
stays hermetic (23 tests green, no key); a `live`-marked test exercises real
Claude, skipped in CI. Local-only — the hosted deploy stays rank-only and keyless.
This mirrors v0's stance: the agent advises, the human decides.

## 2026-07-06 — cloud-deployed, live endpoint

v0 is fully shipped. The agent runs as a live cloud endpoint, closing the last
acceptance criterion (reachable as a deployed endpoint, not local-only).

- Served via a small FastAPI layer (`learn_to_ship/server.py`) in a container,
  deployed **free** to Hugging Face Spaces — no paid LangGraph Platform needed.
- Live: <https://vegekiwi-learn-to-ship.hf.space> (`GET /` health, `POST /rank`).
- The hosted deploy serves the public fictional stub; the private corpus never
  leaves local (`.env` + real corpus are `.dockerignore`'d).

That completes every v0 goal and acceptance criterion in `spec.md`.

## 2026-07-06 — v0 shipped public, CI green

First public ship. The whole v0 spine is live and proven end to end.

- **Agent** — a thin LangGraph graph with one node, `focus-director`, that ranks
  a candidate study list by which JD gap each item unblocks. Pure, deterministic
  ranker (word-anchored keyword match → sort by closing-leverage).
- **MCP corpus** — the agent reads the JD-gap corpus through a `get_jd_gaps` MCP
  tool (a real stdio round-trip), never a direct file read.
- **CI eval harness** — a golden eval pins the full ranked order; GitHub Actions
  runs lint + the eval on every push. First run passed green in ~18s.
- **Served endpoint** — verified reachable via `langgraph dev` over HTTP;
  `langgraph.json` registers the graph for LangGraph Platform.
- **Public / private split** — the committed corpus is a fictional "Sample
  Learner" stub; the real career corpus stays private, wired via
  `LTS_CORPUS_PATH`. History was rewritten clean before publishing so no real
  JD-gap data exists in any commit.

Repo: https://github.com/canglang-social/learn-to-ship

Next: push a hosted cloud deploy; wire the real private corpus for daily use.
