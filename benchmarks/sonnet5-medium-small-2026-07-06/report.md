# Sonnet 5 x medium, small-profile only, framework vs. baseline — 2026-07-06

Requested round: re-run the fixed runbook's small-profile cells (1-4) against
their baseline (no-scaffold) twins, at `claude-sonnet-5` / medium effort, to
validate the framework still works correctly after the 2026-07-06 template
change (§21 CONCEPT.md: explore-freshness guard in `render_agents_md_small`,
pointer-genre clarification in the shared `notes.md` stub) and to compare
token economics. Full set: cells 1-4 (sh-refactor, rust-package, py-bugfix,
py-feature), each paired with its baseline twin — 8 runs total.

## Deviation from the runbook (disclosed)

The fixed runbook specifies strictly sequential dispatch ("Parallel dispatch
is prohibited — it burns the usage window ~5x faster and stalls cells
mid-run"). **This round dispatched all 8 cells in parallel** per explicit
user instruction, using the Task tool to spawn 8 independent sub-agents from
one orchestrator session rather than 8 standalone `claude` CLI invocations.
This worked without any stall or mid-run failure, but two mechanical
consequences follow, noted throughout:

1. **Transcript location differs.** `count_tokens.py` expects each cell's
   transcript under a work-dir-keyed `~/.claude/projects/<encoded-path>/`
   directory (true for a standalone CLI session cd'd into the work dir). Here
   all 8 sub-agent transcripts land as sibling files under the *orchestrator
   session's own* `subagents/agent-<id>.jsonl`. Token counts below were
   produced by isolating each agent's own file and pointing
   `count_tokens.py --projects-dir` at it — same dedup/summing logic, same
   output format, just a different lookup path than the tool's default.
2. **Reviewer sub-agent cost is a sibling file, not nested.** The framework
   arm's `reviewer` sub-agent (spawned by each cell's own agent) shows up as
   another flat sibling under the same `subagents/` directory
   (`spawnDepth: 2`), not inside the calling agent's transcript. Added in
   separately per the runbook's "reviewer cost stays in" rule.

## Configuration

| Field | Value |
|---|---|
| Model | claude-sonnet-5 |
| Effort | medium |
| Profile | small (cells 1-4 only) |
| Date | 2026-07-06 |
| Dispatch | parallel (8 concurrent sub-agents) — deviates from runbook default |
| Permission mode | full tool access per sub-agent (no interactive prompts either arm) |

## Results

| Pair | Arm | Gate | Output tokens | Total tokens | Cost (intro pricing) | Duration |
|---|---|---|---|---|---|---|
| 1 sh-refactor | framework | **PASS** | 14,394 | 8,463,596 | $2.42 | ~39 min |
| 1 sh-refactor | baseline | **PASS** | 3,458 | 1,681,474 | $0.52 | ~7 min |
| 2 rust-package | framework | **PASS** | 10,389 | 2,673,410 | $0.83 | ~6.5 min |
| 2 rust-package | baseline | **PASS** | 4,279 | 544,829 | $0.21 | ~2.2 min |
| 3 py-bugfix | framework | **PASS** | 9,026 | 2,815,954 | $0.82 | ~7 min |
| 3 py-bugfix | baseline | **PASS** | 5,406 | 779,679 | $0.27 | ~2.9 min |
| 4 py-feature | framework | **PASS** | 12,166 | 11,440,672 | $2.81 | ~16.5 min |
| 4 py-feature | baseline | **PASS** | 8,388 | 6,218,778 | $1.54 | ~9.4 min |

Cost uses Sonnet 5 introductory pricing active as of this run (input $2/MTok,
cache write 5m $2.50/MTok, cache read $0.20/MTok, output $10/MTok; reverts to
$3/$15 standard after 2026-08-31).

**8/8 gates PASS, both arms, all four cells.** No framework or baseline
failures this round.

### Framework overhead vs. baseline (one-shot, per pair)

| Pair | Framework total | Baseline total | Overhead |
|---|---|---|---|
| sh-refactor | 8,463,596 | 1,681,474 | **+403%** |
| rust-package | 2,673,410 | 544,829 | **+391%** |
| py-bugfix | 2,815,954 | 779,679 | **+261%** |
| py-feature | 11,440,672 | 6,218,778 | **+84%** |

Baseline won every one-shot pair on both cost and wall-clock, by a wide
margin on three of four. This is the runbook's own predicted shape (§13:
right-sizing — ceremony must not exceed the task; one-shot small cells favor
baseline), now reconfirmed at a new model/date with a full small-profile
matrix rather than the earlier haiku-high round's partial one. **This round
did not run the B-amortized two-task-same-repo sequence** (cells 3+4 chained
in one work dir), which is the specific design the runbook uses to test the
framework's actual thesis — amortized value on a *second* task in an already-
explored repo. Nothing here tests that thesis; it only reconfirms the
already-expected one-shot cost.

### Reliability / correctness signal (not gated, but observed)

Both arms handled every planted trap correctly this round — unlike the
2026-07-04 haiku-high round, where the baseline arm destroyed an uncommitted
seed via a `git checkout` reflex and confabulated a fix. At Sonnet 5 x medium:

- **Cell 1 wrong-premise probe** (the three `abort()` definitions are not
  actually identical): both arms caught it independently, recorded it as a
  numbered assumption, and converged on a similar generalized-function
  resolution rather than forcing an incorrect merge. The framework arm
  additionally hit and fixed a real regression mid-build (a later
  `tracing.bash` re-source silently clobbering the dedup) that the baseline
  arm's simpler edit didn't introduce in the first place — not evidence of
  which is "better," just a different code path to the same passing gate.
- **Cell 3 root cause** (two-hop `detect_fts` bracket/quote dispatch bug):
  both arms found the exact same one-line structural-inverse fix and both
  passed the cross-check test (`test_tracer.py`) that a naive symptom patch
  would have broken.
- **Cell 4 collision trap** (silent data loss via `transform(rename=)`):
  both arms found it and guarded against it, via two different but equally
  valid designs — framework arm went straight to `ALTER TABLE ... RENAME
  COLUMN` (sidestepping the collision class entirely); baseline arm
  delegated to `transform()` with an added `AlterError` guard.

At this model/effort, this round shows no reliability gap between arms — a
different result from the haiku-high round, consistent with the runbook's
own expectation that gaps narrow as model capability increases.

## Did this "prove" the 2026-07-06 template changes?

Partially, and it's worth being precise about what was and wasn't tested.

**What this round validates:** the small-profile templates render correctly
and produce a working scaffold end-to-end with the July 6 wording changes in
place — all four framework cells ran `/explore` -> `/spec` -> `/build` ->
review -> gate cleanly on the current `init_agent.py`, with no template
regression, no rendering error, no protocol confusion. This is a legitimate
functional regression check.

**What this round does NOT validate:** the specific incremental behavior the
§21 change targets — an agent noticing a stale/missing project-context digest
and self-correcting by running `/explore` before proceeding. Every framework
cell's dispatch prompt in this runbook hard-codes `/explore` as an
unconditional STEP 2 ("read `.claude/skills/explore/SKILL.md` and follow
it... Run `probe.py` first... Commit `.ai`"), so the new Protocol item 1
clause (check the digest, run `/explore` if it's still a stub) never had a
chance to be the deciding factor — `/explore` ran regardless of whether the
guidance was there. Proving that clause's actual effect needs a narrower,
different experiment: a session that is *not* told to run `/explore` (only
given a direct task, mirroring the real scenario found in this repo's own
history), comparing old vs. new Protocol wording on whether the agent
self-corrects. That is a smaller, targeted test — not this fixed four-cell
matrix — and remains open if it's wanted as a follow-up.

## Files

Raw per-cell results (config table, spec, `.ai` commit history, full diff,
full gate output, token usage) copied from `/tmp/benchmark/results/` into
`results/` alongside this report.
