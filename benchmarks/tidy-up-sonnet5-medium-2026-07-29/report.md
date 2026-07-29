# /tidy-up round, sonnet-5 medium, 2026-07-29

First round for the `/tidy-up` skill (framework v5.16). Two scoped sweeps
against the fixed-runbook cell 2 target, run one at a time.

## Setup

| Field | Value |
|---|---|
| Framework | v5.16, small profile, claude harness |
| Target | Satty, `2d18065ea534bd12792865784eed86a617ffbdc7` (v0.21.1), runbook cell 2 |
| Model | sonnet-5, effort medium |
| Scaffold | `--name satty --size small --harness claude -y` |
| Invocation | read `.claude/skills/tidy-up/SKILL.md` in full, follow it for the given scope |

Two independent copies of the scaffolded repo, one per sweep, so neither run
sees the other's diff.

**Deviation from the skill, operator-imposed:** the step 0 build/test/lint
baseline was waived. Satty cannot link here (`gtk4-layer-shell` is absent), and
the run was specified as change-only with no build. Both agents were told to
record the waiver, and both did. This means step 5's compare-against-baseline
was exercised only in its non-linking form, and the gate that makes the skill
safe in normal use is the one part this round did not test. That is the main
caveat on these results.

## Cells

### VC1, scope `src/tools`

| | |
|---|---|
| Verdict | PASS |
| Tokens | 147410 |
| Tool calls | 57 |
| Wall clock | 8m38s |
| Diff | 6 files, +10/-38 |

- **Pass 1 (dead code):** 3 removals, all commented-out code, each with a
  stated reason: a superseded `Tools::Crop` registration line
  (`tools/mod.rs`), a dead `canvas.delete_image` call (`tools/blur.rs`), a
  stray duplicate of the live line above it (`tools/text.rs`). No live code
  touched. Declined to declare anything else dead without a compiler, which is
  the behavior the pass asks for when evidence is ambiguous.
- **Pass 2 (obsolete files):** empty table, all 12 files live. Correct: there
  was nothing to find, and it did not invent candidates.
- **Pass 3 (comments):** 9 blocks shortened across `arrow.rs`, `crop.rs`,
  `highlight.rs`. The information the code cannot carry survived the
  compression: 15-degree snap steps, the diamond/sharp head trade-off, the
  CTRL-toggles-highlighter-mode rule. Two comments that only restated their
  match arms were deleted outright, which is right.
- **Pass 3 judgment call:** kept the 29-line ASCII arrow-geometry diagram in
  `arrow.rs` at full length and said so, rather than silently skipping it.
  This is the "never delete knowledge to satisfy a line count" rule working.
- **Pass 4 (em dashes):** 0 in scope, reported as 0.

### VC2, scope `src/ui`, `src/configuration.rs`, `README.md`, `.github/`

| | |
|---|---|
| Verdict | PASS |
| Tokens | 118770 |
| Tool calls | 67 |
| Wall clock | 9m50s |
| Diff | 3 files, +9/-15 |

- **Pass 1 (dead code):** nothing removed. Every getter, helper, and enum
  variant in `configuration.rs` and `ui/toolbars.rs` traced to a live call
  site. A sweep that correctly removes nothing is the harder result to get and
  the more important one to see.
- **Pass 2 (obsolete files):** empty table, no candidate met the three-part
  evidence bar.
- **Pass 3 (comments):** 4 blocks in `README.md` and `.github/dependabot.yml`
  compressed to 1-2 lines. Every version marker (`0.20.0`, `0.20.1`,
  `0.21.0`), URL, and caveat preserved.
- **Pass 4 (em dashes):** 2 found, 2 rewritten, 0 left. Both rewritten by
  clause rather than swapped character for character: one to a comma
  (`even better, but no pressure`), one to a colon (`<kbd>0</kbd>: select nth
  color`). The markdown hard-linebreak trailing spaces in `feature.yml`
  survived, which a naive substitution would have eaten.

## What the round establishes

- The four passes run in order and produce the intended shape of diff on a
  real codebase in an ecosystem the skill never names.
- The authority split holds. Both runs removed code and rewrote prose; neither
  deleted a file, and both produced the proposal table instead (empty, in both
  cases, because there was nothing to propose).
- Commit discipline holds. Both left the host repo uncommitted. VC2 committed
  `.ai` as `tidy-up: <scope>`; VC1 found nothing durable to record and
  committed nothing rather than fabricating a commit.
- Behavior preservation held in both diffs on inspection: only comments,
  commented-out code, and documentation prose changed.

## What it does not establish

- The step 0 / step 5 baseline gate, waived here. A round on a target that
  actually builds is the obvious next cell.
- The large profile's KB reconciliation (nodes whose `covers` globs match a
  removed path). Small profile only, so that path was never taken.
- The copilot harness rendering, covered by the Layer 1 checks but not by an
  agent run.
