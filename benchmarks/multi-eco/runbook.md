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

- **Matrix:** 7 cells, one model per round. Five **anti-overfitting** cells
  (Python, Shell, C++/ROS 2 × bugfix/feature/refactor) plus the two original
  **reference scenarios** folded in — Satty (Rust packaging) and
  Understand-Anything (TypeScript/Angular plan-only) — so this one list spans
  every ecosystem and task type the framework has been benchmarked on.
- **Ecosystems:** Python, Shell, Rust, TypeScript/Angular, C++/ROS 2.
  **Task types:** bugfix-from-failing-test, cross-file feature, refactor-with-
  invariants, packaging.
- **The anti-overfitting claim rests on the five non-reference cells** (no
  packaging, not Rust or Angular): the two reference cells are included for
  regression coverage and cross-scenario comparison, not to prove versatility.
- **Pass/fail anchor:** deterministic container checks only (plan-only cells use
  static plan checks). A cell PASSes when its validation script exits 0 inside
  the named Docker image. Rubric-style quality dimensions are recorded but never
  decide PASS/FAIL.
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
results; heaviest cells last):

1. `sh-refactor-small` (fast, no package install)
2. `rust-package-small` (small; cargo-deb on a mock binary, quick)
3. `py-bugfix-small`
4. `py-feature-small`
5. `ros-refactor-large` (colcon build + test)
6. `ng-plan-large` (plan-only; TS/pnpm monorepo explore)
7. `ros-plan-large` (plan-only; heaviest explore, but no build of agent code)

Budget: at sonnet-5 medium a small cell is ~10-20 min and a large cell
~20-60 min (ROS 2 includes the colcon build), so a full 7-cell serial round is
roughly 3-4 h of wall time. If the window is tight, stop after any completed
cell; a partial round is still valid (report the cells that ran). To run only
the anti-overfitting core, skip cells 2 and 6.

## Matrix

| Cell | Target repo | Profile | Effort | Task type | Image |
|---|---|---|---|---|---|
| py-bugfix-small | [sqlite-utils](https://github.com/simonw/sqlite-utils.git) | small | medium | bugfix from failing test | `python:3.12` |
| py-feature-small | sqlite-utils | small | medium | cross-file feature | `python:3.12` |
| sh-refactor-small | [bats-core](https://github.com/bats-core/bats-core.git) | small | medium | refactor with invariants | `bats-eco-builder` |
| ros-plan-large | [navigation2](https://github.com/ros-navigation/navigation2.git) (`jazzy`) | large | high | cross-file feature, explore+plan only | `ros2-nav2-builder` |
| ros-refactor-large | navigation2 (`jazzy`) | large | medium | refactor with invariants, single package | `ros2-nav2-builder` |
| rust-package-small _(reference)_ | [Satty](https://github.com/Satty-org/Satty.git) | small | medium | packaging (cargo-deb) | `satty-deb-builder` |
| ng-plan-large _(reference)_ | [Understand-Anything](https://github.com/Egonex-AI/Understand-Anything.git) | large | medium | cross-file feature, explore+plan only | none (plan-only) |

The two `(reference)` cells reproduce the original scenarios (see
[../satty-deb-2026-07-01/report.md](../satty-deb-2026-07-01/report.md) and
[../ua-plan-2026-07-02/report.md](../ua-plan-2026-07-02/report.md)); their
agent-prompt structure is the small/large template from the
[satty runbook](../satty-deb-2026-07-01/runbook.md). They are the packaging and
Angular scenarios the anti-overfitting cells were designed to *not* resemble, so
running them alongside gives a same-round cross-ecosystem baseline.

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
- **Packaging (rust-package-small, reference):** the Satty Debian-packaging task
  verbatim from the [satty runbook](../satty-deb-2026-07-01/runbook.md) — add
  `[package.metadata.deb]` + a `deb: build-release` Makefile target, gated by
  `cargo deb --no-build --no-strip` in Docker. No re-pinning; it is the fixed
  reference scenario.
- **Plan-only feature (ng-plan-large, reference):** the Understand-Anything
  UA-1 task verbatim — add an Angular `FrameworkConfig` to
  `@understand-anything/core`'s framework registry (the config, its three-place
  registration, and a registry test), verified statically against
  `FrameworkConfigSchema` and the existing `framework-registry.test.ts`. Fixed
  reference scenario; confirm the repo SHA at run.

### Pinned briefs (pinned 2026-07-02)

| Cell | Pinned SHA | Brief | Notes |
|---|---|---|---|
| py-bugfix-small | sqlite-utils `79117b9` | "The test `tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table` fails. Find the root cause and fix it." | Seed: revert the `sqlite_utils/db.py` hunk of `1a28416` (detect_fts `content=[...]` vs `content="..."` LIKE pattern), keep the test. Symptom is `table "books_fts" already exists` — root cause is two hops away in `detect_fts`. Verified failing 2026-07-02 (1 failed, 46 passed). |
| py-feature-small | sqlite-utils `79117b9` | "Add a `rename-column` CLI command and a `Table.rename_column(old, new)` API method, mirroring the existing `rename-table` command / `rename_table()` pattern. Include tests and doc updates." | Gap verified: `rename-table` exists (`cli.py:1681`, `db.py:1233`), no column equivalent. May delegate to `transform()`. |
| sh-refactor-small | bats-core `5a7db7a` | "The function `abort()` is defined identically in `libexec/bats-core/bats`, `bats-exec-suite`, and `bats-gather-tests`. Deduplicate it into `lib/bats-core/common.bash` with zero behavior change. The existing test suite must pass unmodified." | Leave the per-formatter `bats_tap_stream_*` trio alone (callback interface, not duplication). **Round-1 correction:** only `bats` and `bats-exec-suite` are true duplicates; `bats-gather-tests`'s `abort()` has a different printf contract (same-name coincidence). The brief is kept verbatim as a deliberate wrong-premise probe: the round-1 agent detected and recorded the discrepancy, which is the desired behavior. |
| ros-plan-large | navigation2 `jazzy` (candidate `60e82db`; confirm SHA at run) | "Plan a new `nav2_behaviors` behavior plugin (a simple time-based motion, e.g. a fixed-duration `Wait`-style or `Spin`-style variant that does not already exist in `nav2_behaviors/plugins/`), mirroring an existing behavior: a class deriving `nav2_core::Behavior` via `TimedBehavior<ActionT>`, the `behavior_plugin.xml` pluginlib export, the corresponding `nav2_msgs` action if needed, `package.xml`/`CMakeLists.txt` wiring, and a `nav2_bringup` params entry enabling it." | Plan-only. Template: `nav2_behaviors/plugins/wait.{hpp,cpp}` (~127 LOC) + `behavior_plugin.xml`. **Pin at run:** verify the chosen behavior name is absent from `nav2_behaviors/plugins/` (existing: back_up, spin, wait, drive_on_heading, assisted_teleop). |
| ros-refactor-large | navigation2 `jazzy` (candidate `60e82db`; confirm SHA at run) | "In `nav2_velocity_smoother`, extract a self-contained helper (e.g. the per-axis velocity clamping / deadband math) out of the node class into its own free-function header + translation unit, with zero behavior change. The package's existing tests must pass unmodified (nothing under `nav2_velocity_smoother/test/` changes)." | Single-package; colcon build + `colcon test` of `nav2_velocity_smoother` is the invariant (2 test files). Pick the exact helper from the source at run. |
| rust-package-small _(reference)_ | Satty (pin at run; round 1 used `0.21.1`) | Verbatim Satty debian-pkg brief: `[package.metadata.deb]` with assets mirroring the Makefile `install` target + a `deb: build-release` target calling `cargo deb --no-build`. | Fixed reference scenario, unchanged. Full step-by-step in the [satty runbook](../satty-deb-2026-07-01/runbook.md) small profile. |
| ng-plan-large _(reference)_ | Understand-Anything (confirm SHA at run) | "Add Angular detection to `@understand-anything/core`'s framework registry: a new `FrameworkConfig` plus its three-place registration and a registry test." Plan-only. | Fixed reference scenario. Template: existing `FrameworkConfig` entries + `framework-registry.test.ts`; validate against `FrameworkConfigSchema`. |

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

`rust-package-small` reuses the **`satty-deb-builder`** image from the
[satty runbook](../satty-deb-2026-07-01/runbook.md) (build it once from there);
`ng-plan-large` needs no image (plan-only).

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
- **rust-package-small (reference):** `cargo deb --no-build --no-strip` in
  `satty-deb-builder` produces a `.deb` and `dpkg-deb --contents` lists every
  asset from the Makefile `install` target (binary, `.desktop`, icon, all
  completions, man page). Same gate as the satty runbook.
- **ng-plan-large (reference):** no container gate (plan-only). Static checks:
  plan.md schema-valid; every task file self-contained; affected files exist at
  the pinned SHA; the planned `FrameworkConfig` validates against
  `FrameworkConfigSchema`; the three registration sites named in the plan exist
  in the repo.

## What this set measures that the prior sets could not

| Question | Cell(s) |
|---|---|
| Do ecosystem-correctness criteria name the *right* linter outside Rust/Debian (ruff/pytest, shellcheck — not lintian/clippy)? | py-*, sh-* |
| Does explore->spec find a root cause, or does the agent patch symptoms? | py-bugfix-small |
| Does the review gate catch behavior drift when the criteria say "no behavior change"? | sh-refactor-small, ros-refactor-large |
| Does the large profile's KB/budget machinery pay off on a genuinely large C++ codebase (vs the ~7k-LOC Satty where it did not)? | ros-* |
| Does `parallel: ok` marking appear only where files are truly disjoint? | ros-plan-large, ng-plan-large |
| Does the project-context refresh step stay quiet when commands/module map did not move (LOC-only drift)? | all small cells |
| Reference: does the packaging scenario still produce a policy-correct `.deb` (no regression vs prior Satty runs)? | rust-package-small |
| Reference: does the TS/Angular plan stay schema-valid and implementable on a ~39k-LOC monorepo? | ng-plan-large |

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
