# Benchmark Report: Multi-Ecosystem Test Set (Round 1)

**Date:** 2026-07-02/03 (runs spanned two session-limit resets)
**Runbook:** [runbook.md](runbook.md), briefs pinned at commit `256a58b`
**Framework state:** main at `2caf613` (project-context refresh + LOC rule + de-biased
linter examples)
**Model/effort:** claude-sonnet-5 x medium for all cells (runbook lists ros-plan at
high; the round was run uniformly at medium by request)
**Raw results:** [results/](results/)

Purpose: the empirical counterpart to the 2026-07-02 overfitting audit. Prior
benchmarks covered only Rust/cargo-deb packaging and an Angular plan-only run;
this round tests Python, Shell, and C++/ROS across bugfix, feature, and
refactor task types. No packaging task.

## Results

| Cell | Repo | Task | Gate | Result |
|---|---|---|---|---|
| py-bugfix-small | sqlite-utils | seeded FTS root-cause bugfix | pytest in python:3.12 | **PASS** 1080/0, tests/ untouched |
| py-feature-small | sqlite-utils | rename-column CLI + API | full suite + repo's own CI gates | **PASS** 1084/0, 7 files |
| sh-refactor-small | bats-core | dedup abort() into common.bash | bats suite + shellcheck, test/ untouched | **PASS** 479/479, zero new findings |
| ros-plan-large | navigation | back_up_recovery plan-only | 4 deterministic checks | **PASS** 4/4, host repo untouched |
| ros-refactor-large | navigation | extract MapServer from main.cpp | catkin build + rostest, test/ untouched | **PASS** 17/17 tests |

**5/5 PASS.** Every cell produced the correct `.ai` commit sequence for its
profile (small: 4 commits; large: 5).

## Key findings

### 1. No benchmark overfitting detected (the round's core question)

- **Ecosystem checks generalized.** py-feature named and ran the repo's own
  gates unprompted - pytest, mypy, flake8, black, cog --check, codespell.
  sh-refactor used shellcheck + the bats suite. No lintian/clippy reflex
  anywhere. The de-biased example list (`2caf613`) did its job.
- **Task types generalized.** Root-cause bugfixing (symptom two hops from
  defect), invariant-preserving refactors, and cross-file features all worked
  under the same skills that previously only saw packaging tasks.

### 2. The review gates caught three real defects across the round

- py-feature: reviewer refused a "documented quirk" assumption and forced a
  fix for a real data-loss bug (transform rename silently drops a column on
  name collision). Guard + tests + docs added.
- ros-refactor: plan review caught a missing include (`MapMode`) before any
  implementation - a guaranteed compile failure averted at plan time.
- ros-plan: plan review fixed 3 findings (include list, garbled expression,
  zero-Twist on collision abort) pre-commit.

### 3. Agents corrected the orchestrator's own errors

- sh-refactor: the pinned brief claimed abort() was identical in three
  scripts. The agent verified the bodies, found bats-gather-tests's version
  has a different printf contract, deduplicated only the true pair, and
  recorded the deviation as numbered assumptions. Evidence beat instructions.
- py-bugfix: found and fixed the *second* test pinning the exact params-dict
  key assignment (test_tracer), rejecting a naive fix that would have passed
  the named test only.

### 4. Cross-session resume worked under real interruption

Four of five cells hit a session limit mid-run and were resumed hours later.
All four recovered their position from `.ai/.current` + committed `.ai` state
+ git status without redoing work (sh-refactor needed only 6 tool calls to
finish after resume). This was the first uncontrived test of the resume
design; it held.

### 5. The project-context refresh step behaved correctly in all five cells

Fired 5/5 times post-build; every drift was LOC-only; AGENTS.md was left
unchanged 5/5 times per the "bare LOC delta is not actionable" rule
(`a0670f0`). No false-positive digest rewrites, no missed command changes
(none of these tasks moved commands - the satty v2 run remains the positive
case).

### 6. Large profile: worth it on the big repo, ceremony visible on scoped tasks

ros-plan built an 8-node KB with verbatim nav_core signatures - plan quality
directly traceable to KB content. ros-refactor (single-package change) used
the trivial path correctly but still carried KB overhead; its own observation:
fine for a first ticket on a fresh repo (KB amortizes), ceremony for a
one-shot.

## Operational fixes applied to the runbook after this round

1. **ros-nav-builder image was insufficient** - it cannot even configure
   map_server (missing tf2/Bullet/SDL/yaml-cpp dev packages) and `rosdep
   update` on EOL noetic requires `--include-eol-distros`. Dockerfile updated;
   validation no longer installs deps per-run.
2. **sh-refactor pinned brief corrected** - abort() is duplicated in two
   scripts, not three; bats-gather-tests is a same-name coincidence.
3. **Session-limit orchestration note** - a stalled parallel cell may resume
   after reset and collide with a relaunched duplicate (happened on
   py-bugfix; both agents detected the foreign edits and converged, but do
   not rely on that). Resume the stalled agent; never launch a second agent
   into the same work dir.

## Verdict

**Success.** The framework generalized cleanly to three new ecosystems and
three new task types at sonnet-5 medium; every deterministic gate passed; the
recent framework changes (refresh step, LOC rule, de-biased examples) all
validated under real conditions; and the failure modes found were in the
benchmark harness (image, brief, orchestration), not in the framework.
