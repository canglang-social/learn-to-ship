# User tests — what the human verifies by hand

`uv run pytest` proves the hermetic core on every push. This checklist covers
what CI *deliberately cannot* touch: the real vault, the real corpus, the real
LLM, and the live deploy. One row per user-facing behavior; re-verify a row
after changing its area, and update the date. (QUESTIONS.md Q11 — this file
exists so "what should I test next?" always has an answer.)

Conventions: **☑ date** = verified by hand on that day · **☐** = never
user-verified · *(auto)* = also exercised by `pytest -m live`.

## rank

| Behavior | How to test | Expect | Status |
| --- | --- | --- | --- |
| `rank --queue` against the real corpus | `uv run python -m learn_to_ship rank --queue` | queue items ranked, each citing a real gap with a rationale | ☑ 2026-07-08 |
| Coverage footer (v1.5) | same command | "Uncovered priority gaps" lists ladder gaps with no queue item | ☑ 2026-07-09 |
| YAML fallback | `… --candidates data/study-candidates.real.yaml` | same shape, from the file | ☐ |
| `--json` shape | `… rank --queue --json` | `{"ranked": …, "uncovered": …}` | ☐ |

## propose

| Behavior | How to test | Expect | Status |
| --- | --- | --- | --- |
| Drafts for uncovered gaps | `uv run python -m learn_to_ship propose --queue` | 2–3 pre-triage drafts per uncovered gap (`route-hint::`, no `LATER`) | ☑ 2026-07-09 |
| `--write` to the vault inbox | `… propose --queue --write`, then open `[[inbox/propose]]` | drafts appended below the header; re-run appends 0 (one batch per gap) | ☑ 2026-07-09 |
| Triage round-trip | route a draft A–D onto the queue, re-run `rank --queue` | the routed item now ranks; its gap leaves the uncovered footer | ☐ |

## recall

| Behavior | How to test | Expect | Status |
| --- | --- | --- | --- |
| Vault resolution | `… recall --journal 2026-07-07` / `--today` | finds the journal; loud error when no journal exists | ☑ 2026-07-08 |
| Format lint on real cards | any card file, no key needed | missing 中文 / tags / `#q/*` flagged | ☑ 2026-07-08 |
| LLM content checks *(auto)* | `uv run pytest -m live` | planted factual error + compound card both flagged | ☑ 2026-07-09 |
| Full check on YOUR OWN cards | write real cards, `… recall --today --material <source>` | complexity/correctness verdicts you agree with | ☐ |

## evidence  ← next up

| Behavior | How to test | Expect | Status |
| --- | --- | --- | --- |
| Auto-logging | just use rank/recall/propose, then `uv run python -m learn_to_ship evidence` | trail lists your runs with dates | ☐ (3 events already waiting) |
| Record a shipped output | `… evidence --item <id> --output <url> --note "…"` (the id = the slug rank shows) | "Recorded: <id> → <url>" | ☐ |
| The nudge | `… evidence` again | output listed under its item + "consider updating their levels in your corpus" | ☐ |

## LLM provider

| Behavior | How to test | Expect | Status |
| --- | --- | --- | --- |
| DeepSeek end to end *(auto)* | `uv run pytest -m live` with `DEEPSEEK_API_KEY` | 3 live tests pass | ☑ 2026-07-09 |
| Anthropic switch | set `LTS_LLM_PROVIDER=anthropic` + key, re-run `pytest -m live` | same 3 pass on Claude | ☐ |

## Hosted demo

| Behavior | How to test | Expect | Status |
| --- | --- | --- | --- |
| Front page ranks | open <https://vegekiwi-learn-to-ship.hf.space>, click **Rank my list** | ranked demo list with rationales | ☑ 2026-07-08 |
| Uncovered gaps on the page (v1.5) | same, after the next Space rebuild | dashed "Uncovered priority gaps" card under results | ☐ (needs rebuild) |
| Styled docs | `/docs/usage`, `/docs/development`, `/docs/learning-loop` | artifact-styled pages, atlas diagrams drawn | ☑ 2026-07-09 |
