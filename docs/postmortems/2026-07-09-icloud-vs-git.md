# Postmortem — iCloud vs git: two strikes in two days (2026-07-08/09)

The repos on this machine live under `~/Documents/GitHub`, and `Documents` is
iCloud-synced. iCloud's conflict resolution duplicates files Finder-style
(`name 2.ext`) — including *inside git working trees and `.git` itself*. That
produced two incidents in two days, one of which briefly published a stray
file to this public repo. Recorded here as an engineering postmortem **and as
a founding bug for the (planned) file-management project** — this is exactly
the class of problem that project should own.

## Incident 1 — the corrupt ref (2026-07-08)

- **Symptom:** `git fetch` failed repo-wide: `fatal: bad object refs/heads/main 2`.
- **Cause:** a file literally named `main 2` (space included) inside
  `.git/refs/heads/`, created ~07-06 by iCloud duplication, pointing at an
  object that didn't exist. Git ignored it as a broken ref name *except*
  during fetch negotiation, which it broke entirely.
- **Fix:** deleted the bogus ref file; the real `main` ref was untouched.
- **Note:** `.gitignore` cannot protect `.git` internals — nothing inside
  `.git/` is guardable from within git.

## Incident 2 — the published duplicate (2026-07-09)

- **Symptom:** `git pull` in the main checkout materialized `QUESTIONS 2.md`
  — a stale snapshot of the question log, committed and pushed to the
  **public** repo.
- **Cause chain:** iCloud duplicated `QUESTIONS.md` inside the *worktree*;
  the v1.7 feature commit used `git add -A`, which swept the stray file in;
  review didn't catch it among an 11-file feature diff.
- **Fix:** the file removed; `* 2.*` and `*\ 2/` added to `.gitignore` so
  this class can never be tracked again.
- **Luck factor:** the duplicate was a public file's snapshot. Had iCloud
  duplicated a `*.real.yaml` before the Q9 ignore-pattern unification,
  `git add -A` could have published private career data. The ignore patterns
  (`data/*.real.yaml`, `data/my-*`, now `* 2.*`) are the layered defense.

## Lessons

1. **iCloud-synced folders are hostile territory for git.** Sync races
   duplicate files in working trees and corrupt `.git` internals; gitignore
   can only defend the first.
2. **`git add -A` is a leak vector in synced directories** — especially for
   automation/agents. Prefer explicit paths, or check `git status` for
   unexpected files before staging broadly.
3. **Duplicates are silent until they break something.** The `main 2` ref sat
   dormant for two days; the file duplicate shipped in a routine commit.
   Detection needs to be proactive, not incidental.

## Remediation state

- [x] Corrupt ref removed (07-08); fetch restored.
- [x] `QUESTIONS 2.md` removed from the repo; duplicate-pattern gitignore
      guard in place (this PR).
- [ ] **Root cause open:** the repos still live under iCloud sync. Options:
      move `~/Documents/GitHub` outside `Documents` (e.g. `~/Projects`), or
      rename to `GitHub.nosync` (iCloud skips `.nosync`). Machine-level —
      owner's call.

## Hint for the file-management project

This is a founding bug: the real problem is **no policy layer between "what
syncs" and "what versions"**. A file-management project worth building would:

- define *placement policy* — code repos, vaults, and sync-managed documents
  each get a home, and the homes don't overlap;
- *detect* Finder/iCloud duplicates (`name 2.ext`, `name 2/`) across managed
  trees and flag or quarantine them before a tool trips on them;
- *audit* git repos for sync-hazard placement (a repo inside an
  iCloud/Dropbox/OneDrive scope is a lint error);
- treat `.git` internals as a protected zone no sync layer may touch.

Two dated incidents, one near-miss with private data, and a concrete feature
list — that's the project's opening `spec.md` material.
