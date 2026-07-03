# Benchmark Report: fast-core on haiku x high

**Date:** 2026-07-03
**Model/effort:** claude-haiku-4-5 x high
**Framework state:** current HEAD (v5.9), commit `9bd26e5`.
**Runbook:** [../fixed-runbook.md](../fixed-runbook.md), cells 1-4 (fast core).
**Raw results:** [results/](results/) (one file per cell).

Purpose: run the fixed reproducible runbook's fast-core cells (the four that need
no heavy compile) at the smallest model, highest effort, to check that
claude-haiku-4-5 drives the small-profile chain end to end and passes every
deterministic gate. Cells 5-7 (ROS 2 colcon, Angular plan) were not run this
round; the `ros2-nav2-builder` image was not built and those cells add ~3-4 h.

Each cell was executed by one autonomous agent, dispatched strictly sequentially
(one at a time, wait for its gate before the next). Every gate below was then
**re-run independently by the orchestrator** on the intact work dir, not trusted
from the agent's self-report. PASS/FAIL is the container gate only.

## Configuration

| Field | Value |
|---|---|
| Cells | 1 sh-refactor, 2 rust-package, 3 py-bugfix, 4 py-feature |
| Profile | small (pinned via `--size small`; auto-size not exercised this round) |
| Model x effort | claude-haiku-4-5 x high (constant across all cells) |
| Harness | claude |
| Gate images | `bats-eco-builder`, `satty-deb-builder`, `python:3.12` |

Auto-size note: the runbook pins the profile with `--size small`, so no
`auto-size:` line is emitted. Auto-size is a separate informational check
(`--size auto`) not exercised here.

## Results: 4/4 PASS (independently re-verified)

| # | Cell | Target @ pinned SHA | Gate re-verification | Result |
|---|---|---|---|---|
| 1 | sh-refactor | bats-core @ `5a7db7a` | `bin/bats test` exit 0, **479/479 ok**; `shellcheck -x` exit 0 on all 4 changed scripts; `test/` diff empty | **PASS** |
| 2 | rust-package | Satty @ `2d18065` | `cargo deb --no-build` produced `satty_0.21.1-1_arm64.deb`; `dpkg-deb --contents` lists binary, `.desktop`, SVG icon, all 6 completions, man page, copyright | **PASS** |
| 3 | py-bugfix | sqlite-utils @ `79117b9` | full suite **1080 passed, 16 skipped**, exit 0; `tests/` diff empty | **PASS** |
| 4 | py-feature | sqlite-utils @ `79117b9` | full suite **1085 passed, 16 skipped**, exit 0 (includes the agent's 3 new tests) | **PASS** |

Container note (cell 1): the bats suite needs `TERM=xterm` in the image, else
unrelated `tput`/TERM tests fail identically before and after the change. The
gate sets `TERM=xterm`; with it the suite is fully green.

## Probe findings (the quality signal)

Each cell embeds a deliberate trap. Haiku at high caught all four.

- **Cell 1 wrong-premise (caught).** The brief asserts the three `abort()`
  definitions are identical; they are not. The agent merged only the two true
  variants (`bats`, `bats-exec-suite`) into `lib/bats-core/common.bash`, and kept
  `bats-gather-tests`'s different contract (`printf` format-string passthrough,
  `ERROR:` prefix). It further found that `bats-gather-tests` transitively
  re-sources `common.bash`, which would silently clobber a same-named local
  function once the shared one exists, and renamed the local function to
  `bats_gather_tests_abort` to avoid the collision. Byte-for-byte output
  unchanged; no forced wrong merge.
- **Cell 2 policy depth (met).** At high the agent added the Debian zsh
  `usr/share/zsh/vendor-completions/` path, `section`, `priority`,
  `extended-description`, `license-file`, and version-pinned depends. It
  self-corrected a cargo-deb constraint (`copyright` must be a string, not an
  array) on the second gate run.
- **Cell 3 root cause vs symptom (root cause).** The symptom is
  `table "books_fts" already exists`; the agent traced it two hops to the real
  cause in `detect_fts` (the `like`/`like2` LIKE patterns were identical, so
  bracket-quoted legacy `content=[...]` tables were never detected) and fixed
  the patterns. Single-line fix in `db.py`; no test file touched.
- **Cell 4 silent-data-loss collision (guarded).** The agent added a regression
  test (`test_rename_column_vs_transform_rename_collision`) proving
  `rename_column()` and `transform(rename=)` coexist without data loss, mirroring
  the existing `rename-table` pattern for the CLI command and API method.

## Observations

- **Fast core is clean at the smallest model when effort is high.** 4/4 gates
  pass and every probe is caught. Haiku x high matched the sonnet x medium
  reference on the shared cell (cell 1: same dedup, same transitive-re-source
  fix, 479/479).
- **Effort carried the policy detail.** Cell 2's high-only items
  (`vendor-completions/`, `license-file`, `section`/`priority`) all appeared,
  consistent with prior rounds where effort, not model, predicts policy depth.
- **Self-correction inside the gate loop worked.** Cell 2's `copyright`
  array-vs-string error was caught and fixed by the agent's own gate run, not by
  the orchestrator.
- **Benign target-repo change (cell 1).** The agent added `.ai/` to the
  target's `.gitignore` (1 line). Not a script, outside the gate; keeps the
  scaffold out of the target's history. No behavior impact.
- **Scope.** Fast core only; cells 5-7 (ROS 2 refactor + plan, Angular plan)
  were not run. A partial round is valid per the runbook; those cells remain the
  cross-ecosystem reference for a later full round.

## Verdict

The framework at v5.9 HEAD passes the full fast-core set at claude-haiku-4-5 x
high, all four deterministic gates green on independent re-verification, and all
four embedded probes caught. No framework defects surfaced this round.
