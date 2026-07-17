# Fixed Reproducible Benchmark Runbook

A fully pinned benchmark of the `llm-agent-framework`. **The only things the user
sets are MODEL and EFFORT.** Everything else — target repos, exact commit SHAs,
seeds, scaffold commands, size profiles, Docker images, deterministic gates,
PASS criteria, and results format — is a fixed constant defined here. Re-running
this file at a later date with the same MODEL and EFFORT must reproduce the same
cells against the same code.

This is the single self-contained runbook to execute. It consolidates and pins
the cross-ecosystem cells the framework has been benchmarked on (Python, Shell,
Rust, TypeScript/Angular, C++/ROS 2); the design history lives in the git log.

---

## USER INPUTS (the only variables)

```
MODEL:  <claude-sonnet-5 | claude-opus-4-8 | claude-haiku-4-5 | ...>
EFFORT: <low | medium | high>
```

Nothing else is user-configurable. Do not change repos, SHAs, profiles, tasks,
images, or gates — that is what makes runs comparable across dates and models.

### EFFORT tiers (self-contained; encode in every agent prompt)

- **low:** be minimal. Explore only what the task names plus `probe.py`. Terse
  spec/plan (2-3 acceptance criteria, one-line assumptions). Implement directly.
  Skip policy extras and optional CI. Goal: a minimal artifact that passes the
  gate. Load-bearing invariants still hold.
- **medium:** be efficient; decide from evidence directly; keep the spec/ticket
  focused. Policy extras only if evident; no extra CI required.
- **high:** be thorough; explore all relevant files, edge cases, and policy
  details; verify every acceptance criterion explicitly.

---

## Fixed cell matrix

| # | Cell | Repo (URL) | Pinned SHA | Profile | Task type | Gate image |
|---|---|---|---|---|---|---|
| 1 | sh-refactor | github.com/bats-core/bats-core | `5a7db7a98951d9d89b3b5e7800037e655a93345f` | small | refactor / invariants | `bats-eco-builder` |
| 2 | rust-package | github.com/gabm/Satty (tag v0.21.1) | `2d18065ea534bd12792865784eed86a617ffbdc7` | small | packaging | `satty-deb-builder` |
| 3 | py-bugfix | github.com/simonw/sqlite-utils | `79117b9` | small | bugfix from failing test | `python:3.12` |
| 4 | py-feature | github.com/simonw/sqlite-utils | `79117b9` | small | cross-file feature | `python:3.12` |
| 5 | ros-refactor | github.com/ros-navigation/navigation2 | `60e82dbb634bd93aed18f2f8d39b27d4b8656038` | large | refactor / invariants | `ros2-nav2-builder` |
| 6 | ros-plan | github.com/ros-navigation/navigation2 | `60e82dbb634bd93aed18f2f8d39b27d4b8656038` | large | cross-file feature, plan-only | none (plan-only) |
| 7 | ng-plan | github.com/Egonex-AI/Understand-Anything | `0e8ad84a2a5236dca533beef618d71ee3f4568f6` | large | cross-file feature, plan-only | none (plan-only) |

Profiles are fixed per cell (not user-set, not auto-detected) so a cell is the
same experiment regardless of repo drift. As an informational check only, the
v5.9 auto-size (`--size auto`) is expected to pick the listed profile at these
SHAs (small for bats-core ~2.5k LOC and sqlite-utils; large for navigation2);
that expectation is recorded, never gating.

**Fast core = cells 1-4** (no heavy compile; ~10-20 min each at medium).
**Full set = 1-7** (adds two ROS 2 colcon builds and two plan-only cells;
~3-4 h at medium). Run the fast core when the window is tight; a partial round
is valid (report the cells that ran). A round may additionally include the
[baseline arm](#baseline-arm-b-cells-no-scaffold-optional-fixed) (B-cells:
same cells without the scaffold, for the token-economy comparison) and/or the
[worker arm](#worker-arm-w-cells-code-worker-dispatch-optional-fixed)
(W-cells: solo vs code-worker-dispatch twins, for the delegation comparison).

---

## One-time setup (fixed)

```bash
mkdir -p /tmp/benchmark/{runs,results}
FRAMEWORK=/path/to/llm-agent-framework/init_agent.py   # set once, not a knob
TOKENS=/path/to/llm-agent-framework/benchmarks/tools/count_tokens.py  # token counter

# Image for cell 1 (bats-core): shellcheck + bash
docker build -t bats-eco-builder - <<'EOF'
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    shellcheck bash git ca-certificates parallel && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
EOF

# Image for cell 2 (Satty): cargo-deb
docker build -t satty-deb-builder - <<'EOF'
FROM rust:latest
RUN cargo install cargo-deb --locked
WORKDIR /workspace
EOF

# Image for cells 5-6 (navigation2): colcon + rosdep on ROS 2 Jazzy
docker build -t ros2-nav2-builder - <<'EOF'
FROM ros:jazzy
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions python3-rosdep build-essential git \
    && rosdep init 2>/dev/null; rosdep update \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
EOF
```

Cells 3-4 use the stock `python:3.12` image (no build). Cells 6-7 are plan-only
(no container gate).

---

## Execution (fixed, strictly sequential)

Run cells in numeric order (fast/cheap first). Dispatch exactly one agent at a
time; wait for its results file and recorded gate PASS/FAIL before starting the
next. If a cell stalls on a session limit, resume the *same* agent after the
reset (its work dir and `.ai` state are intact) — never launch a duplicate into
the same work dir. Parallel dispatch is prohibited (it burns the usage window
~5x faster and stalls cells mid-run).

For each cell, spawn the agent with the [shared agent prompt](#shared-agent-prompt)
below, substituting only `{MODEL}` and `{EFFORT}` (your two inputs) and the
cell's fixed constants from the matrix and the per-cell blocks.

**Token count (mandatory, orchestrator duty).** After a cell's agent finishes
(and before starting the next cell), count the tokens the run consumed and
append the tool's Markdown block to the cell's results file:

```bash
python3 "$TOKENS" "$WORK_DIR" >> /tmp/benchmark/results/$RUN_ID.md
```

The counter sums API usage (input, cache write, cache read, output; per model
and total) from the Claude Code session transcripts of the work dir,
deduplicated by message id; multiple sessions (resume-after-limit) and
sub-agent usage are included. Run it from the orchestrator, not the agent: an
agent cannot see its own final turn, and self-reported numbers are not
trusted anyway (same rule as the gates). Token counts are recorded for every
run and are informational, never gating.

---

## Per-cell fixed constants

Each block gives the exact SEED (clone + checkout + any deterministic failing
state), the exact SCAFFOLD command, the TASK brief (verbatim, pinned), and the
GATE with its PASS rule. `RUN_ID = <cell>-<date>` (e.g. `sh-refactor-2026-07-03`);
`WORK_DIR = /tmp/benchmark/runs/$RUN_ID/<repo>`.

### Cell 1 — sh-refactor (bats-core, small)

```bash
# SEED
git clone https://github.com/bats-core/bats-core.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 5a7db7a98951d9d89b3b5e7800037e655a93345f
# SCAFFOLD
python3 "$FRAMEWORK" --name bats-core \
  --description "Bash Automated Testing System (bats) — TAP-compliant test runner" \
  --size small --harness claude -y
```
**TASK (verbatim):** "The function `abort()` is defined identically in
`libexec/bats-core/bats`, `bats-exec-suite`, and `bats-gather-tests`.
Deduplicate it into `lib/bats-core/common.bash` with zero behavior change. The
existing test suite must pass unmodified." *(Deliberate wrong-premise probe: the
three definitions are NOT identical — `bats-gather-tests` has a different printf
contract. The agent must verify and not force a wrong merge. Do not soften the
brief.)*

**GATE** (`bats-eco-builder`, `TERM=xterm` set; all three must hold):
```bash
docker run --rm -e TERM=xterm -v "$WORK_DIR":/workspace bats-eco-builder bash -c '
  cd /workspace && ./bin/bats test; echo "SUITE-EXIT: $?"'
# + shellcheck -x exit 0 on EVERY changed script
# + git -C "$WORK_DIR" diff --stat -- test/  is EMPTY
```
PASS = bats suite exit 0 AND shellcheck exit 0 on every changed script AND no
diff under `test/`.

### Cell 2 — rust-package (Satty, small)

```bash
# SEED  (shallow clone of the tag is fine; the SHA is the v0.21.1 commit)
git clone https://github.com/gabm/Satty.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 2d18065ea534bd12792865784eed86a617ffbdc7
# SCAFFOLD
python3 "$FRAMEWORK" --name satty \
  --description "Modern screenshot annotation tool (Rust/GTK4)" \
  --size small --harness claude -y
```
**TASK (verbatim):** Add `[package.metadata.deb]` to `Cargo.toml` with assets
mirroring every path in the Makefile `install` target (binary `usr/bin/satty`
755, `.desktop`, SVG icon, all shell completions incl. fig, man page, license),
and add a `deb: build-release` Makefile target that calls `cargo deb --no-build`
(the `build-release` dependency runs the `ci-release` feature first, generating
`completions/` and `man/`). At EFFORT=high also add `section="graphics"`,
`priority="optional"`, `extended-description`, `license-file=["LICENSE","0"]`,
version-pinned depends, and the Debian zsh path `usr/share/zsh/vendor-completions/`.

**GATE** (`satty-deb-builder`): create mock build artifacts, then
```bash
mkdir -p "$WORK_DIR"/target/release "$WORK_DIR"/completions "$WORK_DIR"/man
printf '\x7fELF\x02\x01\x01\x00' > "$WORK_DIR"/target/release/satty
chmod +x "$WORK_DIR"/target/release/satty
for f in satty.bash _satty satty.fish satty.elv satty.nu satty.ts; do
  [ -f "$WORK_DIR"/completions/$f ] || touch "$WORK_DIR"/completions/$f; done
[ -f "$WORK_DIR"/man/satty.1 ] || touch "$WORK_DIR"/man/satty.1
docker run --rm -v "$WORK_DIR":/workspace satty-deb-builder bash -c '
  cd /workspace && cargo deb --no-build --no-strip 2>&1
  echo "=== contents ==="; dpkg-deb --contents target/debian/satty_*.deb | awk "{print \$6}" | sort'
```
PASS = a `target/debian/satty_*.deb` path is produced AND `dpkg-deb --contents`
lists binary, `.desktop`, icon, all completions, and man page. (`$auto` deps
warning on the mock binary is expected, not a failure.)

### Cell 3 — py-bugfix (sqlite-utils, small)

```bash
# SEED — deterministic failing state: keep the test, remove only the fix
git clone https://github.com/simonw/sqlite-utils.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 79117b9
# Reverse-apply ONLY the db.py hunk of fix commit 1a28416 (use `git diff`, not
# `git show` — the latter's commit header makes `git apply` reject the patch):
git -C "$WORK_DIR" diff 1a28416~1 1a28416 -- sqlite_utils/db.py | git -C "$WORK_DIR" apply -R
# Verified: reverts detect_fts `content=[{}]` -> `content="{}"`; the test
# tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table FAILS
# (verified failing: 1 failed, 46 passed). Do NOT tell the agent the reverted SHA.
# SCAFFOLD
python3 "$FRAMEWORK" --name sqlite-utils \
  --description "CLI tool and Python library for manipulating SQLite databases" \
  --size small --harness claude -y
```
**TASK (verbatim):** "The test
`tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table`
fails. Find the root cause and fix it." *(Symptom is `table "books_fts" already
exists`; root cause is two hops away in `detect_fts` — `content=[...]` vs
`content="..."` LIKE pattern. Reward root-cause fix over symptom patch.)*

**GATE** (`python:3.12`):
```bash
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'
# + git -C "$WORK_DIR" diff --stat -- tests/  shows NO test file changed
```
PASS = full suite green (the previously failing test now passes) AND no test
file modified.

### Cell 4 — py-feature (sqlite-utils, small)

```bash
# SEED (clean checkout, no revert)
git clone https://github.com/simonw/sqlite-utils.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 79117b9
# SCAFFOLD  (same as cell 3)
python3 "$FRAMEWORK" --name sqlite-utils \
  --description "CLI tool and Python library for manipulating SQLite databases" \
  --size small --harness claude -y
```
**TASK (verbatim):** "Add a `rename-column` CLI command and a
`Table.rename_column(old, new)` API method, mirroring the existing `rename-table`
command / `rename_table()` pattern (cli.py:1681, db.py:1233). Include tests and
doc updates." *(May delegate to `transform()`; watch for the `transform(rename=)`
silent-data-loss collision — add an `AlterError` guard + regression test.)*

**GATE** (`python:3.12`):
```bash
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'
```
PASS = full suite green including the agent's new tests. (Also run the repo's
own configured lint if defined; recorded, not gating.)

### Cell 5 — ros-refactor (navigation2, large)

```bash
# SEED
git clone https://github.com/ros-navigation/navigation2.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 60e82dbb634bd93aed18f2f8d39b27d4b8656038
# SCAFFOLD
python3 "$FRAMEWORK" --name navigation2 \
  --description "ROS 2 Navigation (Nav2) stack — C++ / colcon / ament" \
  --size large --harness claude -y
```
**TASK (verbatim):** "In `nav2_velocity_smoother`, extract a self-contained
helper (the per-axis velocity clamping / deadband math) out of the node class
into its own free-function header + translation unit, with zero behavior change.
The package's existing tests must pass unmodified (nothing under
`nav2_velocity_smoother/test/` changes)." *(Large profile: run explore as its own
session that commits the KB, then plan/implement in a second session.)*

**GATE** (`ros2-nav2-builder`, work dir mounted; build only the touched package):
```bash
docker run --rm -v "$WORK_DIR":/workspace ros2-nav2-builder bash -c '
  cd /workspace && . /opt/ros/jazzy/setup.sh
  apt-get update -qq                                   # image strips apt lists
  rosdep install --from-paths . --ignore-src -y --rosdistro jazzy  # SEED clones to root, no src/
  apt-get install -y ros-jazzy-bondcpp ros-jazzy-geographic-msgs   # rosdep misses these; needed at test/configure
  colcon build --packages-up-to nav2_velocity_smoother --executor sequential  # parallel executor races on nav2_behavior_tree
  . install/setup.sh                                   # overlay so the gtest finds libbondcpp.so
  colcon test --packages-select nav2_velocity_smoother
  colcon test-result --verbose; echo "EXIT: $?"'
# + git -C "$WORK_DIR" diff --stat -- '*/nav2_velocity_smoother/test/*'  is EMPTY
```
PASS = build succeeds AND `colcon test` passes (0 errors, 0 failures; the
unmodified baseline is 46 tests / 6 skipped) AND no test source under
`nav2_velocity_smoother/test/` changed.

*Gate environment notes (validated 2026-07-04): the four inline corrections above
are required for the gate to build against the pinned SEED/image at all
(`--from-paths .` not `src`; `apt-get update` before rosdep; explicit
`bondcpp`/`geographic_msgs` since rosdep does not pull them and exits 0 anyway;
`--executor sequential` to avoid a parallel race that fails `nav2_behavior_tree`).
Do not "simplify" them back.*

### Cell 6 — ros-plan (navigation2, large, plan-only)

Same SEED and SCAFFOLD as cell 5.
**TASK (verbatim):** "Plan a new `nav2_behaviors` behavior plugin (a simple
time-based motion that does not already exist in `nav2_behaviors/plugins/`),
mirroring an existing behavior: a class deriving `nav2_core::Behavior` via
`TimedBehavior<ActionT>`, the `behavior_plugin.xml` pluginlib export, the
matching `nav2_msgs` action if needed, `package.xml`/`CMakeLists.txt` wiring, and
a `nav2_bringup` params entry enabling it." *Plan-only — stop at the plan-review
gate.* Existing behaviors to avoid duplicating: back_up, spin, wait,
drive_on_heading, assisted_teleop.

**GATE** (deterministic static checks, all must hold):
plan.md schema-valid (frontmatter keys + kb-commit present); every task file
self-contained per the task-file format; every affected file exists at the
pinned SHA; the chosen behavior name is absent from `nav2_behaviors/plugins/`;
and one control build of the UNMODIFIED workspace succeeds to prove the
environment is real, using the same corrected setup as cell 5's gate:
```bash
docker run --rm -v "$WORK_DIR":/workspace ros2-nav2-builder bash -c '
  cd /workspace && . /opt/ros/jazzy/setup.sh
  apt-get update -qq
  rosdep install --from-paths . --ignore-src -y --rosdistro jazzy
  apt-get install -y ros-jazzy-bondcpp ros-jazzy-geographic-msgs
  colcon build --packages-up-to nav2_behaviors --executor sequential; echo "EXIT: $?"'
```
PASS = all true. (See cell 5's gate environment notes; the same four corrections
apply. `--executor sequential` matters most here: the parallel executor
intermittently fails `nav2_behavior_tree`.)

### Cell 7 — ng-plan (Understand-Anything, large, plan-only)

```bash
# SEED
git clone https://github.com/Egonex-AI/Understand-Anything.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 0e8ad84a2a5236dca533beef618d71ee3f4568f6
# SCAFFOLD
python3 "$FRAMEWORK" --name understand-anything \
  --description "TypeScript / Angular monorepo (pnpm workspaces)" \
  --size large --harness claude -y
```
**TASK (verbatim):** "Add Angular detection to `@understand-anything/core`'s
framework registry: a new `FrameworkConfig` plus its three-place registration and
a registry test." *Plan-only.*

**GATE** (no container; static checks, all must hold): plan.md schema-valid;
every task file self-contained; affected files exist at the pinned SHA; the
planned `FrameworkConfig` validates against `FrameworkConfigSchema`; the three
registration sites named in the plan exist in the repo. PASS = all true.

---

## Shared agent prompt

> Copy verbatim per cell. Fill ONLY `{MODEL}` and `{EFFORT}` (your two inputs).
> Every other `{...}` is a fixed constant read from the cell's block above; paste
> its pinned value, do not invent one.

```
You are benchmark agent {RUN_ID} running the llm-agent-framework {PROFILE} profile.
Model: {MODEL} | Effort: {EFFORT}

AUTONOMOUS RUN. No human is available. Resolve every question from code evidence,
record numbered assumptions in .ai files, and proceed without blocking. Follow
the framework's own skills and phase docs; do not improvise another workflow.
EFFORT semantics: {paste the matching low/medium/high tier text}.

Record start: date '+%Y-%m-%dT%H:%M:%S'

STEP 1 — SETUP: run the cell's SEED commands, then cd $WORK_DIR and run the
cell's SCAFFOLD command exactly as written.

STEP 2 — EXPLORE: read .claude/skills/explore/SKILL.md and follow it. Run
python3 .ai/agent/tools/probe.py first. Fill the AGENTS.md project-context (small)
or the KB nodes + manifest (large), and .ai/notes.md. Commit .ai.
(Large profile: make explore its own session/commit before planning.)

STEP 3 — SPEC/TICKET+PLAN: follow the profile's skill(s). Write the spec (small)
or ticket + self-contained task files (large) for the cell's TASK. Verify any
premise in the TASK against the code before acting; record findings as numbered
assumptions. Commit .ai.

STEP 4 — BUILD/IMPLEMENT: follow the skill. Make the changes. Run the framework
review gate (spawn the reviewer sub-agent with only the diff + acceptance
criteria; if you cannot spawn one, self-review and say so). Fix correctness gaps.
Set status=done. Commit .ai. (Plan-only cells 6-7 stop after the plan-review gate.)

STEP 5 — GATE: run the cell's GATE commands exactly. Record full output and the
PASS/FAIL per the cell's rule. Do not modify the target to make the gate pass in
a way the TASK forbids (e.g. editing tests in a refactor cell).

STEP 6 — RESULTS: write /tmp/benchmark/results/{RUN_ID}.md with: Configuration
table (Run ID, Cell, Profile, Model, Effort, Start, End, Duration, Gate PASS/FAIL);
Auto-size line printed at scaffold (informational); Spec/plan produced;
.ai commit history (git -C .ai log --oneline); target diff (git diff --stat HEAD +
full diff); any premise-verification finding; full gate output; 3-5 observations.

Report back a concise summary: gate PASS/FAIL per check, premise findings,
duration. Do not sanitize failures.
```

---

## Baseline arm (B-cells, no scaffold; optional, fixed)

Answers the token-economy question: what does the same task cost the same
model WITHOUT the framework? A B-cell is the paired twin of a numbered cell:
**identical SEED (same SHA, same revert), identical TASK text, identical GATE
and image, same MODEL x EFFORT, run in the same round directly after its
framework twin.** The only difference: the SCAFFOLD step is skipped entirely
(no `init_agent.py`, no `.ai`, no AGENTS.md, no skills).
`RUN_ID = <cell>-baseline-<date>`; own work dir
`/tmp/benchmark/runs/$RUN_ID/<repo>` (separate transcript dir, so
`count_tokens.py` separates the arms automatically).

- **Eligible: cells 1-5** (target-repo-state gates, scaffold-agnostic).
  **Not eligible: cells 6-7** — their gates check plan.md schema and task-file
  format, i.e. framework artifacts a bare agent does not produce.
- **Canonical pair: B3 + B4** (cheap, fast, shared SHA). B1/B2/B5 optional;
  B5 is the expensive large-repo data point where the amortization thesis
  actually lives.
- **Permission mode (fixed):** any round that includes B-cells dispatches
  BOTH arms in the harness's bypass-permissions mode. The framework arm's
  scaffolded allowlist must not be a hidden advantage; otherwise the round
  measures prompt friction, not token economy.
- **Reviewer cost stays in.** The framework arm's reviewer sub-agent tokens
  are part of the framework's price; report them inside its total, never
  "corrected" out.

### Baseline agent prompt (fixed; replaces the shared prompt for B-cells)

> Copy verbatim. Fill ONLY `{MODEL}` and `{EFFORT}`. The premise-verification
> sentence stays wordwise identical to the framework prompt: it tests the
> model, not the framework, and must be constant across arms.

```
You are benchmark agent {RUN_ID} (BASELINE arm, no framework).
Model: {MODEL} | Effort: {EFFORT}

AUTONOMOUS RUN. No human is available. Resolve every question from code
evidence, record numbered assumptions in $WORK_DIR/../BASELINE-NOTES.md (not
inside the target repo), and proceed without blocking. There is no prescribed
workflow, no required artifacts, and no framework: work directly on the task
in whatever way you consider best.
EFFORT semantics: {paste the matching low/medium/high tier text}.

Record start: date '+%Y-%m-%dT%H:%M:%S'

STEP 1 — SETUP: run the cell's SEED commands (no scaffold), then cd $WORK_DIR.

STEP 2 — TASK: solve the cell's TASK. Verify any premise in the TASK against
the code before acting; record findings as numbered assumptions.

STEP 3 — GATE: run the cell's GATE commands exactly. Record full output and
the PASS/FAIL per the cell's rule. Do not modify the target to make the gate
pass in a way the TASK forbids (e.g. editing tests in a refactor cell).

STEP 4 — RESULTS: write /tmp/benchmark/results/{RUN_ID}.md with: Configuration
table (Run ID, Cell, Arm=baseline, Model, Effort, Start, End, Duration, Gate
PASS/FAIL); target diff (git diff --stat HEAD + full diff); any
premise-verification finding; full gate output; 3-5 observations.

Report back a concise summary: gate PASS/FAIL per check, premise findings,
duration. Do not sanitize failures.
```

Token counting is the same orchestrator duty as for numbered cells
(`python3 "$TOKENS" "$WORK_DIR" >> .../results/$RUN_ID.md`).

### B-amortized (fixed sequence; tests the amortization thesis)

The framework's claimed win is the SECOND task in the same repo. Cells 3 and 4
share the sqlite-utils SHA, so:

- `py-seq-<date>` (framework arm): ONE work dir, cell 3's SEED (with revert),
  scaffold once. Session 1: explore + cell 3's TASK to done. Session 2 (fresh
  session, same work dir): cell 4's TASK to done. Both gates as written.
- `py-seq-baseline-<date>` (baseline arm): ONE work dir, same SEED, no
  scaffold. Session 1: cell 3's TASK. Session 2 (fresh session, no memory):
  cell 4's TASK. Both gates as written.

Measure with `count_tokens.py --per-session`: the comparison number is the
**marginal cost of session 2** per arm. If the framework's session 2 is not
clearly cheaper than the baseline's, the amortization thesis failed the test;
say so in the report.

### Comparison table (fixed report format, informational, never gating)

```
| Pair | Arm | Gate | Probe caught | Output tokens | Total tokens | Duration |
|---|---|---|---|---|---|---|
| 3 py-bugfix | framework | ... | ... | ... | ... | ... |
| 3 py-bugfix | baseline  | ... | ... | ... | ... | ... |
```

Report output tokens separately: cache reads dominate totals and the two arms
have very different cache profiles. Interpretation guardrails: n=1 per pair
has high agentic variance; treat deltas under ~30-40% as noise, repeat the
cheap B-cells before concluding anything from a close result. Expected shape
(the concept's own prediction, §13/§9): baseline wins or ties one-shot cells
on small repos; framework must win the B-amortized session 2 and the large-
repo pair. A baseline loss on one-shot small cells is NOT a framework defect;
a framework loss on B-amortized session 2 is.

---

## Worker arm (W-cells, code-worker dispatch; optional, fixed)

Answers the delegation question (CONCEPT §23): what does the same framework
task cost when `/build` dispatches eligible checklist items to the scaffolded
`code-worker` sub-agent instead of implementing inline? A W-pair consists of
two twins of a numbered cell, **both framework-scaffolded**: identical SEED,
TASK, GATE and image, same MODEL x EFFORT, same round. The only difference is
the /build execution mode, controlled by one added prompt line each:

- **solo twin** (control), `RUN_ID = <cell>-solo-<date>`: shared agent prompt
  plus the line "Work every implementation task inline yourself; do NOT
  dispatch to the code-worker sub-agent." (The scaffold ships the worker, so
  without this line the control arm is uncontrolled.)
- **worker twin**, `RUN_ID = <cell>-worker-<date>`: shared agent prompt plus
  the line "Dispatch checklist items that meet /build's delegation rules
  (fully specified, test-verifiable, mechanical or multi-file) to the
  `code-worker` sub-agent; re-run the tests yourself after every worker
  report."

Fixed rules:
- **Eligible:** implementation cells whose TASK is multi-file — cell 4
  canonical; 1, 2, 5 optional. **Cell 3 is NOT eligible:** its fix is a
  one-file change that /build's own right-sizing keeps inline; a W3 would
  measure rule violation, not delegation. Plan-only cells 6-7 ineligible.
- **Worker model comes from the scaffolded frontmatter** (`model: sonnet`),
  never overridden per cell. With MODEL = claude-sonnet-5 the pair isolates
  delegation mechanics (context hygiene) at constant tier; with a stronger
  MODEL it additionally measures the tier price gap. Record which
  configuration ran.
- Own work dir per twin (separate transcript dirs); worker sub-agent usage
  is sidechain usage and lands in the worker twin's total automatically.
- Both twins bypass-permissions (same rule as B-cells). Reviewer cost stays
  in both totals.
- Gate re-verified by the orchestrator for both twins (a worker's
  self-reported pass is doubly untrusted).

Comparison table: same fixed format as the B-cells (Pair | Twin | Gate |
Output tokens | Total tokens | Duration), output tokens reported separately.
Interpretation guardrails: n=1 per pair, deltas under ~30-40% are noise. A
worker-twin token loss on a small repo is consistent with §13/§23 (dispatch
overhead has a scale threshold) and is not a defect by itself; the strong
delegation claim (net token win) FAILS the test if the worker twin costs
more in BOTH total and output tokens at an equal gate outcome. Correctness
divergence between twins is reported alongside, with the same weight.

---

## Results and evaluation (fixed format)

Each cell writes `/tmp/benchmark/results/<RUN_ID>.md` (structure above). After a
round, verify every cell against this checklist:

```
[ ] SEED produced the pinned state (SHA checked out; py-bugfix test fails pre-run)
[ ] auto-size (informational) printed the expected profile at the pinned SHA
[ ] .ai commit sequence matches profile
     small: init -> explore -> spec -> build
     large: init -> explore -> ticket -> plan [-> implement]
[ ] gate ran exactly as written and recorded PASS/FAIL (plan cells: all static checks)
[ ] refactor cells: no test files modified
[ ] token usage appended by the orchestrator (count_tokens.py block present)
[ ] results file written in the fixed format
[ ] B-cells only: same SEED/TASK/GATE as the twin, no scaffold, both arms in
    bypass-permissions mode, comparison table in the report
[ ] B-amortized only: per-session token split recorded (--per-session)
[ ] W-cells only: both twins scaffolded, one-line mode instruction per twin,
    worker model from frontmatter (recorded), orchestrator re-ran the gate
    for both twins, comparison table in the report
```

To record a round in the repo: create `benchmarks/<run>/report.md` and copy the
raw per-cell results under `benchmarks/<run>/results/`. Report PASS/FAIL from the
deterministic gate only; rubric-style quality notes are recorded, never gating.

## Determinism guarantees

- **Pinned:** every repo SHA, seed (incl. the py-bugfix reverse-apply), scaffold
  command, size profile, Docker image (by inline Dockerfile), gate command, and
  PASS rule are constants in this file.
- **User-set:** MODEL and EFFORT only.
- **Expected to drift, non-gating:** wall-clock duration, token usage (recorded
  every run via `count_tokens.py`, orchestrator duty; comparable within a round,
  drifts across models/dates), exact prose the agent writes, and any
  upstream-image package versions (`rust:latest`, `ros:jazzy`, `python:3.12`
  float; pin the image tags too if byte-for-byte gate reproduction is
  required). The code under test does not drift because targets are pinned to
  SHAs, not branches.
