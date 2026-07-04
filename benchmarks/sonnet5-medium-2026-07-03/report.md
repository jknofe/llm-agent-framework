# Benchmark Report: full set (cells 1-7) on sonnet-5 x medium

**Date:** 2026-07-03 / 2026-07-04 (cells 4-7 spanned session-limit resets)
**Model/effort:** claude-sonnet-5 x medium
**Framework state:** current HEAD (v5.9), commit `738ad86`.
**Runbook:** [../fixed-runbook.md](../fixed-runbook.md), cells 1-7 (full set).
**Raw results:** [results/](results/) (one file per cell).
**Companion round:** [../haiku-high-2026-07-03/report.md](../haiku-high-2026-07-03/report.md)
(fast core, cells 1-4, at claude-haiku-4-5 x high).

Purpose: the full seven-cell cross-ecosystem set at claude-sonnet-5 x medium.
Cells 1-4 (fast core) were run first and are directly comparable to the haiku x
high round (same tasks, SHAs, gates); cells 5-7 add the two large-profile ROS 2
cells (navigation2 colcon) and the two plan-only cells (ROS behavior plugin,
Angular framework registry).

Each cell was executed by one autonomous agent, dispatched strictly sequentially.
Every gate below was **re-run independently by the orchestrator** on the intact
work dir, not trusted from the agent's self-report. PASS/FAIL is the container
gate (or, for plan-only cells, the static-check set) only. Three agents hit
session limits mid-run (cells 4, 6, and cell 6's reviewer) and were resumed as
the same agent, same work dir, per the runbook.

**The ROS cells required correcting four defects in the runbook's cell-5/6 gate
before any build could run (see "ROS gate defects" below).** These are
environment/runbook issues, not agent issues; each corrected gate was validated
against the unmodified workspace before the agent's solution was judged.

## Configuration

| Field | Value |
|---|---|
| Cells | 1 sh-refactor, 2 rust-package, 3 py-bugfix, 4 py-feature (small); 5 ros-refactor, 6 ros-plan, 7 ng-plan (large) |
| Profiles | small (cells 1-4), large (cells 5-7); pinned per cell |
| Model x effort | claude-sonnet-5 x medium (constant across all cells) |
| Harness | claude |
| Gate images | `bats-eco-builder`, `satty-deb-builder`, `python:3.12`, `ros2-nav2-builder` (built this round from `ros:jazzy`) |

## Results: 7/7 PASS (independently re-verified)

| # | Cell | Target @ pinned SHA | Gate re-verification | Result |
|---|---|---|---|---|
| 1 | sh-refactor | bats-core @ `5a7db7a` | `bin/bats test` exit 0, **479/479 ok**; `shellcheck -x` exit 0 on all 3 changed scripts; `test/` diff empty | **PASS** |
| 2 | rust-package | Satty @ `2d18065` | `cargo deb --no-build` produced `satty_0.21.1-1_arm64.deb`; `dpkg-deb --contents` lists binary, `.desktop`, SVG icon, all 6 completions, man page | **PASS** |
| 3 | py-bugfix | sqlite-utils @ `79117b9` | full suite **1080 passed, 16 skipped**, exit 0; `tests/` diff empty | **PASS** |
| 4 | py-feature | sqlite-utils @ `79117b9` | full suite **1086 passed, 16 skipped**, exit 0 (includes the agent's 5 new tests) | **PASS** |
| 5 | ros-refactor | navigation2 @ `60e82db` | (corrected gate) `colcon build --packages-up-to nav2_velocity_smoother` exit 0; `colcon test` **46 tests, 0 errors, 0 failures, 6 skipped**; `nav2_velocity_smoother/test/` diff empty | **PASS** |
| 6 | ros-plan | navigation2 @ `60e82db` | static checks 1-4 PASS (schema-valid plan incl kb-commit, self-contained task files, affected files exist at SHA, `wiggle` absent from `plugins/`); check 5 control build `--packages-up-to nav2_behaviors` exit 0 (10 pkgs) | **PASS** |
| 7 | ng-plan | Understand-Anything @ `0e8ad84` | static checks 1-5 PASS (schema-valid plan incl kb-commit, self-contained task files, affected files exist, FrameworkConfig validates against schema, 3 registration sites cited); no source edits | **PASS** |

Container note (cell 1): the bats suite needs `TERM=xterm` in the image, else
unrelated `tput`/TERM tests fail identically before and after the change. The
gate sets it; with it the suite is fully green.

## ROS gate defects (cells 5-6; flagged for a runbook fix)

The runbook's literal cell-5/6 gate cannot produce a build against the pinned
SEED layout and image. Four issues were diagnosed and corrected; each correction
was validated against the UNMODIFIED workspace before any agent solution was
judged (control build green), so the fixes do not mask agent behavior:

1. **`rosdep --from-paths src` -> `--from-paths .`.** The SEED clones navigation2
   to the workspace root; there is no `src/` colcon dir.
2. **Missing `apt-get update`.** The image ends with `rm -rf
   /var/lib/apt/lists/*`, so without an update every `ros-jazzy-*` install fails
   to locate a package. (`rosdep install` also exits 0 even when an individual
   apt install fails, which hid this.)
3. **Missing runtime deps `rosdep` does not pull:** `ros-jazzy-bondcpp`
   (nav2_velocity_smoother launch_test loads `libbondcpp.so`; without it the
   cell-5 baseline shows 1 error + 1 failure) and `ros-jazzy-geographic-msgs`
   (nav2_msgs exports it; without it nav2_behavior_tree fails to configure).
4. **Parallel-executor race.** The default colcon executor intermittently fails
   `nav2_behavior_tree` with a compile error before its generated deps are ready;
   `--executor sequential` builds the `nav2_behaviors` tree cleanly.

Recommended runbook change: update the cell-5/6 gate to `apt-get update && rosdep
install --from-paths . --ignore-src -y --rosdistro jazzy && apt-get install -y
ros-jazzy-bondcpp ros-jazzy-geographic-msgs && colcon build ... --executor
sequential`, or bake bondcpp/geographic_msgs into the image and run `apt-get
update` in the gate.

## Probe findings (the quality signal)

Each cell embeds a deliberate trap. Sonnet at medium caught all four.

- **Cell 1 wrong-premise (caught).** Confirmed the three `abort()` definitions
  are not identical. Merged only the two matching ones (`bats`,
  `bats-exec-suite`) into `common.bash` and left `bats-gather-tests`'s
  format-string contract alone. The transitive-re-source clobber was caught by
  the gate's first run (test 44 failed) rather than proactively, because the
  reviewer saw only the diff and `bats-gather-tests` was not in it; the agent
  then guarded the shared definition (see quality assessment).
- **Cell 2 policy depth (medium-appropriate).** Verified the `build-release ->
  ci-release` chain populates `completions/` and `man/`, and mirrored the
  Makefile exactly including its zsh `site-functions` path. Correctly did not add
  the high-effort extras (`section`, `priority`, `vendor-completions`, etc.),
  which is the right call at medium.
- **Cell 3 root cause vs symptom (root cause).** Traced the
  `table "books_fts" already exists` symptom two hops to the `detect_fts`
  `like`/`like2` pattern collapse, and noted the `test_tracer` key-order
  constraint on the fix. No test file touched.
- **Cell 4 silent-data-loss collision (handled thoroughly).** Empirically
  confirmed that `transform(rename=)` onto an existing column silently drops
  data, then implemented `rename_column` with native `ALTER TABLE RENAME COLUMN`
  (avoiding the path) AND added an explicit `AlterError` guard rejecting a rename
  onto an existing distinct column, plus a missing-column guard and a regression
  test.
- **Cell 5 zero-behavior-change refactor (verified).** Extracted the per-axis
  clamp/deadband math into free functions and had the node's methods delegate to
  them, keeping the class API so the existing tests pass unmodified; the full
  46-test suite is green at 0/0 with `test/` untouched.
- **Cell 6 copy-paste-reuse trap (caught by review).** The draft reused
  `Spin::isCollisionFree`, whose `relative_yaw`-gated early-break makes the
  look-ahead near-blind right after each direction flip; the plan review caught
  it and specified a dedicated full-horizon collision check for the new Wiggle
  behavior. Also chose the correct completion semantics (succeed-on-elapse like
  Wait, not timeout-on-elapse like Spin).
- **Cell 7 "three-place registration" ambiguity (flagged).** The agent noted the
  three registration sites are three lines in one file (`frameworks/index.ts`),
  not three separate files, and its planned FrameworkConfig validates field-by-
  field against `FrameworkConfigSchema`.

## Quality assessment (rubric, non-gating)

Rated from the actual diff (read against the pinned base). Scores are 1-5 per
dimension and do not affect PASS/FAIL. **Corr** = correctness/robustness beyond
the gate; **Min** = scope discipline; **Idiom** = fit and readability; **Probe**
= trap handling; **T&D** = tests and docs.

| Cell | Corr | Min | Idiom | Probe | T&D | Overall |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 sh-refactor | 5 | 5 | 5 | 4.5 | 5 | **A** |
| 2 rust-package | 5 | 5 | 5 | 5 | 4.5 | **A** |
| 3 py-bugfix | 5 | 4 | 4.5 | 5 | 4.5 | **A-** |
| 4 py-feature | 5 | 5 | 5 | 5 | 5 | **A (exemplary)** |
| 5 ros-refactor | 5 | 5 | 5 | 5 | 5 | **A (exemplary)** |
| 6 ros-plan (plan-only) | 5 | 4.5 | 5 | 5 | 5 | **A** |
| 7 ng-plan (plan-only) | 5 | 5 | 5 | 4.5 | 5 | **A** |

**Cell 1 sh-refactor (A).** The dedup mechanism is elegant: the shared `abort`
in `common.bash` calls `usage` only when `declare -f usage` succeeds, so it
adapts per sourcing script (`bats` has `usage`, `bats-exec-suite` does not) with
**zero call-site edits**, and it is wrapped in `if ! declare -f abort` so a
transitive re-source cannot clobber a caller's local override. `bats-gather-tests`
is left completely untouched. Minimal (3 files, 27 lines) and self-documenting.
The half-point off Probe is process, not result: the re-source hazard surfaced
from the gate's first failing run rather than from analysis up front, and the
diff-only reviewer could not have seen it.

**Cell 2 rust-package (A).** Tidy and correctly scoped for medium: a 3-line
`deb: build-release` target and a `[package.metadata.deb]` block with just the
asset map, mirroring the Makefile precisely (including its `site-functions` zsh
path). No high-effort extras, and no unrelated edits (contrast the haiku-high run,
whose Makefile diff also stripped trailing whitespace from the `package` target).
Half-point off T&D only because a `.deb` has no unit test surface.

**Cell 3 py-bugfix (A-).** Correct root-cause fix restoring the two distinct
`detect_fts` patterns, with the `test_tracer` key-order constraint spotted. End
state is byte-identical to the canonical upstream fix. The deduction is process
hygiene: during investigation the agent used `git stash`/`git checkout`, which
overwrote the buggy bytes with the tracked (already-correct) content, muddying
the pre-fix diff capture. It was transparent about this, re-reproduced the exact
symptom, and re-verified, so the outcome is sound, but the path was messier than
a targeted edit would have been.

**Cell 4 py-feature (A, exemplary).** The strongest solution in either round.
Native `ALTER TABLE RENAME COLUMN` (the true mirror of `rename_table`'s native
`ALTER TABLE RENAME TO`), a missing-column guard, and a collision guard that
rejects renaming onto an existing distinct column with a comment naming the
`transform(rename=)` trap it avoids. Chainable (returns `self`), injection-safe
via `quote_identifier`, `--ignore` parity with `rename-table`, five tests, and
four doc files updated including the cog-regenerated `cli-reference.rst`. Review
sub-agent PASS; one genuinely out-of-scope note (case-sensitivity of
`columns_dict`) correctly deferred.

**Cell 5 ros-refactor (A, exemplary).** A faithful C++ extraction: the per-axis
clamp/deadband math moved verbatim into `velocity_smoother_math.{hpp,cpp}` (free
functions `findEtaConstraint`, `applyConstraints`, `clampVelocity`,
`applyDeadband`), with the node's private methods delegating to them and the
inline `std::clamp`/deadband ternaries replaced by the new calls. The delegating-
wrapper choice preserves the class API so the existing tests pass unmodified,
directly serving the "zero behavior change / tests untouched" constraint; the 46-
test suite confirms it. Minimal (one TU + header + one CMake line), clean large-
profile chain (init -> explore -> ticket -> plan -> implement), and the plan
review added a real portability criterion (explicit `<algorithm>`/`<cmath>`
includes in the new TU).

**Cell 6 ros-plan (A, plan-only).** A self-contained, schema-valid plan for a new
`Wiggle` behavior (in-place oscillating rotation) mirroring the existing plugin
pattern: the `TimedBehavior<ActionT>` derivation, `behavior_plugin.xml` export,
`nav2_msgs` action, package.xml/CMakeLists wiring, and the bringup params entry.
The review caught the substantive trap (blind collision look-ahead from a reused
`Spin` early-break) and the plan chose correct completion semantics. Half-point
off Min for one arguably-broad task, but scoping decisions (multi-robot params
called out as explicit out-of-scope rather than silently dropped) were sound.

**Cell 7 ng-plan (A, plan-only).** Schema-valid plan for the Angular
`FrameworkConfig` with field-by-field validation against `FrameworkConfigSchema`
and all three registration sites cited to `file:line`. The half-point off Probe
is that the "three-place registration" being three lines in one file was surfaced
as a note rather than shaping the task decomposition, but the plan is correct and
implementable.

## Aggregate and comparison to haiku x high

Mean overall is around A, a notch above the haiku x high round (A-/A). All four
solutions are production-plausible; none games the gate.

- **Cell 1:** sonnet's capability-detection dedup (adapt via `declare -f usage`,
  no call-site edits) is cleaner than haiku's function-rename approach, though
  haiku caught the re-source hazard proactively while sonnet caught it via the
  gate. Both correct.
- **Cell 2:** not directly comparable (medium omits the high-effort policy items
  haiku-high added); within its tier sonnet was clean with no scope creep.
- **Cell 3:** both landed the canonical fix. Haiku left a cosmetic quote residue;
  sonnet ended byte-identical but via a messier `git checkout` path.
- **Cell 4:** sonnet clearly stronger. It added the explicit `AlterError`
  collision guard the runbook hint called for; haiku sidestepped the collision by
  design and did not add the guard.

Net (fast core): at these two configurations the effort tier did not visibly cap
sonnet at medium below haiku at high; sonnet's medium output was consistently
clean and, on cell 4, the best of those eight solutions. The large-profile cells
(5-7) have no haiku companion this round; all three scored A.

## Observations

- **The framework handled the large profile end to end.** Cells 5-7 drove the
  large-profile chain (init -> explore committed on its own -> ticket -> plan
  [-> implement]) across a real ~90-package colcon workspace and a pnpm/Angular
  monorepo, with the KB/manifest and self-contained task files as designed.
- **Resume-after-limit worked repeatedly.** Cells 4 and 6 (and cell 6's reviewer)
  hit session limits and were resumed as the same agent, same work dir, each
  finishing with a clean commit chain and no duplicate work.
- **The gate/review split held both ways.** Cell 1's re-source hazard was
  invisible to a diff-only reviewer and only the suite gate caught it; cell 6's
  reused-collision-check trap was invisible to a build (plan-only) and only the
  plan reviewer caught it. Each backstop earned its keep on a different cell.
- **The ROS runbook gate is broken as written** (four defects above) but the
  underlying environment is sound once corrected; this is the round's most
  actionable finding for the framework's own benchmark harness.
- **Medium scoping held across ecosystems.** No gold-plating: cell 2 skipped the
  high-effort deb extras, cell 5 was a one-helper extraction, and the plan cells
  called out-of-scope items out explicitly rather than over-reaching.
- **No framework defects surfaced.** All seven gates green on independent
  re-verification; every issue this round was environment/runbook, not framework.

## Verdict

The framework at v5.9 HEAD passes the full seven-cell set at claude-sonnet-5 x
medium, all seven gates green on independent re-verification (the four ROS gate
defects being runbook/environment issues, corrected and validated against the
unmodified workspace), every probe caught, and clean resumes across three
session-limit resets. Mean quality ~A. No framework defects surfaced; the one
actionable output is the cell-5/6 runbook gate fix documented above.
