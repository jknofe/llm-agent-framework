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
- **New axes vs prior runs:** ecosystem (Python, Shell, C++/ROS 2) and task type
  (bugfix-from-failing-test, cross-file feature, refactor-with-invariants).
  No packaging task in this set on purpose.
- **Pass/fail anchor:** deterministic container checks only. A cell PASSes when
  its validation script exits 0 inside the named Docker image. Rubric-style
  quality dimensions are recorded but never decide PASS/FAIL.
- **Execution: strictly sequential.** Run one cell at a time; never dispatch
  cells in parallel (see [Execution](#execution-sequential-one-cell-at-a-time)).

## Execution (sequential, one cell at a time)

Run the cells **one after another**, not concurrently. Round 1 dispatched all
five in parallel and burned the usage window ~5x faster than serial, so four of
five cells stalled on a session limit mid-run and had to be resumed hours later
across two resets. Serial execution keeps a round inside one usage window and
makes each cell's outcome clean to attribute.

Procedure:

1. Pick the next cell in the order below. Dispatch exactly one agent for it.
2. Wait for it to finish: its results file exists under
   `/tmp/benchmark/results/<cell>.md` and the container gate has a recorded
   PASS/FAIL. Do not start the next cell before this.
3. If it stalls on a session limit, resume that same agent after the reset
   (its work dir and `.ai` state are intact); do not launch a duplicate into
   the same work dir. Only after it completes do you move to the next cell.
4. Record the result, then proceed to the next cell.

Recommended order (cheapest/fastest first, so a limited window still yields
results; heaviest ROS 2 cells last):

1. `sh-refactor-small` (fast, no package install)
2. `py-bugfix-small`
3. `py-feature-small`
4. `ros-refactor-large` (colcon build + test)
5. `ros-plan-large` (plan-only; heaviest explore, but no build of agent code)

Budget: at sonnet-5 medium a small cell is ~10-20 min and a large ROS 2 cell
~30-60 min including the colcon build, so a full serial round is roughly
2-3 h of wall time. If the window is tight, stop after any completed cell; a
partial round is still valid (report the cells that ran).

## Matrix

| Cell | Target repo | Profile | Effort | Task type | Image |
|---|---|---|---|---|---|
| py-bugfix-small | [sqlite-utils](https://github.com/simonw/sqlite-utils.git) | small | medium | bugfix from failing test | `python:3.12` |
| py-feature-small | sqlite-utils | small | medium | cross-file feature | `python:3.12` |
| sh-refactor-small | [bats-core](https://github.com/bats-core/bats-core.git) | small | medium | refactor with invariants | `bats-eco-builder` |
| ros-plan-large | [navigation2](https://github.com/ros-navigation/navigation2.git) (`jazzy`) | large | high | cross-file feature, explore+plan only | `ros2-nav2-builder` |
| ros-refactor-large | navigation2 (`jazzy`) | large | medium | refactor with invariants, single package | `ros2-nav2-builder` |

The ROS cells target **ROS 2 Jazzy** and the `navigation2` (Nav2) stack, built
with **colcon + ament** (not ROS 1 catkin — round 1 used `ros-planning/navigation`
on noetic; see [report.md](report.md) for that history). They follow the
large-profile session split (explore session commits KB, second session
plans/implements) — the lesson from satty-deb finding #4. `ros-plan-large`
stops after the plan-review gate, like ua-plan-2026-07-02: plan quality on a
large C++ stack is the signal; a full colcon build of an agent-written feature
is round-2 material.

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
  3-5 files spanning at least two areas (CLI + lib + tests for Python; a new
  Nav2 plugin class + its pluginlib XML export + package.xml/CMakeLists wiring +
  a bringup/config entry for ROS 2). Must be implementable without upstream
  context the repo does not contain, and must mirror an existing in-repo
  template (a sibling plugin).
- **Refactor with invariants (sh-refactor-small, ros-refactor-large):** extract
  or split a module/helper with zero behavior change. The existing test suite
  is the invariant: it must pass unmodified (test files untouched in the diff).

### Pinned briefs (pinned 2026-07-02)

| Cell | Pinned SHA | Brief | Notes |
|---|---|---|---|
| py-bugfix-small | sqlite-utils `79117b9` | "The test `tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table` fails. Find the root cause and fix it." | Seed: revert the `sqlite_utils/db.py` hunk of `1a28416` (detect_fts `content=[...]` vs `content="..."` LIKE pattern), keep the test. Symptom is `table "books_fts" already exists` — root cause is two hops away in `detect_fts`. Verified failing 2026-07-02 (1 failed, 46 passed). |
| py-feature-small | sqlite-utils `79117b9` | "Add a `rename-column` CLI command and a `Table.rename_column(old, new)` API method, mirroring the existing `rename-table` command / `rename_table()` pattern. Include tests and doc updates." | Gap verified: `rename-table` exists (`cli.py:1681`, `db.py:1233`), no column equivalent. May delegate to `transform()`. |
| sh-refactor-small | bats-core `5a7db7a` | "The function `abort()` is defined identically in `libexec/bats-core/bats`, `bats-exec-suite`, and `bats-gather-tests`. Deduplicate it into `lib/bats-core/common.bash` with zero behavior change. The existing test suite must pass unmodified." | Leave the per-formatter `bats_tap_stream_*` trio alone (callback interface, not duplication). **Round-1 correction:** only `bats` and `bats-exec-suite` are true duplicates; `bats-gather-tests`'s `abort()` has a different printf contract (same-name coincidence). The brief is kept verbatim as a deliberate wrong-premise probe: the round-1 agent detected and recorded the discrepancy, which is the desired behavior. |
| ros-plan-large | navigation2 `jazzy` (candidate `60e82db`; confirm SHA at run) | "Plan a new `nav2_behaviors` behavior plugin (a simple time-based motion, e.g. a fixed-duration `Wait`-style or `Spin`-style variant that does not already exist in `nav2_behaviors/plugins/`), mirroring an existing behavior: a class deriving `nav2_core::Behavior` via `TimedBehavior<ActionT>`, the `behavior_plugin.xml` pluginlib export, the corresponding `nav2_msgs` action if needed, `package.xml`/`CMakeLists.txt` wiring, and a `nav2_bringup` params entry enabling it." | Plan-only. Template: `nav2_behaviors/plugins/wait.{hpp,cpp}` (~127 LOC) + `behavior_plugin.xml`. **Pin at run:** verify the chosen behavior name is absent from `nav2_behaviors/plugins/` (existing: back_up, spin, wait, drive_on_heading, assisted_teleop). |
| ros-refactor-large | navigation2 `jazzy` (candidate `60e82db`; confirm SHA at run) | "In `nav2_velocity_smoother`, extract a self-contained helper (e.g. the per-axis velocity clamping / deadband math) out of the node class into its own free-function header + translation unit, with zero behavior change. The package's existing tests must pass unmodified (nothing under `nav2_velocity_smoother/test/` changes)." | Single-package; colcon build + `colcon test` of `nav2_velocity_smoother` is the invariant (2 test files). Pick the exact helper from the source at run. |

## Validation (deterministic, per cell)

Build the two custom images once (like `satty-deb-builder`):

```bash
docker build -t bats-eco-builder - <<'EOF'
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    shellcheck git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
EOF

docker build -t ros2-nav2-builder - <<'EOF'
FROM ros:jazzy
# colcon + rosdep + build essentials for Nav2. Per-package deps are resolved
# with rosdep at run time (Nav2 is large; installing the whole stack up front
# is wasteful). Jazzy is a current LTS, so no --include-eol-distros needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions python3-rosdep build-essential git \
    && rosdep init 2>/dev/null; rosdep update \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
EOF
```

The ROS 2 cells build only the touched package and its dependencies with
`colcon build --packages-up-to <pkg>`, not the whole Nav2 stack. Resolve that
package's deps first with
`rosdep install --from-paths src --ignore-src -y --rosdistro jazzy`.

Per-cell gates (all run with the work dir mounted at `/workspace`):

- **py-bugfix-small:** `pip install -e . pytest hypothesis && python -m pytest`
  (sqlite-utils uses PEP 735 dependency-groups, not a `[test]` extra) — the
  previously failing test now passes AND the full suite is green. Extra check
  outside the container: `git diff --stat` touches no test file.
- **py-feature-small:** full suite green including the agent's new tests;
  the repo's own lint config (whatever `pyproject.toml`/CI defines) is clean.
- **sh-refactor-small:** `bin/bats test` green AND
  `shellcheck` clean on every changed script AND `git diff` shows zero changes
  under `test/`.
- **ros-plan-large:** no container gate (plan-only). Deterministic checks:
  plan.md schema-valid (frontmatter keys, kb-commit present), every task file
  self-contained per the task-file format, affected files exist at the pinned
  SHA (and the chosen behavior name is confirmed absent from
  `nav2_behaviors/plugins/`), and `colcon build --packages-up-to nav2_behaviors`
  of the *unmodified* workspace succeeds once to prove the environment is real.
- **ros-refactor-large:** `colcon build --packages-up-to nav2_velocity_smoother`
  succeeds AND `colcon test --packages-select nav2_velocity_smoother` passes
  (`colcon test-result --verbose`) AND test sources untouched
  (`git diff` shows nothing under `nav2_velocity_smoother/test/`).

## What this set measures that the prior sets could not

| Question | Cell(s) |
|---|---|
| Do ecosystem-correctness criteria name the *right* linter outside Rust/Debian (ruff/pytest, shellcheck — not lintian/clippy)? | py-*, sh-* |
| Does explore->spec find a root cause, or does the agent patch symptoms? | py-bugfix-small |
| Does the review gate catch behavior drift when the criteria say "no behavior change"? | sh-refactor-small, ros-refactor-large |
| Does the large profile's KB/budget machinery pay off on a genuinely large C++ codebase (vs the ~7k-LOC Satty where it did not)? | ros-* |
| Does `parallel: ok` marking appear only where files are truly disjoint? | ros-plan-large |
| Does the project-context refresh step stay quiet when commands/module map did not move (LOC-only drift)? | all small cells |

## Orchestration: session limits and resume

Cells run serially (see [Execution](#execution-sequential-one-cell-at-a-time)),
so at most one cell is ever in flight. If that cell stalls on a session limit it
is not dead: resume the *same* agent after the reset (its context, work dir, and
`.ai` state are intact), then continue to the next cell only once it completes.
Never launch a fresh duplicate into the same work dir — in round 1 (which ran in
parallel, the practice this rework replaces) a duplicate relaunch collided with
a resumed original on py-bugfix; both agents detected the foreign edits and
converged, but do not rely on that. The resume path (`.ai/.current` + committed
`.ai` state) was validated by four real interruptions in round 1; serial
execution should make such stalls rare in the first place.

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
