# Amortization Playbook (planned — not yet run)

Two experiments, designed to actually answer the question raised after the
2026-07-06 Sonnet-5 small-profile round: does the framework's amortization
thesis (a warm-started second task beats a cold one) hold, and does it hold
on this model? Neither experiment has been executed. This file is the
fully-pinned procedure to run later — same determinism discipline as
`fixed-runbook.md` (SEED, SCAFFOLD, TASK, GATE all fixed; only MODEL is a
free variable, pinned here to `claude-sonnet-5` per the request that
prompted this).

Rationale for two, not one: the only direct amortization measurement that
exists (`benchmarks/haiku-high-2026-07-04/baseline-comparison.md`, B-amortized
section) is haiku, n=1, on a **small** repo, and showed the framework's
marginal session was *more* expensive than baseline's, not less — the
relative overhead stayed flat (~35-45%) across the modeled N. CONCEPT.md §13
explicitly predicts amortization should **not** work on small repos (cold
discovery is cheap enough that ceremony dominates) and stakes the thesis on
**medium/large** repos instead, where cold discovery is expensive. Experiment
A re-runs the small-repo case at Sonnet 5 (cheap, fast, checks if a stronger
model changes the small-repo verdict). Experiment B runs the large-repo case
for the first time ever, on any model (expensive, slow, but the actual test
of where the thesis is supposed to live).

---

## Experiment A: small-repo (sqlite-utils) B-amortized, Sonnet 5 x medium

Reuses the already-pinned SEED/TASK/GATE from `fixed-runbook.md` cells 3+4
and its own B-amortized section verbatim — only MODEL/EFFORT are new here.
Nothing about this experiment needs re-deriving; it is cells 3+4 chained in
one work dir instead of run as two independent one-shot cells (which is what
the 2026-07-06 round did instead, by mistake relative to what would actually
test amortization).

```
MODEL:  claude-sonnet-5
EFFORT: medium
RUN_ID: py-seq-sonnet5-<date>          (framework arm)
        py-seq-sonnet5-baseline-<date> (baseline arm)
WORK_DIR: /tmp/benchmark/runs/$RUN_ID/sqlite-utils
```

**SEED** (identical for both arms, one work dir each): clone
`github.com/simonw/sqlite-utils`, checkout `79117b9`, reverse-apply the
`detect_fts` fix from `1a28416` (`git diff 1a28416~1 1a28416 --
sqlite_utils/db.py | git apply -R`), then **commit the reverted state**
(`git add -A && git commit -m "seed: revert detect_fts fix (benchmark bug
state)"`) — do this before dispatch, exactly as the 2026-07-06 round did,
per the `.ai/notes.md` gotcha that an uncommitted seed is fragile against a
baseline agent's `git checkout` reflex (this destroyed a haiku-round baseline
result on 2026-07-04; committing the bug state as its own commit closed that
hole and should stay standard practice for this SEED going forward).

**Framework arm sequence:**
1. Session 1: `python3 init_agent.py --name sqlite-utils --description
   "CLI tool and Python library for manipulating SQLite databases" --size
   small --harness claude -y`, then `/explore`, then cell 3's TASK (the
   `detect_fts` bugfix) to done (spec -> build -> review -> gate).
2. Session 2 (fresh session, same work dir, no memory of session 1 beyond
   what's on disk): cell 4's TASK (the `rename-column` feature) to done.
   Do **not** re-run `/explore` — the point of the test is whether the
   agent works from the existing `AGENTS.md` digest and `.ai/notes.md`
   without rediscovery. If the agent re-explores anyway, record that as a
   finding (it means the warm-start design isn't being honored), not a
   silent pass.

**Baseline arm sequence:** two fresh sessions, no scaffold, no memory link
between them (mirrors a user coming back on a different day with no
memory-carrying artifact) — session 1 = cell 3's TASK cold, session 2 = cell
4's TASK cold.

**GATE:** both cells' gates exactly as pinned in `fixed-runbook.md` (`pip
install -q -e . pytest hypothesis && python -m pytest -q`, plus cell 3's "no
test file changed" check).

**Token counting:** `count_tokens.py --per-session <WORK_DIR>` per arm — the
`--per-session` flag is exactly for this, splitting the one project
directory's sessions apart so session-2's marginal cost is isolated from
session 1's. (Note: if dispatched via Task-tool sub-agents inside one
orchestrator session rather than standalone `claude` CLI processes per
session, as the 2026-07-06 round did, use the isolate-and-count workaround
documented in that round's report instead — copy each session's
`subagents/agent-<id>.jsonl` into its own directory and run
`count_tokens.py --projects-dir` against it; the two sessions will be two
different agent IDs even though they share a `WORK_DIR`.)

**Comparison table (fixed format):**

```
| Arm       | Session         | Gate | Output tokens | Total tokens | Cost | Duration |
|-----------|------------------|------|----------------|---------------|------|----------|
| framework | s1 (incl. explore) | ... | ...            | ...           | ...  | ...      |
| framework | s2 (warm)          | ... | ...            | ...           | ...  | ...      |
| baseline  | s1 (cold)          | ... | ...            | ...           | ...  | ...      |
| baseline  | s2 (cold)          | ... | ...            | ...           | ...  | ...      |
```

**Verdict rule (fixed, matches the runbook's own criterion):** compare
framework s2 total/output against baseline s2 total/output. Framework
cheaper -> amortization thesis holds on this model/repo size. Not cheaper,
or within the ~30-40% noise guardrail -> inconclusive-to-failed, same as the
haiku result; report the number, do not round it into a verdict it doesn't
support.

---

## Experiment B: large-repo (navigation2) B-amortized, first run on any model

No prior run of this exists — cell 5/6 in `fixed-runbook.md` are a
refactor cell and a *plan-only* cell, not a same-shape two-build-task
sequence, so there is no existing pinned second task to chain after cell 5.
One had to be found and verified against the actual pinned SHA before this
file could be written; details below are already confirmed real (package
exists, function exists, tests reference it directly), not invented.

### New second task: `nav2_rotation_shim_controller` (verified 2026-07-06)

Verified by cloning `github.com/ros-navigation/navigation2` at the cell 5/6
pinned SHA (`60e82dbb634bd93aed18f2f8d39b27d4b8656038`) and inspecting:

- `nav2_rotation_shim_controller/src/nav2_rotation_shim_controller.cpp`
  (459 lines) has `computeRotateToHeadingCommand` (lines 311-340): a
  self-contained numeric computation (accel-limited angular-velocity
  clamping via `std::clamp`, then an overshoot-avoidance speed cap) that
  reads five controller-member values as inputs and returns a
  `TwistStamped` — the same shape as cell 5's velocity-clamping extraction
  (inline per-call math embedded in a node class, no ROS transforms inside
  the math itself).
- `nav2_rotation_shim_controller/test/test_shim_controller.cpp` (10 `TEST`
  cases) already exercises this exact function through a test-only
  `computeRotateToHeadingCommandWrapper` (defined in the test file, calls
  the controller's method directly) at two call sites (~line 208-215 and
  ~line 682) — so "existing tests must pass unmodified" is a real,
  checkable constraint, not a guess.
- `package.xml` name is `nav2_rotation_shim_controller`; dependencies
  (`nav2_controller`, `nav2_costmap_2d`, `nav2_util`, `angles`, `pluginlib`,
  `tf2`, test-deps on `nav2_regulated_pure_pursuit_controller` +
  `nav2_controller`) are the same shape as cell 5's package, so the
  existing gate environment corrections (rosdep `--from-paths .`, `apt-get
  update` before rosdep, explicit `bondcpp`/`geographic_msgs` install,
  `--executor sequential`) are expected to carry over unchanged — but this
  is *expected*, not yet *proven* for this specific package (see the
  required control build below).

**Not yet verified (do this first, before the real round):** the exact
unmodified baseline test count (cell 5's gate states its baseline as "46
tests / 6 skipped" because that number was captured by actually running the
gate once; the equivalent number for `nav2_rotation_shim_controller` has not
been captured here — no docker build was run as part of writing this
playbook, per the instruction to plan only). Capture it with one control
build before dispatching either arm:

```bash
docker run --rm -v "$WORK_DIR":/workspace ros2-nav2-builder bash -c '
  cd /workspace && . /opt/ros/jazzy/setup.sh
  apt-get update -qq
  rosdep install --from-paths . --ignore-src -y --rosdistro jazzy
  apt-get install -y ros-jazzy-bondcpp ros-jazzy-geographic-msgs
  colcon build --packages-up-to nav2_rotation_shim_controller --executor sequential
  . install/setup.sh
  colcon test --packages-select nav2_rotation_shim_controller
  colcon test-result --verbose; echo "EXIT: $?"'
```
Record the resulting pass/skip count and substitute it into the GATE's PASS
rule below before running either arm for real — do not skip this and do not
guess the number.

### Fixed constants

```
MODEL:  claude-sonnet-5 (or whichever model the real round targets)
EFFORT: medium
RUN_ID: ros-seq-<date>          (framework arm)
        ros-seq-baseline-<date> (baseline arm)
WORK_DIR: /tmp/benchmark/runs/$RUN_ID/navigation2
```

**SEED** (identical for both arms):
```bash
git clone https://github.com/ros-navigation/navigation2.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 60e82dbb634bd93aed18f2f8d39b27d4b8656038
```

**SCAFFOLD** (framework arm only, same as cell 5):
```bash
python3 "$FRAMEWORK" --name navigation2 \
  --description "ROS 2 Navigation (Nav2) stack — C++ / colcon / ament" \
  --size large --harness claude -y
```

**Task 1 (verbatim, = cell 5 unchanged):** "In `nav2_velocity_smoother`,
extract a self-contained helper (the per-axis velocity clamping / deadband
math) out of the node class into its own free-function header +
translation unit, with zero behavior change. The package's existing tests
must pass unmodified (nothing under `nav2_velocity_smoother/test/`
changes)."

**Task 2 (verbatim, new):** "In `nav2_rotation_shim_controller`, extract a
self-contained helper (the accel-limited angular-velocity clamping and
overshoot-avoidance speed cap in `computeRotateToHeadingCommand`) out of the
controller class into its own free-function header + translation unit, with
zero behavior change. The package's existing tests must pass unmodified
(nothing under `nav2_rotation_shim_controller/test/` changes)."

**Framework arm sequence:**
1. Session 1 (its own session/commit per the large-profile protocol: explore
   first, commit `.ai`, then plan+implement Task 1 in a second session as
   cell 5 already specifies) — run to done, gate as cell 5's.
2. Session 3 (fresh session, same work dir, KB already built and committed
   from session 1): Task 2, planned + implemented from the existing KB
   without re-running `/explore`. If the agent re-explores anyway, record
   it as a finding, same rule as Experiment A.

**Baseline arm sequence:** two fresh sessions, no scaffold — session 1 =
Task 1 cold, session 2 = Task 2 cold. (Large baseline sessions are
expensive; this is the priciest single measurement in either experiment —
confirm appetite before running.)

**GATE (per task, mirrors cell 5's corrected environment exactly, target
package substituted for task 2):**
```bash
docker run --rm -v "$WORK_DIR":/workspace ros2-nav2-builder bash -c '
  cd /workspace && . /opt/ros/jazzy/setup.sh
  apt-get update -qq
  rosdep install --from-paths . --ignore-src -y --rosdistro jazzy
  apt-get install -y ros-jazzy-bondcpp ros-jazzy-geographic-msgs
  colcon build --packages-up-to <package> --executor sequential
  . install/setup.sh
  colcon test --packages-select <package>
  colcon test-result --verbose; echo "EXIT: $?"'
# + git -C "$WORK_DIR" diff --stat -- '*/<package>/test/*'  is EMPTY
```
PASS (task 1) = cell 5's existing rule (46 tests / 6 skipped, unchanged).
PASS (task 2) = build succeeds AND `colcon test` passes with the control-run
count captured above AND no diff under
`nav2_rotation_shim_controller/test/`.

**Token counting:** same `count_tokens.py --per-session` approach as
Experiment A; large-profile sessions additionally include the `reviewer`
sub-agent cost at the ticket-review gate (Phase 3) — add it in per the
runbook's existing rule, same as every framework-arm cell already does.

**Comparison table:** identical shape to Experiment A's, with a session-3
row (large profile's explore is its own session/commit per protocol, so the
sequence is session1=explore, session2=task1, session3=task2 rather than
session1=explore+task1 as in the small profile) — report all three
framework sessions plus the two baseline sessions, then compare framework
session3 (marginal, warm) against baseline session2 (marginal, cold).

**Verdict rule:** same as Experiment A — framework's marginal (warm) session
cheaper than baseline's marginal (cold) session means the thesis holds here;
this is the repo-size regime (medium/large) where CONCEPT.md §13 predicts it
should.

---

## What "worth it" means for the original question

Neither experiment answers "would 4-5 changes make the overhead worthwhile"
by itself — each gives exactly one marginal-cost data point (task 2 vs. task
1), the same shape as the existing haiku measurement. Extrapolating from a
single marginal delta to N=4-5 uses the model already laid out in the prior
turn's analysis:

```
Total_framework(N) = Cost(session with explore) + (N-1) x Marginal_framework
Total_baseline(N)  = N x Marginal_baseline
```

If `Marginal_framework < Marginal_baseline` (framework's per-task marginal
cost, table above, is lower), the relative overhead shrinks as N grows and
crosses over at some N — solvable directly from the two experiments'
numbers once run. If `Marginal_framework >= Marginal_baseline` (the haiku
small-repo result), the relative overhead holds flat or widens with N — more
changes does not help, regardless of how many are assumed.

## Status

Not executed. Docker images (`bats-eco-builder`, `satty-deb-builder`,
`ros2-nav2-builder`) and the `python:3.12` pull already exist locally from
the 2026-07-06 round and do not need rebuilding. The
`/tmp/nav2-inspect/navigation2` clone used to verify Task 2 above is a
disposable research clone, not a benchmark work dir — delete it before
running Experiment B for real and seed a fresh `$WORK_DIR` clone per the SEED
block.
