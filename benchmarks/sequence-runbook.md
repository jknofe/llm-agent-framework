# Sequence Benchmark: do later tasks benefit from the framework? (n=3)

Designed 2026-09-14 after the framework 6.0 verification round. The one-shot
cells in `fixed-runbook.md` cannot answer the question the framework exists
for: whether a spec-driven workflow plus accumulated project knowledge makes
the **second and third task on the same repository** cheaper or more correct
than a bare agent starting cold each time. The only prior measurement
(`haiku-high-2026-07-04/baseline-comparison.md`, B-amortized) was n=1, two
tasks, haiku. This runbook fixes three tasks, two arms, three replications,
hidden gate tests, and a verdict rule stated before any run.

Same determinism discipline as `fixed-runbook.md`: everything is pinned except
MODEL and EFFORT. Default for the first round: `claude-sonnet-5` x `medium`.

---

## Question and hypothesis

**Question.** For tasks T2 and T3 on a repo where T1 has already been done in
the same work dir, does the framework arm (scaffold, `/explore`, then `/spec`
and `/build` per task, `.ai` persisting between sessions) cost less or pass
more than a baseline arm (no scaffold, fresh cold session per task)?

**Hypothesis (the framework's own, CONCEPT.md section 13 and 36).** T1 costs
more on the framework arm (explore plus ceremony). T2 and T3 cost less or
pass more, because the requirements block, `.ai/notes.md` and
`.ai/notes/map.md` carry what T1 learned. If T2 and T3 are not cheaper and
not more correct, the amortization thesis fails on this repo size.

**Why three tasks, not two.** Two tasks give one marginal data point. Three
give a direction: if the framework's marginal cost falls from T2 to T3 while
the baseline's stays flat, knowledge is compounding; if both are flat, it is
not.

**Why n=3.** Agentic runs at n=1 have 30 to 40% variance on tokens (runbook
guardrail). Three independent replications per arm let the verdict rest on
consistency of direction across pairs rather than on one delta.

## Fixed constants

```
MODEL:   claude-sonnet-5      (user-set; first round pinned here)
EFFORT:  medium               (user-set; tier text from fixed-runbook.md)
REPO:    github.com/simonw/sqlite-utils at 79117b9
IMAGE:   python:3.12
HARNESS: claude
ARMS:    F (framework, current generator), B (baseline, no scaffold)
REPS:    3 per arm, fresh work dir each: F1 F2 F3, B1 B2 B3
ORDER:   F1, B1, B2, F2, F3, B3   (alternating blocks so date drift lands on both arms)
```

`FRAMEWORK=/path/to/llm-agent-framework/init_agent.py`,
`TOKENS=/path/to/llm-agent-framework/benchmarks/tools/count_tokens.py`,
`HIDDEN=/path/to/llm-agent-framework/benchmarks/hidden-tests`.

Cost estimate from the 2026-07-06 round at Sonnet 5 introductory pricing:
framework cells $0.8 to $2.8, baseline $0.3 to $1.5. Eighteen task sessions
plus three explore sessions: roughly $25 to $45 and 2 to 3 hours, strictly
sequential.

## SEED (identical for both arms, once per replication)

```bash
RUN_ID=seq-<arm><rep>-<date>            # e.g. seq-F1-2026-09-20
WORK_DIR=/tmp/benchmark/runs/$RUN_ID/sqlite-utils
git clone https://github.com/simonw/sqlite-utils.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 79117b9
# T1 bug state: reverse-apply only the db.py hunk of fix 1a28416, then COMMIT
# it (an uncommitted seed was destroyed by a baseline agent's git checkout on
# 2026-07-04; committing the bug state closed that hole).
git -C "$WORK_DIR" diff 1a28416~1 1a28416 -- sqlite_utils/db.py | git -C "$WORK_DIR" apply -R
git -C "$WORK_DIR" -c user.name=seed -c user.email=seed@bench commit -am "seed: benchmark bug state"
```
Verified state: `tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table`
fails, 46 pass.

## SCAFFOLD (F arm only, once per replication, its own session)

```bash
cd "$WORK_DIR" && python3 "$FRAMEWORK" --name sqlite-utils \
  --description "CLI tool and Python library for manipulating SQLite databases" \
  --harness claude -y
```
Then session 0: `/explore` per the scaffolded skill, commit `.ai`. This session
is counted and reported as `s0`; it is charged to the framework arm's T1 in the
total-sequence comparison and shown separately in the marginal one.

## Tasks (verbatim, pinned; each in a fresh session, same work dir)

**T1 (bugfix, existing gate):** "The test
`tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table`
fails. Find the root cause and fix it."

**T2 (feature, hidden gate):** "Add a `rename-column` CLI command and a
`Table.rename_column(old, new)` API method, mirroring the existing
`rename-table` command / `rename_table()` pattern. Renaming onto an existing
column name must raise and leave the table unchanged. Include tests and doc
updates."

**T3 (feature, hidden gate):** "Add a `drop-column` CLI command and a
`Table.drop_column(name)` API method, mirroring the existing `add-column`
command / `add_column()` pattern. Dropping a column that does not exist must
raise and leave the table unchanged. Include tests and doc updates."

T2 and T3 touch the same four places (`sqlite_utils/db.py`,
`sqlite_utils/cli.py`, `docs/python-api.rst`, `docs/cli.rst`) and the same
trap: `docs/cli-reference.rst` is generated by `cog`, and CI runs
`cog --check`. An agent that learned this in T2 and wrote it down should not
rediscover it in T3. That is the knowledge signal this benchmark measures
directly (see GATE).

## Per-session prompts

**F arm, task session (T1, T2, T3):**
```
You are benchmark agent {RUN_ID} session {N} (framework arm).
Model: {MODEL} | Effort: {EFFORT}. EFFORT semantics: {tier text}.
AUTONOMOUS RUN. No human is available. Resolve questions from code evidence,
record numbered assumptions in .ai files, proceed without blocking.
WORK_DIR={WORK_DIR}. It is already scaffolded and explored; read AGENTS.md and
follow the framework's protocol and skills. Do not re-run /explore unless
AGENTS.md says the requirements section is still a stub.
Record start: date '+%Y-%m-%dT%H:%M:%S'
TASK: {task text}
Use /spec then /build (read the SKILL.md files and follow them). Run the review
gate as the build skill says. Commit .ai. Do not run the benchmark GATE
yourself; the orchestrator does.
Write /tmp/benchmark/results/{RUN_ID}-s{N}.md: Configuration table (Run ID,
Session, Arm, Task, Model, Effort, Start, End), spec text, .ai log
(git -C .ai log --oneline --stat), git diff --stat HEAD, full diff,
3 observations including which of AGENTS.md, .ai/notes.md, .ai/notes/map.md
you read and what from them you actually used.
```

**B arm, task session (T1, T2, T3):**
```
You are benchmark agent {RUN_ID} session {N} (baseline arm, no framework).
Model: {MODEL} | Effort: {EFFORT}. EFFORT semantics: {tier text}.
AUTONOMOUS RUN. No human is available. Resolve questions from code evidence,
record numbered assumptions in $WORK_DIR/../BASELINE-NOTES-s{N}.md, proceed
without blocking. WORK_DIR={WORK_DIR}.
Record start: date '+%Y-%m-%dT%H:%M:%S'
TASK: {task text}
Keep the test suite green. Do not run the benchmark GATE yourself.
Write /tmp/benchmark/results/{RUN_ID}-s{N}.md: Configuration table, git diff
--stat HEAD, full diff, 3 observations.
```

Both arms: one fresh session per task (a new sub-agent or a new `claude`
process; never a resumed conversation), same work dir, both in the same
permission mode. The baseline arm has no memory between sessions except what
it left on disk in the repo; that is the condition a bare agent actually runs
under, and the arm is not given a notes file to level it.

## GATE (orchestrator, after every task session)

```bash
# 1. Full suite plus hidden tests. Hidden tests are copied in AFTER the
#    session and removed before the next one; the agent never sees them.
case $N in 2) H=test_hidden_t2_rename_column.py;; 3) H=test_hidden_t3_drop_column.py;; *) H="";; esac
[ -n "$H" ] && cp "$HIDDEN/$H" "$WORK_DIR/tests/"
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis cogapp >/dev/null 2>&1
  python -m pytest -q; echo "SUITE-EXIT: $?"
  cog --check README.md docs/*.rst; echo "COG-EXIT: $?"'
[ -n "$H" ] && rm "$WORK_DIR/tests/$H"
# 2. T1 only: no test file changed
git -C "$WORK_DIR" diff --stat HEAD -- tests/
```

PASS rules, all recorded per session:
- **T1:** suite green AND no file under `tests/` changed.
- **T2, T3:** suite green including the hidden file (6 hidden tests: API,
  collision or missing-column guard with no data loss, CLI). The agent's own
  tests count only via the suite; the hidden file decides.
- **COG (knowledge signal, recorded, not part of PASS):** `cog --check` exit
  0 means the agent regenerated `docs/cli-reference.rst` after adding a
  command. Verified at the base commit: exit 0 with no changes. Expected
  shape if knowledge carries: F arm fails or passes COG at T2 by discovery,
  then passes at T3 from notes; B arm's T3 is independent of its T2.

Hidden tests were verified on 2026-09-14 to fail at the base commit (4 of 6
fail; the two guard tests pass vacuously until the method exists and then
check that nothing is lost). They live in `benchmarks/hidden-tests/` and are
pinned; do not edit them between replications.

## Measurements (orchestrator duty, per session)

```bash
python3 "$TOKENS" --per-session "$WORK_DIR" >> /tmp/benchmark/results/$RUN_ID.md
```
(If sessions run as Task-tool sub-agents inside one orchestrator, isolate each
agent's transcript plus its reviewer sibling as documented in
`v6-vs-5.26-sonnet5-medium-2026-09-14/report.md`.)

Per session record: gate PASS/FAIL, COG exit, total tokens, output tokens,
API calls (steps), duration, and for the F arm: `.ai/notes.md` word count
after the session and whether the transcript shows a Read of `notes.md` or
`map.md` (grep the tool inputs; count, do not trust the agent's report).

## Results table (fixed format)

```
| Rep | Arm | Session | Task | Gate | COG | Steps | Output | Total | Duration | notes.md words | read notes/map |
|-----|-----|---------|------|------|-----|-------|--------|-------|----------|----------------|----------------|
| 1 | F | s0 | explore | n/a | n/a | ... | ... | ... | ... | ... | n/a |
| 1 | F | s1 | T1 | ... |
| 1 | F | s2 | T2 | ... |
| 1 | F | s3 | T3 | ... |
| 1 | B | s1 | T1 | ... |
| 1 | B | s2 | T2 | ... |
| 1 | B | s3 | T3 | ... |
| 2 | ... |
```

Then two derived tables:

**Marginal:** per rep, `F(T2)+F(T3)` vs `B(T2)+B(T3)` in total and output
tokens, and the T2 to T3 trend within each arm.

**Total sequence:** per rep, `F(s0+T1+T2+T3)` vs `B(T1+T2+T3)`.

## Verdict rule (stated before running; do not move it afterwards)

Primary, cost: count the replications in which the framework's marginal
`T2+T3` total tokens are lower than the baseline's.
- 3 of 3: amortization supported on this repo size.
- 2 of 3: inconclusive; run three more before saying anything.
- 0 or 1 of 3: amortization failed on this repo size (same verdict as the
  haiku round, now with n=3 and Sonnet 5).

Secondary, correctness: hidden-test PASS count over the six T2/T3 sessions
per arm, and the T1 PASS count. A cost loss with a correctness win is
reported as exactly that; the two are not netted against each other.

Tertiary, knowledge: COG exit per session and the `read notes/map` column.
If the F arm's T3 never reads `notes.md`, the framework's memory is not being
used and the cost result is about ceremony, not knowledge; say so.

Interpretation guardrails: a delta under 30% in a single pair is noise;
output tokens are the cleaner cost signal (cache reads dominate totals and the
arms cache differently); the reviewer sub-agent's tokens stay inside the F
arm's numbers.

## Optional third arm

C (context-only, from `fixed-runbook.md`): scaffold plus `/explore`, then T1
to T3 without `/spec`, `/build` or review, `.ai` left in place. Adds nine
sessions and separates "knowledge on disk" from "spec-driven workflow" inside
the framework's own cost. Run it only after F and B have a verdict; it is the
follow-up question, not this one.

## Checklist per replication

```
[ ] SEED: SHA 79117b9, bug state committed, T1 test fails pre-run
[ ] F arm: init -> explore (s0) committed in .ai before s1
[ ] one fresh session per task, same work dir, same permission mode both arms
[ ] hidden test copied in after the session, removed before the next
[ ] gate output recorded verbatim; COG exit recorded
[ ] token block per session (--per-session or isolated transcripts)
[ ] notes.md word count and read-evidence recorded (F arm)
[ ] B arm: BASELINE-NOTES-s<N>.md exists (agent followed the brief)
```

Record a round under `benchmarks/seq-<model>-<effort>-<date>/` with
`report.md` and the raw per-session files under `results/`.
