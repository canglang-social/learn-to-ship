# Postmortem — the stuck v1.3 deploy (2026-07-08)

Two stacked failures turned a routine docs deploy into a 40-minute
incident: a real packaging bug in our code, then a platform wedge that
survived the fix. Written up both as an engineering record and as a
case study in human ↔ AI-agent division of labor.

## Timeline (UTC)

| Time | Event |
| --- | --- |
| 05:14 | v1.3 merged (styled `/docs` routes); factory rebuild #1 triggered |
| 05:17 | New container starts… and silently crashloops; old v1.2 keeps serving |
| 05:2x | Diagnosis: `{"detail":"Not Found"}` on `/docs/usage` proves the *old* app is answering |
| 05:30 | Root cause #1 reproduced locally: `uv sync --no-editable` + import from a neutral cwd → `FileNotFoundError: site-packages/docs/USAGE.md` |
| 05:35 | Hotfix PR #7 merged: `docs/` force-included into the wheel as `learn_to_ship/_docs`; server resolves whichever location exists |
| 05:36 | Factory rebuild #2 — build succeeds, image pushed |
| 05:36–05:55 | Space wedged in `RUNNING_APP_STARTING`; container log shows a startup marker and *nothing else*; plain Restart doesn't help |
| ~05:5x | Agent-side proof of innocence: fresh clone of `main` built and run as a real Linux container locally — boots in ~12 s, serves `/docs/usage → 200` |
| ~06:0x | Human commits a one-line cache-bust comment to the Space's Dockerfile → genuinely fresh build+deploy → replica finally rotates |
| 06:0x | All endpoints verified live: `/`, `/health`, `/rank`, `/docs/*`, `/static/theme.css` |

## Root cause #1 — ours: docs weren't in the wheel

The `/docs` routes rendered `docs/*.md` resolved relative to the repo
root (`Path(__file__).parent.parent / "docs"`). Locally `uv sync`
installs the project **editable**, so `__file__` lives in the source
tree and the path exists. The deploy container installs
**non-editable**: `__file__` lives in `site-packages`, `docs/` doesn't
exist there (the wheel only packaged `learn_to_ship/`), and the render
ran **at import time** — so the app raised `FileNotFoundError` before
uvicorn printed a single line.

Fix (PR #7): hatch `force-include` ships `docs/` inside the wheel as
`learn_to_ship/_docs`; the server resolves repo-root `docs/` (source
checkouts) or the in-wheel copy (installs), and fails loudly if
neither exists.

## Root cause #2 — theirs: the Space wedged after the fix

Even with a correct image built at 05:36, the Space sat in
`RUNNING_APP_STARTING` for ~20 minutes: the old replica kept serving,
the new one never went healthy, and neither factory rebuild nor plain
restart cleared it. A one-line commit to the Space repo's Dockerfile
(a comment above the `git clone` layer) forced a fully fresh
build-and-deploy cycle, which rotated the replica at last.

## What made it hard: the observability trap

**HF Space container logs hide stderr.** Python tracebacks and uvicorn
logs both go to stderr — so a crashlooping app and a healthy-but-stuck
deploy look *identical*: one startup marker, then silence. The log
panel in the browser also kept aborting its stream. Conclusion:
platform logs could not distinguish our bug from their wedge; only
local reproduction could.

## The diagnostic ladder that worked

1. `{"detail":"Not Found"}` — FastAPI's *default* 404, not our custom
   one → the responding app has no `/docs` route at all → old
   container still serving. (Read error shapes, not just status codes.)
2. Reproduce the container's install mode locally:
   `uv sync --no-editable`, then import from a **neutral cwd**
   (`python -c` puts the cwd on `sys.path` and silently masks the
   test — first attempt "passed" wrongly).
3. After the fix, prove innocence at increasing fidelity: fresh clone
   + frozen sync + uvicorn (macOS) → then the real Dockerfile in a
   real Linux container. Same code, ~12 s boot, 200.
4. With code exonerated and logs blind, the remaining suspect is the
   platform → force the freshest possible deploy path.

## Division of labor — what each side could and couldn't do

- **Agent could:** notice the 404 shape, reproduce both install modes,
  ship the packaging fix end-to-end (repro → fix → tests → PR → CI →
  merge), build the real container locally, and rule out every code
  explanation.
- **Agent could not:** see stderr on the platform, and — by design —
  edit production deploy config autonomously. The permission system
  blocked the agent mid-edit of the Space's Dockerfile (and the
  blocked keystroke would have corrupted the file: the edit landed on
  the wrong line). The agent discarded the state, verified nothing was
  committed, and handed the decision back with three options.
- **Human did:** the 30-second production act — one commented line in
  the Space Dockerfile, committed via the web UI — plus the judgment
  call that it was worth doing.

The boundary held exactly where it should: the agent owns diagnosis,
reproduction, and reversible code changes; the human owns production
keys and the final unstick.

## Lessons

1. **Test the install mode you ship.** Editable dev installs hide
   packaging bugs; one `uv sync --no-editable` + import-from-elsewhere
   in CI would have caught this before deploy.
2. **Never do fallible I/O at import time** without a loud, early
   failure story — a crash before logging is the worst failure mode on
   a platform that hides stderr.
3. **Local reproduction beats platform logs.** One real container run
   answered what 20 minutes of log-staring could not.
4. **`python -c` self-tests lie** — the cwd is on `sys.path`; test
   installed packages from a neutral directory.
5. **Verify the artifact, not the status note** (same-day rhyme: spec
   said the blog post was unpublished; it had been live for two days).
6. **Platform wedges are real**: keep a "smallest commit that forces a
   fresh deploy" trick in the runbook.
7. **Permission guardrails are a feature.** The blocked edit would
   have shipped a corrupted Dockerfile; the deny forced a cleaner path
   and put the production change in human hands.
