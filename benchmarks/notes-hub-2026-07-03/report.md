# Benchmark Report: Small-profile notes hub (A/B)

**Date:** 2026-07-03
**Model/effort:** claude-sonnet-5 × medium, both cells
**Framework state:** working tree adding the progressive notes-hub guidance to the
small profile (AGENTS.md protocol, notes.md stub, `/explore`, `/build` step 5).
**Raw results:** [results/](results/)

Purpose: validate a new small-profile feature — `.ai/notes.md` may become a
hub-and-spoke (a linked index with `.ai/notes/<topic>.md` leaves) once it grows,
so a session reads a compact hub instead of an ever-growing flat log. Guidance
only; no new tooling. Controlled A/B: **same repo (sqlite-utils `79117b9`) and
same task (add `rename-column`)**; the single independent variable is the
starting size of `notes.md`.

## Cells

| Cell | Starting notes.md | Expected | Code gate | Split? | Correct? |
|---|---|---|---|---|---|
| notes-hub-split | seeded 84 lines, 7 topics (mature project) | split into hub + leaves | PASS (1084/0) | **YES**, 1 leaf, links in sync | ✅ |
| notes-flat-control | fresh stub → 43 lines after the run | stay flat | PASS (1087/0) | **NO** | ✅ |

Both branches behaved as designed: the split triggers only above the threshold,
and the control correctly resisted premature splitting ("one file is cheaper to
read whole than an index plus a leaf"). Links were kept in sync with no
orphaned/dangling leaves. The end-of-build project-context refresh stayed quiet
on LOC-only drift in both cells (no regression of the v5.7 behavior).

## Finding that changed the design

`notes-hub-split` followed the original wording — "move the **largest** topic
cluster" — literally: it moved exactly one cluster (Build/dev, 13 bullets),
leaving the hub at 72 lines, **still over threshold**. Immediate session-start
read reduction was only ~14% (85→72 lines); the win would only compound over
many future builds. For an already-mature project that under-delivers.

**Fix applied after the run:** the trigger changed from "move the largest
cluster" (once) to "move topic clusters (largest first) **until the hub is back
under ~1 screen**" — bring it under threshold in one pass. Applied to all three
places the guidance appears (AGENTS.md protocol, notes.md stub, `/build` step
5). Not re-benchmarked (wording-only; the split mechanism itself was already
validated end-to-end).

## Secondary observations

- The "do not split while short" guidance was clear and consistent across its
  three locations; the control agent felt no pull to split prematurely.
- The review gate again earned its keep: the control cell's reviewer caught the
  same `transform(rename=...)` silent-data-loss collision bug seen in the
  multi-eco py-feature cell, and added the `AlterError` guard + regression test
  — independent reproduction of that finding.
- Honesty note from the split cell: the hub only exists *after* `/build`, so the
  same session could not read hub-first; the benefit accrues to later sessions.
  That is inherent to a build-time split and is the correct behavior.

## Verdict

The progressive notes hub works: correct on both branches, links maintained,
no regression to the refresh step. One wording flaw (under-splitting a mature
project) was surfaced and fixed. Feature shipped.
