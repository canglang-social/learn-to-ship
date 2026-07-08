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
