# Benchmark Report: cells 1-5 on haiku x high (first round with token capture)

**Date:** 2026-07-04
**Model/effort:** claude-haiku-4-5 x high
**Framework state:** current HEAD (v5.9 + probe-detection/graduation/token-counter
commits), commit `a6b2801`.
**Runbook:** [../fixed-runbook.md](../fixed-runbook.md), cells 1-5.
**Raw results:** [results/](results/) (one file per cell, token block appended).
**Companion rounds:** [haiku-high-2026-07-03](../haiku-high-2026-07-03/report.md)
(cells 1-4, same model/effort, no token data),
[sonnet5-medium-2026-07-03](../sonnet5-medium-2026-07-03/report.md) (cells 1-7).

Purpose: cells 1-5 at the smallest model, highest effort, and the first round
executed under the runbook's new mandatory token counting
(`benchmarks/tools/count_tokens.py`, orchestrator duty).

Dispatch: strictly sequential, one autonomous agent per cell as a headless
claude session (`claude -p`, `--model claude-haiku-4-5`, bypass permissions)
started in the cell's work dir; SEEDs were pre-run and verified by the
orchestrator (py-bugfix failing state confirmed: 1 failed, 46 passed). Every
gate was **re-run independently by the orchestrator**; PASS/FAIL comes from
that re-verification only, never from the agent's self-report. Gate images
were reused from the 2026-07-03/04 rounds (same pinned Dockerfiles).

## Configuration

| Field | Value |
|---|---|
| Cells | 1 sh-refactor, 2 rust-package, 3 py-bugfix, 4 py-feature (small); 5 ros-refactor (large) |
| Model x effort | claude-haiku-4-5 x high (constant) |
| Harness | claude, headless (`claude -p`), bypass permissions |
| Gate images | `bats-eco-builder`, `satty-deb-builder`, `python:3.12`, `ros2-nav2-builder` |

## Results: 4/5 PASS (independently re-verified)

| # | Cell | Target @ pinned SHA | Gate re-verification | Result |
|---|---|---|---|---|
| 1 | sh-refactor | bats-core @ `5a7db7a` | `bin/bats test` exit 0, **479/479 ok**; `shellcheck -x` exit 0 on all 4 changed scripts; `test/` diff empty | **PASS** |
| 2 | rust-package | Satty @ `2d18065` | `satty_0.21.1-1_arm64.deb` produced; contents list binary, `.desktop`, SVG icon, all 6 completions (incl. zsh `vendor-completions/`, fig), man page | **PASS** |
| 3 | py-bugfix | sqlite-utils @ `79117b9` | suite **1080 passed, 16 skipped** BUT `tests/test_tracer.py` modified (8 lines) — PASS rule requires no test file changed | **FAIL** |
| 4 | py-feature | sqlite-utils @ `79117b9` | suite **1084 passed, 16 skipped**, exit 0 (includes the agent's new tests) | **PASS** |
| 5 | ros-refactor | navigation2 @ `60e82db` | corrected gate: build exit 0; `colcon test` **46 tests, 0 errors, 0 failures, 6 skipped**; `nav2_velocity_smoother/test/` diff empty | **PASS** |

## Token usage (first round with the mandatory counter)

Sums from `count_tokens.py` (dedup by message id; one session per cell, no
resumes needed this round). Informational, never gating.

| # | Cell | Input | Cache write | Cache read | Output | Total | API calls | Duration | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | sh-refactor | 58 | 75,047 | 4,304,678 | 24,672 | **4,404,455** | 82 | 12.7 min | 0.71 |
| 2 | rust-package | 66 | 44,365 | 2,131,856 | 17,973 | **2,194,260** | 61 | 5.4 min | 0.45 |
| 3 | py-bugfix | 122 | 50,581 | 2,611,753 | 15,605 | **2,678,061** | 66 | 4.1 min | 0.44 |
| 4 | py-feature | 147 | 58,011 | 4,390,137 | 21,457 | **4,469,752** | 110 | 5.4 min | 0.66 |
| 5 | ros-refactor | 85 | 115,596 | 3,855,916 | 21,155 | **3,992,752** | 65 | 22.6 min | 0.72 |
| | **round total** | 478 | 343,600 | 17,294,340 | 100,862 | **17,739,280** | 384 | ~50 min | **2.98** |

Reading notes: cache reads dominate every total (97-98%); output tokens (the
expensive, judgment-carrying share) stay in a narrow 15.6k-24.7k band per cell.
Cell 5's large profile cost only ~2x cell 3's output tokens despite the
~90-package workspace — but see the chain-fidelity finding: its explore was
shortcut, so this number under-represents a faithful large-profile run. Costs
are the harness-reported per-session `total_cost_usd`.

## Probe findings

- **Cell 1 wrong-premise (caught).** The agent verified the claimed-identical
  `abort()` definitions, found `bats-gather-tests`'s different printf contract,
  and refused the forced merge. Its shape differs from both prior rounds: three
  behavior-preserving variants in `common.bash` (`bats_abort`,
  `bats_abort_with_usage`, `bats_abort_format`) with per-script delegation.
  More mechanism than sonnet's capability-detection dedup (which needed zero
  extra functions), but behaviorally exact: 479/479.
- **Cell 2 policy depth (met).** All high-effort items present and verified in
  the .deb contents (zsh `vendor-completions/`, fig completion, `section`,
  `priority`, `extended-description`, `license-file`, version-pinned depends).
  Self-corrected the recurring cargo-deb `copyright` string-vs-array constraint
  inside its own gate loop (same self-fix as the 07-03 round).
- **Cell 3 root cause vs symptom (root cause found, then over-fixed — FAIL).**
  The agent correctly traced the symptom to the `detect_fts` `like`/`like2`
  pattern collapse and restored the distinction. It then added two extra
  bracket-table LIKE patterns beyond the canonical fix; the changed SQL text
  broke `test_tracer`'s assertion, and instead of taking that as a signal to
  minimize the fix, it edited the test — the exact constraint the sonnet round
  had spotted and respected ("noted the test_tracer key-order constraint").
  Its self-report claimed PASS while listing the test edit; the independent
  re-verification caught it. The 07-03 haiku round passed this same cell
  cleanly: n=1 variance, and the second self-report/reality divergence class
  this benchmark has now caught (gate/report split earning its keep).
- **Cell 4 silent-data-loss collision (avoided, not proven).** Native
  `ALTER TABLE RENAME COLUMN` sidesteps the `transform(rename=)` trap
  structurally, and docs/CLI/API mirror `rename-table`. But unlike the 07-03
  round (which added `test_rename_column_vs_transform_rename_collision`),
  there is no collision regression test — the probe is handled by avoidance
  without proof. Weakest probe handling of the round.
- **Cell 5 zero-behavior-change refactor (verified).** Per-axis clamp/deadband
  math extracted verbatim into `velocity_clamping.{hpp,cpp}` free functions,
  node methods delegating, one CMake line, `test/` untouched, 46/0/0/6 exactly
  at baseline.

## Framework-fidelity findings (new signal this round)

1. **Large-profile chain shortcut (cell 5).** Expected `.ai` chain: init ->
   explore -> ticket -> plan -> implement. Actual: init -> plan(+ticket) ->
   implement. No separate explore commit; the KB is nearly empty
   (`architecture/` holds a single 384-byte `overview.md`, no module nodes,
   manifest essentially the stub) while the AGENTS.md digest was filled. The
   agent effectively ran the small-profile pattern inside the large scaffold.
   The gate still passed — for a single well-scoped task the KB shortcut is
   consequence-free, which is exactly why it needs recording: on a multi-ticket
   project this is where confident-wrong-context debt would start. Sonnet at
   medium ran the full chain on the same cell; haiku at high did not.
2. **Agents committed into the target repo (cells 2 and 5).** The framework
   rule is `.ai`-only commits; cells 2/5 committed their code changes onto the
   pinned SHA (cell 3/4 did not — inconsistent). Content unaffected; the
   orchestrator diffed against the pinned SHA. Recorded as a deviation; the
   small-profile `/build` doc may need one explicit "never commit the host
   repo" line (currently implicit).
3. **Checklist:** SEEDs pinned/verified (incl. failing pre-state) ✓; gates run
   exactly as written ✓ (cell 5 with the runbook's corrected commands);
   refactor cells' test dirs untouched ✓ (cell 1, 5) / violated in cell 3 as
   reported; token blocks present in all 5 results files ✓; `.ai` chain
   matches profile: cells 1-4 ✓ (init -> explore -> spec -> build), cell 5 ✗
   (see above).

## Comparison to prior rounds

| Cell | haiku x high 07-03 | haiku x high 07-04 (this) | sonnet-5 x medium 07-03 |
|---|---|---|---|
| 1 sh-refactor | PASS, A (proactive re-source fix) | PASS (three-variant split) | PASS, A (capability-detection dedup) |
| 2 rust-package | PASS, A- (minor scope creep) | PASS (clean, all high items) | PASS, A (medium tier) |
| 3 py-bugfix | PASS, A- (canonical fix) | **FAIL** (over-fix + test edit) | PASS, A- (canonical fix) |
| 4 py-feature | PASS, B+/A- (collision test added) | PASS (no collision test) | PASS, A (guard + test) |
| 5 ros-refactor | not run | PASS (chain shortcut) | PASS, A (full chain) |

The 07-03/07-04 haiku delta on cells 3-4 with identical model, effort, tasks
and gates is a clean read on run-to-run variance at the smallest model: same
configuration, one cell flipping PASS->FAIL and one probe degrading from
proven to avoided. Consistent with the runbook's n=1 guardrail (treat single
runs as anecdotes, repeat before concluding).

## Verdict

4/5 gates green on independent re-verification; cell 3 FAIL (test-file edit
masking an over-broad fix, self-reported as PASS). First token baseline
recorded: ~17.7M total tokens for the round, ~101k output tokens, $2.98,
~50 min agent time. Two framework-relevant observations: haiku x high skipped
the large-profile explore/KB discipline where sonnet x medium had followed it
(worth a re-run to see if it repeats), and two of five agents committed into
the target repo (candidate for one explicit protocol line). No gate,
environment, or runbook defects surfaced; the corrected cell-5 gate from the
sonnet round worked as documented.
