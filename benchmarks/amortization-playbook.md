# Amortization Playbook (withdrawn, kept as record)

**Status: superseded by CONCEPT.md section 38 (2026-09-14). Do not execute.**

The amortization thesis this file was written to test is retired. The chain
it rested on was: a warm-started session beats a cold one because cold
discovery is expensive, and discovery is expensive in large repos. Section 36
measured the discovery half directly (ETH Zurich evaluation of context files)
and found agents with a context file reach the first task-relevant file no
faster than agents without, on SWE-bench Lite (django, sympy, scikit-learn
among them) and on AGENTbench's 12 niche repos. Both ends of the size range,
same null. A bigger repo is therefore not where the thesis lives, and a
fourth negative round would have bought little.

What happened to the two experiments this file planned:

- **Experiment A** (small-repo sqlite-utils, Sonnet 5) was answered by
  `benchmarks/seq-sonnet5-medium-2026-09-14/`, which ran the same shape with
  three replications and hidden gate tests: marginal cost of tasks 2 plus 3
  was +74%, +160% and +136% over baseline, and amortization failed 0 of 3
  under the rule fixed before the run. Its design is kept below as the record
  of how the question was framed.
- **Experiment B** (large-repo navigation2, never run on any model) was
  removed from this file on 2026-09-14 along with this header. Its pinned
  procedure, including the verified `nav2_rotation_shim_controller` task and
  the colcon gate, is in git history at the commit before this one. It also
  no longer runs as written: its scaffold command passes `--size large`, a
  flag removed with the large profile in framework 5.22.

The successor question is not amortization but control: does carrying
constraints that the repository cannot state itself change the outcome. The
round that tests it is described in CONCEPT.md section 38 under "Next
measurement", and it reuses the sequence runbook's seed and gate rather than
anything in this file.

The rest of this file is history. Nothing below is a live instruction.

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


---

## What "worth it" means for the original question

Neither experiment answered "would 4-5 changes make the overhead worthwhile"
by itself. Each gives exactly one marginal-cost data point (task 2 vs. task
1), the same shape as the existing haiku measurement. Extrapolating from a
single marginal delta to N=4-5 used the model laid out at the time:

```
Total_framework(N) = Cost(session with explore) + (N-1) x Marginal_framework
Total_baseline(N)  = N x Marginal_baseline
```

If `Marginal_framework < Marginal_baseline`, the relative overhead shrinks as
N grows and crosses over at some N. If `Marginal_framework >=
Marginal_baseline`, the relative overhead holds flat or widens with N, and
more changes does not help regardless of how many are assumed. The haiku
round, and then the 2026-09-14 sequence round at Sonnet 5, both landed in the
second case. That is what closed the question.

## Status

Withdrawn 2026-09-14, never executed as written. Experiment A's question was
answered by the sequence round; Experiment B was removed. Any leftover
research clone under `/tmp/nav2-inspect/` from verifying the removed task can
be deleted.
