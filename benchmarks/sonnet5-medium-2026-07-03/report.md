# Benchmark Report: fast-core on sonnet-5 x medium

**Date:** 2026-07-03 (cell 4 finished 2026-07-04 after a session-limit reset)
**Model/effort:** claude-sonnet-5 x medium
**Framework state:** current HEAD (v5.9), commit `738ad86`.
**Runbook:** [../fixed-runbook.md](../fixed-runbook.md), cells 1-4 (fast core).
**Raw results:** [results/](results/) (one file per cell).
**Companion round:** [../haiku-high-2026-07-03/report.md](../haiku-high-2026-07-03/report.md)
(same four cells at claude-haiku-4-5 x high).

Purpose: the same fast-core set as the haiku x high round, now at
claude-sonnet-5 x medium. Note both axes differ (model and effort), so this is a
paired-cell comparison of two configurations, not a single-variable isolation.
The cell tasks, SHAs, and gates are identical, so solution-quality observations
remain directly comparable.

Each cell was executed by one autonomous agent, dispatched strictly sequentially.
Every gate below was **re-run independently by the orchestrator** on the intact
work dir, not trusted from the agent's self-report. PASS/FAIL is the container
gate only. Cell 4's agent hit a session limit mid-run and was resumed (the same
agent, same work dir, per the runbook) rather than relaunched.

## Configuration

| Field | Value |
|---|---|
| Cells | 1 sh-refactor, 2 rust-package, 3 py-bugfix, 4 py-feature |
| Profile | small (pinned via `--size small`; auto-size not exercised) |
| Model x effort | claude-sonnet-5 x medium (constant across all cells) |
| Harness | claude |
| Gate images | `bats-eco-builder`, `satty-deb-builder`, `python:3.12` |

## Results: 4/4 PASS (independently re-verified)

| # | Cell | Target @ pinned SHA | Gate re-verification | Result |
|---|---|---|---|---|
| 1 | sh-refactor | bats-core @ `5a7db7a` | `bin/bats test` exit 0, **479/479 ok**; `shellcheck -x` exit 0 on all 3 changed scripts; `test/` diff empty | **PASS** |
| 2 | rust-package | Satty @ `2d18065` | `cargo deb --no-build` produced `satty_0.21.1-1_arm64.deb`; `dpkg-deb --contents` lists binary, `.desktop`, SVG icon, all 6 completions, man page | **PASS** |
| 3 | py-bugfix | sqlite-utils @ `79117b9` | full suite **1080 passed, 16 skipped**, exit 0; `tests/` diff empty | **PASS** |
| 4 | py-feature | sqlite-utils @ `79117b9` | full suite **1086 passed, 16 skipped**, exit 0 (includes the agent's 5 new tests) | **PASS** |

Container note (cell 1): the bats suite needs `TERM=xterm` in the image, else
unrelated `tput`/TERM tests fail identically before and after the change. The
gate sets it; with it the suite is fully green.

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

Net: at these two configurations the effort tier did not visibly cap sonnet at
medium below haiku at high on this set; sonnet's medium output was consistently
clean and, on cell 4, the best of the eight solutions.

## Observations

- **Resume-after-limit worked as designed.** Cell 4's agent hit a session limit
  after the init scaffold; resuming the same agent (not a duplicate) carried the
  intact work dir through explore, spec, build, and gate with a clean
  `init -> explore -> spec -> build` commit chain.
- **The gate remains the backstop the reviewer is not.** Cell 1's re-source
  hazard was invisible to a diff-only reviewer and only the full-suite gate
  caught it, reinforcing the framework's non-skippable-gate stance.
- **Medium scoping held.** Cells 2 and 3 stayed minimal; no policy gold-plating
  crept in where the tier did not call for it.
- **No framework defects surfaced.** All four gates green on independent
  re-verification; the scaffolder, skills, and phase flow drove each cell.

## Verdict

The framework at v5.9 HEAD passes the full fast-core set at claude-sonnet-5 x
medium, all four deterministic gates green on independent re-verification, all
four probes caught, and a clean resume across a session-limit reset. No framework
defects surfaced this round.
