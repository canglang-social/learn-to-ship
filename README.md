# learn-to-ship

An **output-driven learning agent**: it learns *in order to ship*. v0 answers one
question — *"of everything I could study next, which item unblocks the most
valuable job-role gap?"* — and returns a ranked list, each item citing the gap
it closes.

Its core is a thin [LangGraph](https://langchain-ai.github.io/langgraph/) node,
**focus-director**, that reads a JD-gap corpus **through an MCP tool** and ranks a
candidate study list deterministically by closing-leverage. v1 adds a second
graph, **card-reviewer**, that checks the flashcards you write (see below). It
ships with a GitHub Actions eval harness and a live cloud deploy, so it doubles as
a portfolio artifact for the exact gaps it reasons about (a shipped agent on a
named framework; a cloud-deployed, CI/eval-tracked build).

**Live:** <https://vegekiwi-learn-to-ship.hf.space> — open it in a browser for
the clickable demo (edit a study list → ranked, on the public demo corpus), or
hit the API directly:

```bash
curl -s -X POST https://vegekiwi-learn-to-ship.hf.space/rank \
  -H 'content-type: application/json' \
  -d '{"candidates":[{"id":"a","title":"Deploy to a cloud container","tags":["cloud","deploy"]}]}'
```

**Docs:** [docs/USAGE.md](docs/USAGE.md) (daily use + the loop atlas) ·
[docs/LEARNING-LOOP.md](docs/LEARNING-LOOP.md) (the human learning loop this
agent serves) ·
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) (architecture map + dev workflows) —
also served styled at [/docs/usage](https://vegekiwi-learn-to-ship.hf.space/docs/usage)
on the live deploy.

## How it works

Two thin graphs. **rank** (v0, the default) — *what should I study next?*

```text
candidate study list ─┐
                      ▼
              ┌───────────────┐     MCP call      ┌──────────────────┐
              │ focus-director │ ───────────────▶ │ JD-gap MCP server │
              │   (one node)   │ ◀─────────────── │  (get_jd_gaps)    │
              └───────────────┘   gaps + weights  └──────────────────┘
                      │
                      ▼
      ranked "study this next, because it unblocks gap X"
```

**recall** (v1) — *you author the cards, it checks them:*

```text
your #card blocks ─┐
                   ▼
          ┌────────────────┐  ── format lint (deterministic) ──┐
          │  card-reviewer  │                                   ├─▶ per-card review
          │   (one node)    │  ── complexity + correctness ─────┘
          └────────────────┘        (Claude, when a key is set)
```

- **focus-director** (`learn_to_ship/graph.py`) — the rank graph's node. Fetches
  the gap corpus over MCP, then applies a **deterministic** ranker.
- **ranker** (`learn_to_ship/ranker.py`) — pure function. Matches each study item
  to the gap it unblocks (word-anchored keyword match) and sorts by the gap's
  closing-leverage. Same inputs → same order, always.
- **MCP server** (`learn_to_ship/mcp_server.py`) — the *only* thing that reads the
  corpus file; exposes `get_jd_gaps`. The agent never reads the corpus directly.
- **card-reviewer** (`learn_to_ship/recall_graph.py`) — the recall graph's node.
  Runs a deterministic Logseq-format lint (`logseq.py`) plus an injectable content
  check (`recall.py`; Claude for complexity + correctness). It critiques; you author.

## Public agent, private data

This repo is built in public, but career data is not. The committed corpus is a
**synthetic stub** (`data/jd-gaps.stub.yaml`) with illustrative numbers — the
public eval runs against it. The real corpus (real JD frequencies + self-assessment)
is private and wired in via an env override, never committed:

```bash
# Relative paths resolve against the repo root (keep the real corpus in a sibling repo):
export LTS_CORPUS_PATH=../private-corpus/jd-gaps.real.yaml   # unset = the stub
```

## Run it

```bash
uv sync

# Rank the bundled example study list
uv run python -m learn_to_ship

# Rank your own list, as JSON
uv run python -m learn_to_ship --candidates data/study-candidates.stub.yaml --json

# Rank your Logseq queue page directly — no retyping. You triage #inbox onto
# the page (default [[Learning/Queue]], override LTS_QUEUE_PAGE); it only reads:
uv run python -m learn_to_ship rank --queue
```

Every rank ends with the **inverse view**: uncovered priority gaps your list
is silent about — rank can only order what you captured, so the silence is the
most valuable signal. Ask for drafts to close them (needs an LLM
key — DeepSeek or Anthropic, see `.env.example`; prints paste-ready queue
bullets — nothing is ever written to your vault):

```bash
uv run python -m learn_to_ship propose --queue
```

Candidate list format (`data/study-candidates.stub.yaml`) — a plain list; the agent
picks up *after* you capture items, it does not capture for you:

```yaml
candidates:
  - id: k8s-deploy
    title: Containerize a service and deploy it to Kubernetes
    tags: [docker, kubernetes, deploy]
```

## Recall check (v1) — you author cards, it checks them

The other half of the learning loop: study → produce an output → recall. Active
recall works *because you phrase the card yourself*, so learn-to-ship never
generates cards — you write them, in canonical Logseq `#card` format, and a
second graph (`card-reviewer`) checks each one:

- **format** (deterministic, no key) — bilingual EN+中文 present, tag order,
  valid `#q/why|how|apply`.
- **complexity + correctness** (the configured LLM — DeepSeek or Claude, see
  `.env.example`) — is it one atomic idea? is the answer
  right / supported by your source? It flags problems; it never rewrites.

```bash
# Check today's journal straight from your Logseq vault
# (set LTS_VAULT_PATH in .env — the folder that contains journals/):
uv run python -m learn_to_ship recall --today
uv run python -m learn_to_ship recall --journal 2026-07-07

# Or point at any file — or a directory, scanned for #card blocks:
uv run python -m learn_to_ship recall --cards path/to/cards.md
uv run python -m learn_to_ship recall --cards path/to/vault/journals

# Format checks alone need no key. With an LLM key (in .env) you also get
# complexity + correctness; --material grounds correctness in your source:
uv run python -m learn_to_ship recall --today --material notes/langgraph.md
```

Local-only (needs your key; the hosted deploy stays rank-only). Cards look like:

```text
- Why rank by leverage, not JD frequency? 为什么按 leverage 而非 JD 频率排序？ #card #lts #lts/ranking #q/why
	- Leverage folds frequency × distance-from-level. Leverage 综合频率×水平差距。
```

## Usage evidence (v1.2) — the loop, made visible

`rank` and `recall` runs auto-log to a **private, gitignored** JSONL trail
(`data/evidence.jsonl`; override with `LTS_EVIDENCE_PATH`). Record an output
you shipped, and the trail links the whole loop — rank → output → recall —
ending in a nudge to update your corpus levels (that update stays yours):

```bash
uv run python -m learn_to_ship evidence --item k8s-deploy \
  --output https://github.com/you/thing --note "deployed with health check"

uv run python -m learn_to_ship evidence      # show the trail
```

Local-only: the hosted server never writes evidence.

## Serve it (deployed endpoint)

```bash
uv run langgraph dev            # local API server on :2024

curl -X POST localhost:2024/runs/wait \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"focus_director","input":{"candidates":[
        {"id":"a","title":"Deploy to a cloud container","tags":["cloud","deploy"]}]}}'
```

`langgraph.json` registers the `focus_director` graph for
[LangGraph Platform](https://langchain-ai.github.io/langgraph/cloud/) deployment.

## Test / lint / eval

```bash
uv run pytest            # hermetic: ranker, MCP round-trip, golden eval, card parse/lint
uv run pytest -m live    # also runs the real-LLM checks (needs a configured key)
uv run ruff check .
```

CI (`.github/workflows/ci.yml`) runs lint + the hermetic suite on every push. The
golden eval pins the full ranked order against `evals/cases.yaml`; a ranking
regression fails the build. Everything in CI is hermetic — no API key, no network:
the recall checker's Claude call sits behind an injectable stub, and the `live`
tests (real Claude) are deselected by default.

## Status

- [x] v0 focus-director graph (LangGraph, one node, deterministic ranker)
- [x] JD-gap corpus consumed via an MCP tool
- [x] CI eval harness (GitHub Actions) — a failing eval fails the build
- [x] Runs as a served endpoint (`langgraph dev`); deploy config in `langgraph.json`
- [x] Real private corpus wired for daily use via `LTS_CORPUS_PATH`
- [x] Cloud-deployed as a live endpoint (Hugging Face Spaces) — see `DEPLOY.md`
- [x] v1 recall loop — `card-reviewer` graph checks your hand-written cards
      (format + complexity + correctness), local-only

**v0 complete; v1 recall-checker shipped.** See `spec.md` for scope, `DEPLOY.md`
to reproduce the deploy, `LOG.md` for the build trail.
