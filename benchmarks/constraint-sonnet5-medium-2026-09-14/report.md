# Constraint Benchmark, Sonnet 5 x medium, 2026-09-14 (n=3)

First run of `benchmarks/constraint-runbook.md`. Three tasks on sqlite-utils,
framework arm (scaffold, `/explore` answered by a human, then each task solved
directly) against a baseline arm (no scaffold, cold session per task), three
replications each, 21 sessions, every session gated by the orchestrator.

**Result: the round does not support the control thesis, and it cannot. The
design has a confound that the run exposed: task N's output becomes task N+1's
local precedent, so by T3 both arms were copying code rather than remembering
a rule.** Details under "Why this round cannot decide".

## Deviations from the runbook (disclosed)

1. **Parallel dispatch across replications.** The runbook prohibits parallel
   agent dispatch. On the user's instruction the six replications ran
   concurrently in four waves (3 explores, then 6 x T1, 6 x T2, 6 x T3), with
   a gate between waves. Sessions *within* a replication stayed strictly
   sequential, which is not a convention but a data dependency: s2 works on
   what s1 left behind and each session must be memoryless. Consequence:
   durations are contended and unreliable, and are not used in any conclusion.
   Token counts and gate results are unaffected.
2. **The F arm ran the direct path, not `/spec` and `/build`.** Decided and
   written into the runbook before any task session ran. `/spec` would have
   written the rule into the spec file and `/build` would have read it back,
   so the rule would have survived through the spec rather than through the
   always-loaded requirements block, measuring the wrong carrier.
3. **Dispatch as Task-tool sub-agents**, as in the two 2026-09-14 rounds
   before this one. SEED and SCAFFOLD by the orchestrator; effort encoded in
   the prompt.
4. **Two SEED corrections from section 37's protocol findings**, both applied:
   the seed leak is closed (`.git` deleted after the revert, single orphan
   seed commit, so no agent can read the upstream fix), and every task session
   was given the Docker one-liner for the suite so self-verification matches
   the gate. Host trees were committed between waves.

## Pre-run controls

All four passed and are recorded in the runbook. The constraint inverts the
repo's own convention: `db.py` drops columns via `self.transform(drop=...)` at
lines 3130 and 3180, and the rule forbids exactly that for new public methods.
The constraint test fails 2 of 3 against a `transform()` implementation and
passes 3 of 3 against an `ALTER TABLE` one.

**Seed state, verified before dispatch:** the revert leaves two tests failing,
not one, and the upstream fix turns both green (1080 passed). The second
failure is the trap that caught two framework sessions in the section 37
round.

## Results

### Gates

| Task | F arm | B arm |
|---|---|---|
| T1 (bugfix, suite green, no `tests/` change) | 3/3 PASS | 3/3 PASS |
| T2 (suite + hidden rename tests) | 3/3 PASS | 3/3 PASS |
| T3 (suite + hidden drop tests) | 3/3 PASS | 3/3 PASS |

18 of 18 task sessions passed their gate. `cog --check` exit 0 everywhere.

### The constraint

| | T2 | T3 | Total |
|---|---|---|---|
| F (framework) | 3/3 | 3/3 | **6/6** |
| B (baseline) | 3/3 | 2/3 | **5/6** |

Only `con-B2` violated the rule, at T3, with
`self.transform(drop=(column,))`.

### Cost

| | T2+T3 marginal | Full sequence |
|---|---|---|
| F | 13,177,166 | 16,644,560 (incl. explore) |
| B | 12,746,410 | 14,322,768 |

The framework arm is 3.4% more expensive on the marginal pair and 16.2% more
expensive over the sequence. Consistent with every prior round in direction,
and much smaller in size than the section 37 result (+74% to +160%), because
this round's F arm runs the direct path rather than the spec chain.

## Verdict

The rule fixed before the run: F at least 7 of 9 and B at most 3 of 9 supports
the thesis; F and B within 2 of each other fails it. Two corrections to that
rule as written: the denominator is 6 per arm, not 9 (3 replications x 2
constrained tasks), which was an arithmetic slip in the runbook; and the
threshold was set on the assumption that the baseline would rarely honor the
rule by accident.

Applied as written: F 6/6, B 5/6, a gap of 1. **The control thesis is not
supported by this round.**

## Why this round cannot decide

The null is uninformative, for a reason the transcripts make explicit.

**T2 never discriminated.** The task says "mirroring the existing
`rename-table` pattern", and `rename_table()` uses
`ALTER TABLE ... RENAME TO`. The constrained path was also the obvious path.
Both baselines that explained their choice gave an engineering reason, not a
remembered rule: `con-B3` wrote that `ALTER TABLE` is "simpler than the
heavier `transform(rename=...)` full-rebuild path".

**T3 was contaminated by T2.** Once T2 landed `rename_column` using
`ALTER TABLE` in the repository, that method became the local precedent for
T3, and the baselines mirrored it. `con-B3` said so directly: T2's
`rename_column` "established a pre-validate-then-`AlterError` convention that
structurally matches this task's requirement better than the nominal mirror
target `add_column`". `con-B1` reasoned the same way. The carrier that kept
the rule alive in the baseline arm was **the code**, not memory of the rule.

This is a real mechanism and it competes with the framework's: a rule written
into the codebase propagates itself. But it means this benchmark measured
precedent-following, not knowledge retention, from T3 onward.

**What the F arm's transcripts show.** All three framework sessions cited the
AGENTS.md line explicitly at both T2 and T3. `con-F2` at T2: the rule was
"directly load-bearing... without it I'd likely have reached for the existing
`transform(rename=...)` machinery". `con-F3` at T3 grepped for the repo's
`transform(drop=...)` uses and deliberately left them alone, because the rule
scopes to new public methods. The mechanism worked; the round just cannot
prove it made the difference, because the baseline had another way to arrive
at the same place.

**The one informative session.** `con-B2` at T3 is the only case where the
counter-pull won. It chose `transform()` with the better engineering argument:
it "works regardless of SQLite's native DROP COLUMN support and correctly
preserves indexes/foreign keys/NOT NULL/defaults". That is a defensible
decision that the stated rule overrides, and the three framework sessions
facing the same choice overrode it. One session is not evidence; it is the
shape the evidence would take.

## What a deciding round needs

1. **A constraint T2 cannot seed.** Either put the rule on something only T3
   touches, or give T2 and T3 unrelated rules so neither becomes the other's
   precedent.
2. **A constrained path that is not also the natural path.** The rule must
   cost the agent something, or compliance is free and meaningless. B2's
   argument shows the drop case has that property; the rename case does not.
3. **Prevent precedent transfer.** Reset the repository between tasks, or
   pick tasks in unrelated modules.
4. **Keep everything else**: the seed fix, the executable suite, the
   host-tree commits, the traced-SQL constraint test. Those worked.

## What this round did establish

- **The section 37 T1 failure did not reproduce.** 6 of 6 sessions fixed
  `detect_fts` correctly and kept the whole suite green. Four of six first
  tried the wrong `like`/`like2` assignment, were caught by the tracer test,
  and corrected. Nobody filed the second red test as pre-existing. The likely
  cause of the difference is the executable test suite this round handed every
  session, which the section 37 round did not have.
- **`/explore` with a human answering puts a stated rule where it belongs.**
  3 of 3 wrote it verbatim into the AGENTS.md requirements block, including
  the clause that contradicts the repo, and left `notes.md` as the stub. That
  path had never been exercised before; section 37 listed it as untested.
- **Framework sessions used the recorded commands.** All three ran
  `cog --check`, which appears only in AGENTS.md and in no task text.
- **The notes carried within a replication.** `con-F1` at T3 used its own T2
  notes entry as the template rather than re-deriving from `add_column`.
- **The framework's cost premium on the direct path is small**: 3.4%
  marginal, 16.2% over the sequence, against 74% to 160% for the spec chain
  in section 37. That number is worth more than the constraint count here.
