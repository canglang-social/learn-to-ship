# LOG — build-in-public trail

Dated milestones for learn-to-ship. Newest first. Each entry marks a real
shipping step (skeleton → stub graph ranks → CI eval green → deployed → real
corpus wired), per the build-in-public rule in CLAUDE.md.

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
