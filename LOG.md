# LOG — build-in-public trail

Dated milestones for learn-to-ship. Newest first. Each entry marks a real
shipping step (skeleton → stub graph ranks → CI eval green → deployed → real
corpus wired), per the build-in-public rule in CLAUDE.md.

## 2026-07-08 — v1.2 shipped: usage-evidence capture closes the loop

QUESTIONS.md Q3 asked what sits between the corpus (input) and the cards
(output). Answer: the learning — human-owned, and until now invisible to the
system. v1.2 makes it visible without entering it:

- `rank` and `recall` auto-log runs to a private, gitignored JSONL trail
  (`data/evidence.jsonl`, `LTS_EVIDENCE_PATH` to override).
- `evidence --item <id> --output <url>` records the output you shipped;
  bare `evidence` shows the trail — rank runs, outputs per item, recall
  sessions — ending in a nudge to update corpus levels. The update stays
  human: the agent reports the middle, never performs it.
- Housekeeping: Goal 4 was found already complete (the case-study post has
  been live since 07-06 in en+zh — the spec note was stale); milestones now
  get annotated git tags (`v1.1` tagged retroactively).

46 hermetic tests green (8 new). Local-only; the hosted server never logs.

## 2026-07-08 — v1.1 shipped: dogfooding questions become features

The project ate its own thesis: a user-questions session (recorded in the new
`QUESTIONS.md` — demand signals live there, decisions land in `spec.md`)
produced four questions; two crossed into scope and shipped the same day.

- **QUESTIONS.md** — a user-question log now drives product design. Per
  question: what was asked, the underlying need, the design implication as a
  hypothesis, and its status. Q1 (why keyword matching) stayed answered-only;
  Q3 (what's the middle — the learning) sharpened the usage-evidence open
  question; Q2 and Q4 became v1.1.
- **Vault-aware recall (Q2).** `LTS_VAULT_PATH` + `recall --today` /
  `--journal DATE` resolve the Logseq journal directly; `--cards` accepts a
  directory. No more hand-typed vault paths. Read-path only — capture stays
  human-owned. Verified against the real vault.
- **Front page (Q4).** The hosted deploy now serves a demo page at `GET /`
  (health → `/health`): edit a study list, see it ranked with rationales.
  One static file, no build toolchain/DB/auth; the v0 non-goal was amended in
  spec.md. Verified in a real browser against the rebuilt live Space.

38 hermetic tests green (13 new). Live: <https://vegekiwi-learn-to-ship.hf.space>.

## 2026-07-07 — v1 hardening: self-audit + parser fixes

Reviewed the recall checker and found three real parser bugs, all fixed with
regression tests:

- the EN/中文 split corrupted cards that pair terms inline as `term (中文)` — the
  vault's own convention. Root fix: stop splitting; store the whole bilingual
  front/back, and let the lint check only that both scripts are present.
- an `id::` / `deck::` property line between front and back dropped the back
  (false "missing back"); the back scan now skips property lines.
- `#card-group` (cloze/image groups) false-matched as `#card`; the tag is now
  matched as a whole word.

Also constrained the LLM checker's `kind`/`severity` to enums, and completed the
README (the How-it-works + test sections still described only v0). 25 tests green.

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
