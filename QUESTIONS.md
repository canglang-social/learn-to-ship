# QUESTIONS.md — user-question log

Questions Felix asks *as a user* of learn-to-ship, recorded verbatim-ish and
then distilled, because they direct product design. When a question turns into
a scope decision, the decision lands in `spec.md` (the source of truth) and
this entry links to it — this file records the *demand signal*, not the spec.

Rules for this file:

- Capture the question as asked (refined for grammar), plus the underlying
  need — what the user was actually trying to do when the question arose.
- Note the design implication as a hypothesis, not a commitment.
- Never record real career-corpus data here; this repo is public.

Format per entry:

```
## Qn · YYYY-MM-DD — <short title>
- **Asked:** <the question, refined>
- **Underlying need:** <what the user was trying to do>
- **Design implication (hypothesis):** <what this suggests we build/change>
- **Status:** open | answered | folded into spec.md §…
```

---

<!-- Entries below, newest first. -->

## Q9 · 2026-07-09 — Where is my-study.yaml from, and why the inconsistent naming?

- **Asked:** Candidates now come from the inbox → [[Learning/Queue]] page —
  so where is `data/my-study.yaml` from? Is it the local version of
  `study-candidates.yaml`? And why not mark the pair with `.stub`/`.example`
  and `.real`, like the corpus files?
- **Answer (facts):** `my-study.yaml` predates the queue feature — created
  in the v0 "real corpus wired for daily use" phase as the private daily
  input; never committed (the `data/my-*.yaml` gitignore pattern covers it),
  so it exists only in the local checkout. Yes: it is exactly the private
  counterpart of the committed example `study-candidates.yaml`. Since v1.4,
  `rank --queue` is the primary input and `my-study.yaml` is an ad-hoc
  fallback via `--candidates`.
- **Why the inconsistency (honest answer):** historical accident, not
  design. The corpus pair got `.stub`/`.real` because the public/private
  split was a hard rule from commit one; the candidates example was named as
  *format documentation*, and the private file grew organically with an
  ownership prefix (`my-`). Two naming philosophies collided: data-kind
  marking vs ownership marking. The user is right that one scheme is better.
- **Design implication (hypothesis):** unify on the corpus scheme —
  `data/study-candidates.stub.yaml` (committed, paired with the stub corpus)
  + `data/study-candidates.real.yaml` (gitignored); one ignore pattern
  `data/*.real.yaml` then covers all private data files; keep `data/my-*`
  ignored for back-compat so nothing ever leaks. Update `DEFAULT_CANDIDATES`
  and docs. Low value for daily use (the queue is primary now), but worth it
  for the repo's coherence as a portfolio artifact — a stranger reading
  `data/` should grasp the public/private split instantly.
- **Status:** decided 2026-07-09 — user approved ("rename"); shipped:
  `study-candidates.stub.yaml` (committed) / `study-candidates.real.yaml`
  (private, renamed locally too), ignore pattern `data/*.real.yaml`, all
  references updated. Origin question also answered: my-study.yaml was
  hand-authored on 2026-07-06 by the v0 build session (Felix + Claude)
  transcribing his real plans — not derived from the job_hunting repo,
  which supplies only the corpus side.

## Q8 · 2026-07-08 — Use DeepSeek first; maybe Anthropic later

- **Asked:** Add an API change: I want to use DeepSeek first, to test. Maybe
  we can change to the Anthropic API later.
- **Underlying need:** Cost control while the LLM features (card checks,
  gap proposals) are being tried daily — test cheap, upgrade deliberately.
  The switch back must not require code changes.
- **Answer given / shipped (v1.6):** the two LLM seams now build their model
  through one module (`llm.py`): `LTS_LLM_PROVIDER = auto | deepseek |
  anthropic` (auto prefers DeepSeek when `DEEPSEEK_API_KEY` is set, else
  Anthropic), `LTS_LLM_MODEL` optionally overrides the per-provider default
  (`deepseek-chat` / `claude-sonnet-5`). Switching later = one line in
  `.env`. Hermetic CI unchanged — the stubs never call any provider.
- **Status:** decided 2026-07-08 — user requested directly; shipped as v1.6.

## Q7 · 2026-07-08 — The queue is only my KNOWN learning; gaps should propose items

- **Asked:** The inbox/queue is just my known learning. We have many gaps —
  I need to learn against the real gaps, right? We should convert gaps into
  the study list in the future.
- **Underlying need:** rank is a *filter*: it can only order what the human
  already captured. A gap with no queue item is invisible — rank never says
  "your #1 gap has nothing addressing it." Live evidence from the first
  real run (same day): the queue's top item unblocked gap **#2** — meaning
  nothing in the queue touches gap #1, and the tool stayed silent about it.
- **Design implication (hypothesis, two stages):**
  1. *Coverage report (deterministic, no LLM):* run the matcher in reverse —
     for each priority gap, does ANY queue item unblock it? Print uncovered
     priority gaps after every rank ("uncovered: gap #1 …"). Pure signal
     from existing machinery.
  2. *Gap→proposal drafts (Claude, local-only, later):* for uncovered gaps,
     draft 2–3 candidate study items (title + tags) as *suggestions* the
     human triages onto the queue page themselves. Boundary: the agent
     proposes text in the terminal; it never writes to the vault — choosing
     and capturing stay human. (Unlike cards, proposing study *directions*
     is the product's core job — advise at entry.)
- **Status:** decided 2026-07-08 — user approved both stages the same day;
  shipped as v1.5. Stage 1: `uncovered` in every rank surface (CLI, JSON,
  API, front page) — the first real run immediately exposed that gap #1 had
  nothing in the queue. Stage 2: `propose [--queue]` (third graph,
  gap_proposer) drafts paste-ready queue bullets via Claude; degrades to
  coverage-only without a key; the vault is never written.

## Q6 · 2026-07-08 — Read my triaged queue page directly

- **Asked:** I need the tool to auto-read my inbox — actually it's already
  triaged into the [[Learning/Queue]] page in my Logseq. Maybe an env var to
  record the page, and an import/convert into the system.
- **Underlying need:** Kill the manual transfer step. The human already
  captures AND triages (routes A–C onto the queue page, Route D to
  Incubation); retyping queue items into `data/my-study.yaml` is pure
  friction the machine can absorb without touching either human step.
- **Design note (parse reality, not an imagined format):** the real page has
  an untasked header bullet, then items as `LATER`-marked bullets tagged
  `#learn` with `route::` / `from::` / `note::` property lines. The parser
  targets exactly that shape; untasked bullets are prose, not items.
- **Answer given / shipped:** `rank --queue` reads the vault page named by
  `LTS_QUEUE_PAGE` (default `Learning/Queue`, resolved via the existing
  `LTS_VAULT_PATH`; Logseq's `/`→`___` filename encoding handled). Items
  become StudyItems: stable slug ids, title with tags stripped, tags from
  inline #hashtags + [[refs]] + the `route::` value. Read-only — no file is
  ever written; `my-study.yaml` still works for ad-hoc lists. Verified live
  against the real vault + real corpus on day one.
- **Status:** decided 2026-07-08 — user requested directly; shipped as v1.4.

## Q5 · 2026-07-08 — Can the repo docs use the artifact's visual style?

- **Asked:** I like the style of the docs artifacts (teal/paper HTML pages).
  Can we just use that style in this repo?
- **Underlying need:** Reading experience. The rendered artifact pages read
  better than raw GitHub Markdown; the user wants that quality for the
  canonical in-repo docs, not just for one-off snapshots.
- **Constraint that shapes the answer:** GitHub does NOT render committed
  HTML — a checked-in artifact file shows as source code on github.com. So
  "the artifact style in the repo" needs a serving surface. The style is
  already partially in-repo: the front page (v1.1) deliberately reuses the
  same design system (palette, type, tokens).
- **Design implication (hypothesis):** Keep `docs/*.md` the single source of
  truth (GitHub still renders it, diffs stay reviewable), and let the
  existing FastAPI app render those same files as styled pages at
  `GET /docs/usage` and `GET /docs/development` — artifact stylesheet shared
  with the front page, mermaid.js for the diagrams. One small markdown
  dependency, one route; live on the Space and locally; no duplicated
  content, no drift. Alternative considered: GitHub Pages (a second deploy
  surface to maintain — the Space already exists).
- **Status:** decided 2026-07-08 — user approved ("merge and build");
  shipped as `GET /docs/{usage,development}` rendering the canonical
  `docs/*.md` with the shared theme (`static/theme.css`, extracted from the
  front page — the second use that justified extraction) + client-side
  mermaid. OpenAPI moved to `/api-docs`. Verified in a real browser.

## Q4 · 2026-07-08 — Everything is commands; a front page would be good

- **Asked:** Right now everything is CLI commands, not a user interface. For
  most users (including me), a front page would be good.
- **Underlying need:** Lower the interaction cost. Even the project's own
  author finds the command-line surface heavy for daily use (see Q2's
  100-character quoted path); a stranger evaluating the portfolio can't
  experience the agent at all without curl.
- **Assessment given:** This is a scope change — spec.md's non-goals say
  "No web UI / DB in v0" — but v0 is complete, so it is now legitimately
  discussable. Two distinct users want a UI for different reasons:
  (a) the portfolio visitor — a clickable hosted demo beats a curl snippet;
  (b) Felix daily — but Q2's vault-aware CLI defaults might serve him
  cheaper than a UI. Cheapest honest step: ONE static HTML page served by
  the existing FastAPI app, calling the existing POST /rank, no DB, no
  build toolchain, no framework — consistent with "no framework until a
  second use demands it." Recall UI stays local-only (needs the user's key;
  hosted deploy stays keyless by design).
- **Design implication (hypothesis):** v1.x candidate: `GET /` serves a
  minimal rank demo page (paste/edit candidates → ranked list with
  rationales) on the hosted stub corpus; same page works locally against
  the private corpus. Explicitly NOT: auth, DB, card-review UI on the
  hosted deploy. Update spec.md non-goals if adopted.
- **Status:** decided 2026-07-08 — user approved; shipped in PR #2 as one
  static page at `GET /` (health → `/health`), verified in a real browser;
  spec.md non-goal amended. Folded into spec.md "Resolved during v1.1".

## Q3 · 2026-07-08 — What's the middle — the learning itself?

- **Asked:** We have the corpus (input, which rank orders) and the cards
  (output, retrieval for learning). What is the middle — the learning?
- **Underlying need:** The user sees the system touches only the two ends of
  the loop and wants to know whether the middle is missing by accident or by
  design — i.e., what the product's actual boundary is.
- **Answer given:** The middle is human-owned *by design* — it is the one
  part that cannot be delegated without defeating the purpose, the same
  logic as never LLM-generating cards. Concretely the middle today is:
  ship an output for the top-ranked item (the output-driven thesis — this
  repo itself is an instance, built to close the LangGraph/cloud-deploy
  gaps) + Socratic study sessions (the agent-kit `learn` skill) + Logseq
  capture. The agent touches the middle only at entry (rank rationale) and
  exit (card check). v2's focus-guardian (keep-session-on-rails) is the
  planned middle-adjacent feature, deliberately deferred.
- **Design implication (hypothesis):** The middle is currently *invisible*
  to the system — nothing records that a ranked item was studied, what
  output shipped, or feeds evidence back into corpus levels. spec.md
  already lists this open question ("usage-evidence capture"). Hypothesis:
  a lightweight session-evidence link (study-item id → output link → cards
  authored) that closes the loop rank → learn → recall → corpus update,
  WITHOUT the agent directing the learning itself. Boundary to hold: the
  agent observes and advises around the middle; it never performs it.
- **Status:** decided 2026-07-08 — user approved as v1.2; shipped as
  usage-evidence capture (`evidence` subcommand + auto-logged rank/recall
  trail, private JSONL). Folded into spec.md "Resolved during v1.2". The
  boundary held: the agent reports the trail; corpus updates stay human.

## Q2 · 2026-07-08 — Where are my cards?

- **Asked:** Where are my cards? I tried to run
  `uv run python -m learn_to_ship recall --cards my-cards.md` (from the usage
  guide) and there is no such file.
- **Underlying need:** The user's cards live in their Logseq vault (journal
  pages, per the capture convention); they expected the tool to know that.
  `my-cards.md` in the docs was a placeholder, and nothing in the product
  bridges "where cards actually live" to the `--cards` flag. First-run
  friction: the happy-path command in the docs is not runnable as written.
- **Answer given:** `--cards` takes any file containing Logseq `#card`
  blocks; the real invocation is pointing it at a vault journal page
  (quoted — the iCloud vault path contains spaces). Verified live against
  the vault: it parsed the newest journal's card and flagged real format
  issues. Docs examples should use a runnable real-shaped path.
- **Design implication (hypothesis):** Make recall vault-aware, in line with
  the spec note that a "Logseq-page → list transform is a v1 concern":
  1. an `LTS_VAULT_PATH` (or `LTS_CARDS_PATH`) env default in `.env`, like
     the corpus override;
  2. a `--today` / `--journal [date]` flag resolving the vault's
     `journals/yyyy_MM_dd.md` naming;
  3. accept a directory (scan for `#card` blocks) instead of a single file.
  Capture stays Felix-owned either way — this is read-path convenience only.
- **Status:** decided 2026-07-08 — user approved; shipped in PR #2
  (`LTS_VAULT_PATH`, `--today`, `--journal DATE`, directory `--cards`),
  verified against the real vault. Folded into spec.md "Resolved during v1.1".

## Q1 · 2026-07-08 — Why keyword matching instead of semantic retrieval?

- **Asked:** Why match study items to gaps by keyword? From RAG retrieval,
  keyword matching is considered the weak approach (vs. embeddings), right?
- **Underlying need:** Trust the ranking — the user knows lexical matching has
  a vocabulary-mismatch problem ("k8s" ≠ "kubernetes") and wants to know
  whether the ranker silently misses matches the way sparse retrieval does.
- **Answer given:** This is not retrieval at scale — it is a ~10×8 matching
  problem over a corpus the user authors, where determinism is load-bearing:
  the golden eval pins the exact order, CI runs hermetic (no key, no network),
  and every match is explainable ("this tag hit this keyword"). Embeddings
  would buy recall the corpus doesn't need yet, at the cost of the eval,
  reproducibility, and a model dependency in the rank path. The RAG lesson
  applies when recall over large, heterogeneous, un-ownable text matters;
  here the fix for a miss is editing one YAML line you own. The vocabulary-
  mismatch risk is real and acknowledged: today it is mitigated by curating
  `keywords` per gap; the miss mode is visible (score 0.00, "No JD gap
  matched"), never silent.
- **Design implication (hypothesis):** If misses become frequent in daily
  use, add a *hybrid* second pass — deterministic keyword match first, then an
  optional LLM/embedding fallback ONLY for items that matched nothing, clearly
  labeled and kept out of the golden eval path. Also consider a `--explain`
  flag showing which keyword hit. Do not replace the deterministic core.
- **Status:** answered — watching daily use for miss frequency before any
  hybrid work.
