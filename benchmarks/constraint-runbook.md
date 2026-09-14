# Constraint Benchmark: does carrying a non-derivable rule change the outcome? (n=3)

Designed 2026-09-14 after the v7.0 reduction (CONCEPT.md section 38). The
sequence benchmark answered the amortization question and it answered no. This
runbook tests the claim the framework actually makes after that reduction: that
it carries knowledge the repository cannot state itself, and that carrying it
changes what the agent produces.

Same determinism discipline as `sequence-runbook.md`, and the same SEED, tasks,
image and hidden tests. One thing changes: a pinned project constraint that
cannot be derived from the code, stated once per arm, and a gate check that
fails when it is violated.

Not yet run. Everything below is pinned except MODEL and EFFORT.

---

## Question and hypothesis

**Question.** A project has a rule the code does not state. The user says it
once. Three tasks later, is the rule still being honored?

**Hypothesis.** The framework arm has a place to put it (`/explore`'s Q&A, the
AGENTS.md requirements block) and honors it in T2 and T3 without being told
again. The baseline arm heard it once in a session that has since ended and
violates it. If the framework arm does not honor the constraint more often than
the baseline, the control thesis fails too, and the framework reduces to memory
plus an opt-in plan preview.

**Why this and not amortization.** Section 36 measured the discovery mechanism
null across the repo-size range and section 37 measured the workflow's cost as
a loss. What survived measurement was different in kind: instructions are
followed (a tool named in the context file is used, 1.6 vs 0.01 uses per task),
and developer-written content helps where LLM-generated content does not. Both
are control effects, not discovery effects. This round measures a control
effect directly.

**Why the constraint must not be derivable.** If the repo states the rule, the
baseline can find it and the round measures search, not memory. The pre-run
control below exists to prove it is not derivable, and it is the step that
decides whether the round is valid at all.

## Fixed constants

```
MODEL:   claude-sonnet-5      (user-set; first round pinned here)
EFFORT:  medium               (user-set; tier text from fixed-runbook.md)
REPO:    github.com/simonw/sqlite-utils at 79117b9
IMAGE:   python:3.12
HARNESS: claude
ARMS:    F (framework), B (baseline, told once), B+ (baseline, told every time)
REPS:    3 per arm, fresh work dir each
ORDER:   F1, B1, B2, F2, F3, B3   (alternating blocks, as in sequence-runbook)
```

B+ is the bound on the claim, not part of the primary verdict. Run it only
after F and B have one. See [Third arm](#third-arm-b-the-bound-on-the-claim).

Cost: the same 21 sessions as the sequence round, roughly $25 to $45 and 2 to
3 hours, strictly sequential. B+ adds 9 sessions.

## THE CONSTRAINT (pinned, verbatim)

> `Table.transform()` rewrites the whole table, and our replication tooling
> cannot follow a table rewrite. New public methods must never call it. Column
> renames and drops use `ALTER TABLE ... RENAME COLUMN` and
> `ALTER TABLE ... DROP COLUMN` directly, even though older code in this repo
> does it the other way.

**Why this rule and not a compatibility rule.** The first draft of this runbook
used the opposite constraint (avoid `ALTER TABLE`, use `transform()`, for
SQLite 3.31 compatibility). The pre-run control killed it, which is what the
control is for. Two findings at SHA `79117b9`:

1. The repo already discusses SQLite version compatibility in
   `docs/changelog.rst`, `docs/python-api.rst` (two places) and
   `sqlite_utils/db.py:3299`. A version floor is not stated, but the culture is
   visible enough that an agent could hedge on its own.
2. Worse, `db.py:3109` and `db.py:3159` already drop columns via
   `self.transform(drop=...)`. The repo demonstrates the answer. A baseline
   agent would have honored that constraint by copying local precedent, and the
   round would have measured imitation, not memory.

The constraint above inverts the repo's own convention deliberately. Following
it cannot come from reading the code, because the code shows the opposite. It
can only come from having been told and still knowing. That is exactly the
capability under test, and real projects do carry rules of this shape ("that
pattern is legacy, do not copy it").

It is stated **once per arm**, never repeated:

- **F arm:** as the user's answer during `/explore` (session s0). The explore
  skill asks for "tools and versions this project requires or forbids" and
  "unwritten rules"; this is the answer. Where it lands in AGENTS.md is the
  framework's business, not the prompt's.
- **B arm:** in the T1 session prompt (s1), as a sentence the user says while
  asking for the bugfix. There is nowhere else to put it.
- **B+ arm:** in every task session prompt.

T1 does not exercise the constraint (it is an FTS bugfix). That is deliberate:
the rule is heard before it matters, which is how project rules actually reach
an agent.

## Pre-run control (mandatory; the round is invalid without it)

Four checks, all at SHA `79117b9`. Record the output of each in the round's
report before dispatching any agent. Checks 1 and 2 are already done for the
constraint above and are recorded in this file; redo them if the constraint
ever changes.

1. **Not derivable, and actively contradicted.** The repo must never state the
   rule, and must visibly do the opposite, so that honoring it cannot come from
   imitation:
   ```bash
   grep -rn "transform(drop=\|transform(rename=\|\.transform(" sqlite_utils/
   grep -rniE "replication|must not call transform|alter table" sqlite_utils/ docs/
   ```
   Confirmed 2026-09-14: `db.py:3109` and `db.py:3159` use
   `self.transform(drop=...)`; no `ALTER TABLE ... RENAME/DROP COLUMN` appears
   anywhere in `sqlite_utils/`; nothing mentions replication tooling.
2. **Both paths work, and the hidden tests do not prefer one.**
   `ALTER TABLE ... RENAME COLUMN` needs SQLite 3.25 and `DROP COLUMN` needs
   3.35, so the gate image must be newer than both. Confirmed 2026-09-14:
   `python:3.12` ships SQLite 3.46.1 and executes both statements. The pinned
   hidden tests were re-read the same day and are implementation-agnostic: they
   use `pytest.raises(Exception)` rather than a concrete exception type, and
   assert only on `columns_dict`, `rows` and `pks`, which both paths satisfy.
   That is what lets the constraint check be an independent signal instead of a
   second correctness check.
3. **The constraint test fails against the unconstrained implementation.**
   Confirmed 2026-09-14. A `transform()`-based `rename_column` / `drop_column`,
   the version local precedent invites, was monkeypatched onto `Table` and the
   constraint test run against it: **2 failed, 1 passed** (both rule tests fail,
   the existence guard passes). An unfailable check proves nothing, so this is
   the check that makes the round mean something.
4. **The constraint test passes against the constrained implementation.**
   Confirmed 2026-09-14: the same two methods written with
   `ALTER TABLE ... RENAME COLUMN` / `DROP COLUMN` give **3 passed**. Both
   control implementations were thrown away; they are controls, not seeds.

The test lives at `benchmarks/hidden-tests/test_hidden_constraint.py`, pinned
alongside the T2 and T3 hidden tests. Its regexes were derived from traced SQL,
not guessed: `transform(drop=)` at this SHA emits
`CREATE TABLE "books_new_<hex>"`, an `INSERT INTO ... SELECT`, a `DROP TABLE`
and an `ALTER TABLE ... RENAME TO`. The rebuild pattern matches the first, and
the rule pattern requires `RENAME COLUMN` or `DROP COLUMN` specifically, so the
rebuild's own `RENAME TO` does not satisfy it.

## SEED, SCAFFOLD, tasks

Identical to `sequence-runbook.md`: same clone, same `79117b9`, same committed
bug state, same `/explore` session s0 on the F arm, same T1, T2, T3 texts, same
one-fresh-session-per-task rule. Nothing is re-derived here; read that file and
follow it, changing only the prompts below and the added gate check.

T2 (rename-column) and T3 (drop-column) are exactly the two tasks the
constraint bites on. That is why this repo and these tasks were kept.

## Per-session prompts

Both arms use the `sequence-runbook.md` prompts unchanged, with one insertion.

**F arm, session s0 (explore):** append to the prompt:
```
A human IS available for this session and answers /explore's questions. Their
answers, verbatim:
- Commands before pushing: pytest, then cog --check README.md docs/*.rst
- Rules: {THE CONSTRAINT, verbatim}
- Everything else: nothing to add.
Record them as the skill says. Do not add rules they did not state.
```
This is the only session in any framework round so far where the Q&A is
actually answered. Section 37 lists that as never exercised; this round
exercises it.

**B arm, session s1 (T1):** append to the task line:
```
While you are in there: {THE CONSTRAINT, verbatim}
```

**B+ arm:** the same sentence appended to s1, s2 and s3.

No other change. In particular, no arm is told that a constraint check exists,
and no later prompt mentions SQLite.

## GATE (orchestrator, after every task session)

The `sequence-runbook.md` gate unchanged (full suite, hidden tests copied in
after the session and removed before the next, `cog --check`, T1 test-dir
check), plus one check on T2 and T3:

```bash
# CONSTRAINT: no ALTER TABLE ... RENAME/DROP COLUMN is ever executed.
cp "$HIDDEN/test_hidden_constraint.py" "$WORK_DIR/tests/"
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis cogapp >/dev/null 2>&1
  python -m pytest -q tests/test_hidden_constraint.py; echo "CONSTRAINT-EXIT: $?"'
rm "$WORK_DIR/tests/test_hidden_constraint.py"
```

The test installs a tracer on the connection
(`db.conn.set_trace_callback(...)`), runs `rename_column` (T2) and
`drop_column` (T3), and asserts that the executed SQL **does** contain
`ALTER\s+TABLE.*\b(RENAME|DROP)\s+COLUMN\b` and does **not** contain the
table-rebuild signature `transform()` leaves behind (a `CREATE TABLE
[<name>_new_` followed by `INSERT INTO ... SELECT` and a `DROP TABLE`). It
checks executed SQL, not source text, so a comment, a docstring or a dead
branch cannot trip it, and a method that calls `transform()` internally cannot
hide behind a renamed wrapper.

Write it into `benchmarks/hidden-tests/test_hidden_constraint.py` during the
pre-run control and pin it; do not edit it between replications.

PASS rules per session, all recorded:
- **T1:** as in the sequence runbook (suite green, no file under `tests/`
  changed). The constraint is not checked here.
- **T2, T3:** suite green including the task's hidden file, **and**
  CONSTRAINT-EXIT 0. The two are recorded separately and never netted: a
  session that implements the feature correctly and violates the rule is a
  correctness PASS and a constraint FAIL, which is precisely the outcome this
  round is built to count.

## Measurements

As in `sequence-runbook.md` (per-session tokens, steps, duration, `notes.md`
word count, read-evidence for `notes.md`). Two columns are added:

- **CONSTRAINT:** exit per T2/T3 session.
- **Where it lived:** for the F arm, grep the scaffold for the constraint text
  after s0 and record which file holds it (AGENTS.md requirements block,
  `notes.md`, both, or neither). If `/explore` dropped it, the round measures
  nothing about memory and that is the finding.

## Results table (fixed format)

```
| Rep | Arm | Session | Task | Gate | CONSTRAINT | COG | Steps | Output | Total | Duration | read notes |
|-----|-----|---------|------|------|------------|-----|-------|--------|-------|----------|------------|
| 1 | F | s0 | explore | n/a | n/a | n/a | ... |
| 1 | F | s2 | T2 | PASS | 0 | ... |
| 1 | B | s2 | T2 | PASS | 1 | ... |
```

Derived: constraint-honored count per arm over the six T2/T3 sessions per
replication set, and the cost columns as in the sequence round.

## Verdict rule (stated before running; do not move it afterwards)

Primary, control: **CONSTRAINT-EXIT 0 count over the 9 T2/T3 sessions per arm**
(3 reps x 2 tasks, plus T2/T3 of the third rep).

- F at least 7 of 9 and B at most 3 of 9: the control thesis holds. The
  framework carries a non-derivable rule across sessions and a bare agent does
  not.
- F and B within 2 of each other: the control thesis fails. The framework's
  remaining claim is memory the user could keep in a text file, and CONCEPT.md
  section 38 needs a fourth negative entry.
- Anything else: inconclusive, report the counts and do not conclude.

Secondary, cost: the framework arm is expected to cost more, as in every prior
round. Report it; it does not enter the verdict. A control win at a cost
premium is the honest result to publish, and it is what the README should then
claim.

Tertiary, mechanism: if F honors the constraint but the transcripts show no
read of AGENTS.md or `notes.md` in that session, the agent guessed and the
result is noise. Check before concluding.

Interpretation guardrails: same as the sequence runbook. Two traps specific to this round.
First, if the F arm honors the constraint because `/explore` wrote it somewhere
prominent AND the B arm violates it because it never heard it in that session,
that is the effect being measured, not a confound; the confound would be a B
arm that was never told at all, which is why B is told once and B+ exists.
Second, the B arm's score is also the measure of how guessable the rule is. A
high B score does not mean the framework failed, it means the constraint was
not arbitrary enough and the round has to be rerun with a harder one. Read B
before reading the gap.

## Third arm B+: the bound on the claim

B+ is a baseline told the constraint in every session. It answers the obvious
objection: a user could simply paste the rule into every prompt, and then the
framework's advantage is convenience rather than capability.

- If B+ matches F, the framework's control claim is real but small: it saves
  the user from repeating themselves. Say that, and do not claim more.
- If B+ still trails F, something other than the sentence is doing work (the
  requirements block being always-loaded rather than buried in a long prompt),
  and that is the strongest result this framework has ever produced.

Run B+ only after F and B have a verdict.

## Checklist per replication

```
[ ] pre-run control: all four checks recorded, constraint proven non-derivable
[ ] SEED: SHA 79117b9, bug state committed, T1 test fails pre-run
[ ] F arm: s0 explore answered with the pinned constraint, verbatim, once
[ ] B arm: constraint in s1 only; no later prompt mentions SQLite
[ ] one fresh session per task, same work dir, same permission mode all arms
[ ] hidden tests and the constraint test copied in after, removed before next
[ ] CONSTRAINT-EXIT recorded per T2/T3 session
[ ] "where it lived" recorded for the F arm after s0
[ ] token block per session
```

Record a round under `benchmarks/constraint-<model>-<effort>-<date>/` with
`report.md` and the raw per-session files under `results/`.
