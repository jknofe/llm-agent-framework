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

## Quality assessment (rubric, non-gating)

The gate is binary; it says nothing about whether a passing solution is minimal,
idiomatic, or robust. This section rates each agent's solution from its actual
diff (read against the pinned base, not from the agent's self-report). Scores are
1-5 per dimension and do not affect PASS/FAIL.

Dimensions: **Corr** = correctness and robustness beyond the gate (edge cases,
safety); **Min** = scope discipline / minimalism (no unrelated changes);
**Idiom** = fit with surrounding conventions and readability; **Probe** = how
well the cell's deliberate trap was handled; **T&D** = tests and docs.

| Cell | Corr | Min | Idiom | Probe | T&D | Overall |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 sh-refactor | 5 | 5 | 5 | 5 | 5 | **A (exemplary)** |
| 2 rust-package | 4.5 | 4 | 5 | 5 | 4.5 | **A-** |
| 3 py-bugfix | 5 | 4.5 | 4.5 | 5 | 4.5 | **A-** |
| 4 py-feature | 4.5 | 4.5 | 5 | 4 | 5 | **B+/A-** |

**Cell 1 sh-refactor (A, exemplary).** Merged only the two genuinely identical
`abort()` definitions into `common.bash` and preserved behavior exactly: because
`bats-exec-suite`'s original `abort` never called `usage`, the agent passed
`--no-print-usage` at all three of its call sites so the shared function is a
byte-for-byte behavioral match. It kept `bats-gather-tests`'s different contract
separate and, beyond the brief, caught that the script transitively re-sources
`common.bash` (which would silently clobber a same-named local function),
renaming it to `bats_gather_tests_abort` with a comment explaining both the
collision and the differing contract. Minimal, idiomatic, self-documenting.
Nothing to fault.

**Cell 2 rust-package (A-).** Every high-effort policy item is present and
correct: full asset set at the right Debian paths, zsh `vendor-completions/`,
`section`/`priority`/`extended-description`/`license-file`, and a working
`deb: build-release` target. Two small deductions: (a) the diff also strips
trailing whitespace from the unrelated `package` target lines in the Makefile
(a harmless but unrequested edit, minor scope creep); (b) the `depends` version
pins (`libgtk-4-1 (>= 4.0.0)`, `libadwaita-1-0 (>= 1.0.0)`, `fontconfig (>=
2.13.0)`) are plausible but not derived from a verified runtime requirement, so
they read as reasonable guesses rather than checked minimums.

**Cell 3 py-bugfix (A-).** Root-cause fix in `detect_fts`, not a symptom
patch, and it restores the correct two-pattern logic (`like` = bracket-quoted
`content=[...]`, `like2` = double-quoted `content="..."`). The net difference
between the final code and the canonical upstream fix is a single cosmetic quote
character on the `like` line, i.e. the agent independently re-derived
essentially the real fix. No test file touched. The only nit is that trivial
quote-style residue (double to single) which adds a tiny stylistic inconsistency
with no functional effect.

**Cell 4 py-feature (B+/A-).** The most complete deliverable: CLI command + API
method mirroring `rename-table`, `--ignore` + `load_extension` options, RST docs,
and three tests (API, CLI, and the collision regression). Identifiers are passed
through `quote_identifier`, so it is injection-safe. The judgment call is the
probe: the runbook hint anticipated the agent delegating to `transform()` and
needing an `AlterError` guard against the `transform(rename=)` silent-data-loss
collision. Instead the agent implemented a direct `ALTER TABLE RENAME COLUMN`,
which sidesteps the collision entirely rather than guarding it, and proved
coexistence with a regression test. That is a defensible (arguably simpler and
safer) design, but it is not the guard the hint literally called for, so the
probe is handled by avoidance rather than by the expected mechanism. Minor edge:
`rename-column --ignore` also swallows a "new name already exists" error, which
is slightly broader than the mirrored `rename-table` semantics.

## Aggregate

All four solutions are production-plausible; none merely games the gate. Mean
overall lands around A-/A. The floor is high (cell 4's B+) and the ceiling is a
clean exemplary pass (cell 1). The recurring haiku-x-high signature: correct and
well-tested, with the small deductions coming from minor scope creep (cell 2),
cosmetic residue (cell 3), or a defensible-but-literal-hint-missing design choice
(cell 4) rather than from any correctness gap.

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
