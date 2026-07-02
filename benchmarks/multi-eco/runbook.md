# Benchmark Runbook: Multi-Ecosystem Test Set

**Purpose:** validate that the framework is versatile across ecosystems and task
types, not tuned to the two scenarios benchmarked so far (Rust/cargo-deb
packaging on Satty, Angular plan-only on Understand-Anything). Motivated by the
2026-07-02 overfitting audit (commit `2caf613`): the audit was static; this set
is the empirical counterpart.

**Shared mechanics:** agent-prompt skeleton, effort tiers, results-file format,
and session-limit handling are inherited from
[../satty-deb-2026-07-01/runbook.md](../satty-deb-2026-07-01/runbook.md).
This file defines only what differs: targets, task briefs, and validation.

---

## Design

- **Matrix:** 5 cells, one model per round (focused profile: fits ~1-2 h wall
  time, cheap enough to run per framework change).
- **New axes vs prior runs:** ecosystem (Python, Shell, C++/ROS) and task type
  (bugfix-from-failing-test, cross-file feature, refactor-with-invariants).
  No packaging task in this set on purpose.
- **Pass/fail anchor:** deterministic container checks only. A cell PASSes when
  its validation script exits 0 inside the named Docker image. Rubric-style
  quality dimensions are recorded but never decide PASS/FAIL.

## Matrix

| Cell | Target repo | Profile | Effort | Task type | Image |
|---|---|---|---|---|---|
| py-bugfix-small | [sqlite-utils](https://github.com/simonw/sqlite-utils.git) | small | medium | bugfix from failing test | `python:3.12` |
| py-feature-small | sqlite-utils | small | medium | cross-file feature | `python:3.12` |
| sh-refactor-small | [bats-core](https://github.com/bats-core/bats-core.git) | small | medium | refactor with invariants | `bats-eco-builder` |
| ros-plan-large | [navigation](https://github.com/ros-planning/navigation.git) (`noetic-devel`) | large | high | cross-file feature, explore+plan only | `ros-nav-builder` |
| ros-refactor-large | navigation | large | medium | refactor with invariants, single package | `ros-nav-builder` |

ROS cells follow the large-profile session split (explore session commits KB,
second session plans/implements) — the lesson from satty-deb finding #4.
`ros-plan-large` stops after the plan-review gate, like ua-plan-2026-07-02:
plan quality on a ~1M-LOC-class C++ stack is the signal; a full catkin build of
an agent-written feature is round-2 material.

## Task briefs

Concrete briefs are **pinned at first run** by the orchestrator and recorded
below, so later rounds compare like against like. Selection protocol per type:

- **Bugfix from failing test (py-bugfix-small):** pick a merged, self-contained
  bugfix commit in the target's history touching ≤2 source files that has an
  accompanying test. Clone at a pinned SHA *after* that fix, revert the source
  change but keep the test (the suite now fails deterministically). Brief given
  to the agent: "test `<id>` fails; find the root cause and fix it." Record the
  reverted commit SHA and the patch here. The agent must not be told the
  reverted commit.
- **Cross-file feature (py-feature-small, ros-plan-large):** a feature touching
  3-5 files spanning at least two areas (CLI + lib + tests for Python; two
  nav packages or plugin + config for ROS). Must be implementable without
  upstream context the repo does not contain.
- **Refactor with invariants (sh-refactor-small, ros-refactor-large):** extract
  or split a module/helper with zero behavior change. The existing test suite
  is the invariant: it must pass unmodified (test files untouched in the diff).

### Pinned briefs (fill at first run)

| Cell | Pinned SHA | Brief | Notes |
|---|---|---|---|
| py-bugfix-small | _tbd_ | _tbd_ | reverted commit: _tbd_ |
| py-feature-small | _tbd_ | _tbd_ | |
| sh-refactor-small | _tbd_ | _tbd_ | |
| ros-plan-large | _tbd_ | _tbd_ | |
| ros-refactor-large | _tbd_ | _tbd_ | |

## Validation (deterministic, per cell)

Build the two custom images once (like `satty-deb-builder`):

```bash
docker build -t bats-eco-builder - <<'EOF'
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    shellcheck git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
EOF

docker build -t ros-nav-builder - <<'EOF'
FROM ros:noetic
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-catkin-tools python3-rosdep build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
EOF
```

Per-cell gates (all run with the work dir mounted at `/workspace`):

- **py-bugfix-small:** `pip install -e '.[test]' && pytest` — the previously
  failing test now passes AND the full suite is green. Extra check outside the
  container: `git diff --stat` touches no test file.
- **py-feature-small:** full suite green including the agent's new tests;
  the repo's own lint config (whatever `pyproject.toml`/CI defines) is clean.
- **sh-refactor-small:** `bin/bats test` green AND
  `shellcheck` clean on every changed script AND `git diff` shows zero changes
  under `test/`.
- **ros-plan-large:** no container gate (plan-only). Deterministic checks:
  plan.md schema-valid (frontmatter keys, kb-commit present), every task file
  self-contained per the task-file format, affected files exist at the pinned
  SHA, `catkin_make` of the *unmodified* workspace succeeds once to prove the
  environment is real.
- **ros-refactor-large:** `catkin_make` (or `catkin build` of the touched
  package) succeeds AND the package's existing rostest/gtest suite passes AND
  test sources untouched.

## What this set measures that the prior sets could not

| Question | Cell(s) |
|---|---|
| Do ecosystem-correctness criteria name the *right* linter outside Rust/Debian (ruff/pytest, shellcheck — not lintian/clippy)? | py-*, sh-* |
| Does explore->spec find a root cause, or does the agent patch symptoms? | py-bugfix-small |
| Does the review gate catch behavior drift when the criteria say "no behavior change"? | sh-refactor-small, ros-refactor-large |
| Does the large profile's KB/budget machinery pay off on a genuinely large C++ codebase (vs the ~7k-LOC Satty where it did not)? | ros-* |
| Does `parallel: ok` marking appear only where files are truly disjoint? | ros-plan-large |
| Does the project-context refresh step stay quiet when commands/module map did not move (LOC-only drift)? | all small cells |

## Quality dimensions (recorded, not gating)

- Bugfix: root cause named in spec; diff minimal (no unrelated hunks);
  regression test added or existing test cited.
- Feature: decomposition sanity (task count vs file count), interfaces stated
  in task files, new tests meaningful.
- Refactor: invariance argued in the spec (not just asserted), review gate
  explicitly re-ran the suite, no test-file edits.
- All: `.ai` commit sequence complete; assumptions numbered and evidence-cited;
  correct ecosystem linter named in criteria unprompted.

## Evaluation checklist

```
[ ] cell validation script exit 0 (or ros-plan deterministic checks all true)
[ ] .ai commit sequence matches profile (small: init->explore->spec->build;
    large: init->explore->ticket->plan[->implement])
[ ] results file written per satty runbook format
[ ] quality dimensions table filled
[ ] no test files modified in refactor cells
[ ] pinned-brief table above filled/confirmed for the round
```
