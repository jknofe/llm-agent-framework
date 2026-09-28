# Sequence benchmark, Sonnet 5 x medium, framework 6.0 vs baseline, n=3 (2026-09-14)

First execution of `benchmarks/sequence-runbook.md`. Question: do the second
and third tasks on a repository benefit from the framework (spec-driven
workflow plus accumulated `.ai` knowledge) compared with a bare agent starting
cold each time? Three pinned tasks on sqlite-utils at `79117b9`, two arms,
three replications each, 21 sessions, all gated by the orchestrator in
`python:3.12` with hidden tests the agents never saw. Verdict rule fixed in the
runbook before the first run.

## Verdict

**Amortization failed: 0 of 3.** The framework's marginal cost for tasks 2
plus 3 was higher than the baseline's in every replication, by +74%, +160% and
+136% total tokens. The T2 to T3 trend inside the framework arm is flat to
slightly down (0%, -9%, -13%), the same shape as the baseline's without any
memory (-22%, -32%, +7%). Knowledge did not compound into cheaper later tasks.

**Correctness: framework worse on T1, equal on T2 and T3.** Baseline passed
all nine gates. The framework arm failed T1 in two of three replications with
the same narrow fix (changing `like2` instead of `like` in `detect_fts`), which
made the target test pass but left the tracer test red; both agents then
recorded the tracer failure as "pre-existing" in `.ai/notes.md`, and every
later session in those trees inherited that wrong belief. All twelve hidden
tests for T2 and T3 passed on both arms.

**Knowledge carry-over: measurable, but it cut both ways.** The cog check was
the designed signal. Baseline: 5 of 6 clean, the one miss being a cold T3
regenerating the reference doc with a drifted `tabulate` (rep 2). Framework:
3 of 6 clean; rep 1 carried the gotcha correctly through T2 and T3, rep 2
shipped the same churn the baseline did and then inherited it, rep 3 wrote the
gotcha down after T2 and its T3 followed the note by hand-inserting a block
that did not match cog's output. Notes were read in every framework task
session (1 to 8 reads of `notes.md`, 0 to 2 of `map.md`), so the memory was
used; it did not make the sessions cheaper or more correct here.

## Configuration

| Field | Value |
|---|---|
| Repo | github.com/simonw/sqlite-utils at `79117b9`, T1 bug state committed as seed |
| Model | claude-sonnet-5 (from transcript `model` field), effort medium via prompt text |
| Framework | 6.0 (working tree of this change), harness claude |
| Arms | F: scaffold + `/explore` (s0), then `/spec` + `/build` per task; B: no scaffold, cold session per task |
| Order run | F1, B1, B2, F2, F3, B3 |
| Gate | full pytest + hidden tests copied in after each session, `cog --check`, no test file changed for T1 |
| Dispatch | Task-tool sub-agents, one per session, sequential; transcripts isolated per agent plus reviewer child |

## Per-session results

See `results/ledger.md` for the full table (gate, COG exit, steps, output and
total tokens, duration, notes size, reads of notes/map/AGENTS.md). Raw
per-session files with spec, diff, gate output and token blocks are under
`results/`.

## Marginal cost, tasks 2 plus 3, per replication

| Rep | Arm | Steps | Output | Total | T2 total | T3 total | T3 vs T2 |
|---|---|---|---|---|---|---|---|
| 1 | F | 181 | 8,935 | 12,529,619 | 6,272,365 | 6,257,254 | -0% |
| 1 | B | 119 | 5,608 | 7,183,838 | 4,033,615 | 3,150,223 | -22% |
| 1 | F vs B | | | **+74%** | | | |
| 2 | F | 202 | 13,783 | 14,248,559 | 7,455,775 | 6,792,784 | -9% |
| 2 | B | 96 | 2,855 | 5,487,897 | 3,265,497 | 2,222,400 | -32% |
| 2 | F vs B | | | **+160%** | | | |
| 3 | F | 202 | 8,018 | 15,897,792 | 8,478,983 | 7,418,809 | -13% |
| 3 | B | 113 | 3,347 | 6,722,475 | 3,246,019 | 3,476,456 | +7% |
| 3 | F vs B | | | **+136%** | | | |

## Total sequence per replication

| Rep | F (s0+T1+T2+T3) | B (T1+T2+T3) | F vs B |
|---|---|---|---|
| 1 | 17,197,321 | 8,677,764 | +98% |
| 2 | 17,673,604 | 6,456,194 | +174% |
| 3 | 20,601,651 | 7,603,857 | +171% |

## Correctness and knowledge signals

| Arm | T1 gate PASS | T2/T3 hidden PASS | COG clean (T2, T3) |
|---|---|---|---|
| F | 1/3 | 6/6 | 3/6 |
| B | 3/3 | 6/6 | 5/6 |

## Where the framework's extra cost goes

Per session the framework arm makes 1.5 to 2 times the API calls of the
baseline at the same context size per call (about 60 to 80k). The extra calls
are the workflow: reading three skill files, writing and committing a spec,
the review sub-agent (37k to 140k tokens per session), the notes and map
updates, the probe re-run and drift check, the `.ai` commits. None of that
shrank from T2 to T3. Nothing in the tree got cheaper to discover either: on
this repo a cold agent finds `rename_table` and `add_column` by grep in a
handful of calls, so there was no discovery cost for memory to save.

## Observations

1. **The spec narrowed the T1 fix.** Both failing framework T1 sessions wrote
   an acceptance criterion of "the named test passes", fixed the second LIKE
   slot, saw the tracer test fail, and classified it as pre-existing because
   it also failed before their change (it did: the seed breaks both). The
   baseline agents had no criterion to satisfy, ran the whole suite, and fixed
   the slot that makes both green. The reviewer sub-agent, given only the
   diff and the criteria, confirmed the narrow fix each time. This is the
   review gate working as designed on a spec that was wrong.
2. **Wrong knowledge persists.** Once "test_tracer fails, pre-existing" was in
   `notes.md`, every later session in that tree repeated it in its report and
   never re-examined it. Memory carried the error as faithfully as it carried
   the cog gotcha.
3. **Uncommitted host diff accumulates.** The protocol never commits the host
   repo, so by T3 each tree carried T1 and T2 as uncommitted changes. The
   framework reviewer flagged them as scope creep in every T3 and the agent
   spent calls ruling them out; a baseline T3 (rep 3) discarded a prior
   session's doc edit with `git checkout` and had to reconstruct it. Both
   arms paid; commit the host tree between sessions in the next revision.
4. **Seed leak, both arms.** The upstream fix commit is reachable in the
   clone, and two baseline T1 sessions found it via `git log -p`. Present in
   every round since July; a shallow clone or an orphan seed commit would
   close it.
5. **Sandbox drift.** Sessions ran on the host Python, where `pip install`
   is refused; agents verified with whatever was importable, and one
   framework T1 reported the target test passing where the gate saw it fail.
   The gate decided every result; the agents' self-reports did not.

## Deviations from the runbook (disclosed)

- Sessions were Task-tool sub-agents, not separate `claude` processes, so
  the scaffolded Stop hook and permission allowlist did not fire for the
  framework arm (both arms had the same tool access).
- SEED and SCAFFOLD were run by the orchestrator; agents verified the SHA
  and stamp themselves.
- Gate rule for T2 and T3 after a failed T1 was set during the round, before
  any T2 gate on an affected tree was run, and applied to both arms: hidden
  tests pass and no failure beyond the set the previous session left.
- The cost per replication was not recorded in dollars; token totals are the
  cost measure.

## What this settles and what it does not

Settled, for this repo size and model: the amortization thesis in CONCEPT.md
sections 13 and 36 does not hold. Three of three replications, hidden-test
gated, the framework's later tasks cost more and were not more correct. This
is the third negative result (haiku 2026-07-04 at n=1, Sonnet 5 one-shot
2026-07-06, now Sonnet 5 sequence at n=3), and the first with a correctness
loss attributable to the framework's own artifacts.

Not settled: large repos where discovery is expensive (Experiment B in
`amortization-playbook.md`, never run on any model), and the C arm that would
show whether `.ai` on disk without the spec/build ceremony costs anything.
The knowledge signal here says memory is read and followed; the open question
is whether there is a repo where what it carries is worth more than the
ceremony that writes it.

## Files

`results/`: 21 session files with configuration, spec (F arm), `.ai` history,
full diff, gate output, token block; nine baseline notes files; `ledger.md`.
Tools used: `benchmarks/tools/seq_gate.sh`, `seq_measure.py`, `seq_derive.py`.
Work dirs under `/tmp/benchmark/runs/seq-*-2026-09-14/` are ephemeral.
