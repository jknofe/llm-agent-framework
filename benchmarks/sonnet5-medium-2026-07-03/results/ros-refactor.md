# Benchmark Cell Result: ros-refactor-s5m-2026-07-03

Orchestrator-authored results file (the agent implemented and self-verified but
returned before writing this file; the gate below is the orchestrator's
independent clean-slate re-verification).

## Configuration

| Field | Value |
|---|---|
| Run ID | ros-refactor-s5m-2026-07-03 |
| Cell | 5 ros-refactor (navigation2, nav2_velocity_smoother) |
| Profile | large |
| Model | claude-sonnet-5 |
| Effort | medium |
| Target @ SHA | ros-navigation/navigation2 @ `60e82dbb634bd93aed18f2f8d39b27d4b8656038` |
| Scaffold KB nodes | 7 |
| .ai chain | init -> explore -> add-ticket -> plan -> implement (VELSMOOTH-1) |
| Gate image | ros2-nav2-builder (ros:jazzy + colcon + rosdep) |
| Gate result | PASS |

## Task

Extract the per-axis velocity clamping / deadband math out of the
`VelocitySmoother` node class into its own free-function header + translation
unit, zero behavior change, `nav2_velocity_smoother/test/` unmodified.

## .ai commit history

```
0608b50 implement: VELSMOOTH-1 done (extracted per-axis math, reviewed PASS)
60fe1c9 plan: VELSMOOTH-1 add review AC (explicit <algorithm>/<cmath> includes)
a406153 plan: VELSMOOTH-1 (reviewed, fixed missing <algorithm>/<cmath> includes)
6fd57aa add-ticket: VELSMOOTH-1
9748933 explore: nav2_velocity_smoother node, math to extract, tests, build
385c1ea init: scaffold KB + phase docs (navigation2)
```

## Target diff (stat)

```
 nav2_velocity_smoother/CMakeLists.txt                              |  1 +
 nav2_velocity_smoother/include/nav2_velocity_smoother/velocity_smoother_math.hpp | 70 ++++++++++
 nav2_velocity_smoother/src/velocity_smoother.cpp                   | 60 +++------
 nav2_velocity_smoother/src/velocity_smoother_math.cpp              | 90 ++++++++++++
 4 files changed, 172 insertions(+), 49 deletions(-)
```

New free functions in `velocity_smoother_math.{hpp,cpp}` (namespace
`nav2_velocity_smoother`): `findEtaConstraint`, `applyConstraints`,
`clampVelocity`, `applyDeadband`. The node's private `findEtaConstraint` /
`applyConstraints` methods now delegate to the free functions; inline
`std::clamp(...)` and the deadband ternaries in `smootherTimer()` were replaced
by `clampVelocity(...)` / `applyDeadband(...)`. The math was moved verbatim. No
change under `nav2_velocity_smoother/test/`.

## Corrected-gate note (three runbook defects, flagged for a runbook fix)

The runbook's literal cell-5 gate cannot build against the pinned SEED layout.
Three defects were diagnosed and corrected by the orchestrator; the corrected
gate was validated against the UNMODIFIED workspace (control build green) before
the agent ran:

1. `rosdep install --from-paths src` -> the SEED clones navigation2 to the
   workspace root (no `src/` dir); must be `--from-paths .`.
2. The image ends with `rm -rf /var/lib/apt/lists/*`, so `apt-get update` is
   required before `rosdep install` or every `ros-jazzy-*` install fails to
   locate a package.
3. `rosdep install` does not pull `ros-jazzy-bondcpp`, which the
   nav2_velocity_smoother launch_test loads at runtime (`libbondcpp.so`);
   without it the baseline itself shows 1 error + 1 failure. Installing it makes
   the baseline green (0/0).

## Gate output (orchestrator clean-slate re-verification)

Wiped `build/ install/ log/`, then ran the corrected gate from scratch:

```
BUILD-EXIT: 0
Summary: 46 tests, 0 errors, 0 failures, 6 skipped
```

`git diff --stat 60e82db -- 'nav2_velocity_smoother/test'` is EMPTY.

**PASS** = colcon build succeeded AND colcon test reported 0 errors AND 0
failures AND no source under `nav2_velocity_smoother/test/` changed. All hold.

## Observations

1. Faithful extraction: the delegating-wrapper approach (node methods call the
   new free functions) keeps the class API intact, so the existing tests that
   call `VelocitySmoother::findEtaConstraint` / `applyConstraints` pass
   unmodified while the math itself lives in the free-function TU.
2. Zero behavior change is corroborated by the full 46-test suite at 0/0 on the
   modified code with `test/` untouched, plus a byte-for-byte move of the branch
   logic (accel/decel component selection, `std::clamp`, deadband threshold).
3. Clean large-profile process chain (init -> explore -> ticket -> plan ->
   implement) with the explore committed before planning, as the profile
   requires; plan review added an acceptance criterion for explicit
   `<algorithm>`/`<cmath>` includes in the new TU (a real portability catch).
4. Medium effort was appropriate: minimal surface (one helper TU + header +
   one CMake line), no gold-plating.
5. The three gate defects are environment/runbook issues, not agent issues; the
   agent's solution passed the corrected, environment-validated gate.
