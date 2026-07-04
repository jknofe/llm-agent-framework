# Benchmark result: py-bugfix-s5m-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | py-bugfix-s5m-2026-07-03 |
| Cell | py-bugfix |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-03T20:10:56 |
| End | 2026-07-03T20:21:44 |
| Duration | ~10m48s |
| Gate | **PASS** |

## Task

`tests/test_fts.py::test_enable_fts_replace_handles_legacy_bracket_quoted_content_table`
failed with `sqlite3.OperationalError: table "books_fts" already exists`.
Find and fix the root cause (in `detect_fts`, per the task hint), not just
the symptom. Do not modify any test file.

## Root-cause finding

**Real root cause, not the symptom.** `Table.detect_fts()`
(`sqlite_utils/db.py`, ~line 2765) finds an FTS virtual table linked to a
base table by grepping `sqlite_master.sql` (which stores the *literal*
`CREATE VIRTUAL TABLE` text SQLite was given) for the table's `content=`
backref, using two SQL `LIKE` patterns bound as `:like` / `:like2`. Legacy
tables (older sqlite-utils, or hand-written SQL) may use bracket-quoting
(`content=[books]`); current sqlite-utils writes double-quote-quoting
(`content="books"`). Both forms need their own distinct LIKE pattern.

At session start, the *working tree* (uncommitted, pre-existing state -
distinct from the pinned commit's tracked content) had both `like` and
`like2` bound to the **same** double-quoted pattern; the bracket-quoted
pattern was missing. Effect chain:

1. `enable_fts(["title","author"], replace=True)` sees `books_fts` exists,
   schema differs -> `should_recreate = True` -> calls `self.disable_fts()`.
2. `disable_fts()` calls `self.detect_fts()` to find the table to drop.
   Because the working-tree bug meant neither LIKE pattern matched the
   literal `content=[books]` text, and the query's third OR clause
   (`tbl_name = :table AND sql LIKE '%VIRTUAL TABLE%USING FTS%'`) matches
   only the *base* table's own row (whose `sql` never contains `VIRTUAL
   TABLE`), `detect_fts()` returned `None`. `disable_fts()` silently no-ops.
3. `enable_fts()` then runs `CREATE VIRTUAL TABLE "books_fts" ...` against a
   table that never got dropped -> `OperationalError: table "books_fts"
   already exists` - the reported symptom, two hops downstream of the actual
   defect.

**Fix**: restore two distinct LIKE patterns in `detect_fts()`'s `args` dict -
`like` = bracket-quoted (`content=[{name}]`), `like2` = double-quote-quoted
(`content="{name}"`) - in that exact key order, because
`tests/test_tracer.py::test_with_tracer` (an unrelated-looking, pre-existing,
currently-passing test) hardcodes the literal SQL + params dict passed to
`db.execute()` for this exact query, including which key holds which
pattern.

**Process note (recorded transparently):** while diagnosing, I ran `git
stash` / `git checkout --` on `sqlite_utils/db.py` before capturing a
pre-fix diff, which overwrote the original uncommitted buggy bytes with the
pinned commit's tracked content before I had committed or diffed them. I
reconstructed the exact original bug text from my first `Read` of the file
(verified against the reported symptom by rebuilding it and re-triggering
the identical `OperationalError`), then re-applied the two-pattern fix. The
end state - two distinct LIKE patterns, `like`=bracket, `like2`=quoted - is
verified correct both by the full gate suite and by a fresh-context reviewer
sub-agent, and turns out to be byte-identical to the pinned commit's tracked
`sqlite_utils/db.py` (see below) and to match upstream commit `1a28416`
("Fix for detect_fts failing on [], refs #694"), which the reviewer
independently found already present in this repo's git history at the
pinned SHA. Net effect: the working tree had an *uncommitted* local
regression of an already-fixed upstream bug; fixing it means the working
tree now matches HEAD exactly.

## Spec / plan produced

`.ai/changes/fts-detect-legacy-bracket/spec.md` (status: done). Goal,
acceptance criteria (target test passes; full suite incl.
`test_tracer.py::test_with_tracer` passes; no `tests/` file touched; minimal
targeted diff), task checklist, review section, and 3 numbered assumptions
recording the reconstruction reasoning above (evidence: original read text,
reproduction of the exact symptom, `git show HEAD` comparison).

## .ai commit history

```
2a99884 build: fts-detect-legacy-bracket
0902d44 spec: fts-detect-legacy-bracket
22205ac explore: project context
9a56599 init: small-profile scaffold (sqlite-utils)
```

## Target diff

```
$ git diff --stat HEAD
 .gitignore | 1 +
 1 file changed, 1 insertion(+)
```

`sqlite_utils/db.py` has **zero diff from HEAD** - the fix brought the
working tree back to byte-identical match with the pinned commit's tracked
content (see root-cause finding above for why this is the expected, correct
end state, not a no-op). The only diff anywhere in the host repo is the
framework's own `.gitignore` addition (`.ai/`), unrelated to the target
code.

Current (fixed, == HEAD) `detect_fts()`:

```python
def detect_fts(self) -> Optional[str]:
    "Detect if table has a corresponding FTS virtual table and return it"
    sql = textwrap.dedent("""
        SELECT name FROM sqlite_master
            WHERE rootpage = 0
            AND (
                sql LIKE :like
                OR sql LIKE :like2
                OR (
                    tbl_name = :table
                    AND sql LIKE '%VIRTUAL TABLE%USING FTS%'
                )
            )
    """).strip()
    args = {
        "like": "%VIRTUAL TABLE%USING FTS%content=[{}]%".format(self.name),
        "like2": '%VIRTUAL TABLE%USING FTS%content="{}"%'.format(self.name),
        "table": self.name,
    }
    rows = self.db.execute(sql, args).fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0][0]
```

Buggy working-tree text present at session start (reconstructed and
verified to reproduce the exact reported symptom):

```python
    args = {
        "like": '%VIRTUAL TABLE%USING FTS%content="{}"%'.format(self.name),
        "like2": '%VIRTUAL TABLE%USING FTS%content="{}"%'.format(self.name),
        "table": self.name,
    }
```

## Gate output (full)

```
$ docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
    pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'

........................................................................ [  6%]
........................................................................ [ 13%]
...................................................................sss.. [ 19%]
........................................................................ [ 26%]
........................................................................ [ 32%]
........................................................................ [ 39%]
........................................................................ [ 45%]
.......................................s................................ [ 52%]
........................................................................ [ 59%]
........................................................................ [ 65%]
........................................................................ [ 72%]
............ssssssssssss................................................ [ 78%]
........................................................................ [ 85%]
........................................................................ [ 91%]
........................................................................ [ 98%]
................                                                         [100%]
=============================== warnings summary ===============================
../usr/local/lib/python3.12/site-packages/_pytest/python.py:124
  PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1080 passed, 16 skipped, 1 warning in 6.84s
EXIT: 0

$ git -C "$WORK_DIR" diff --stat -- tests/
(empty - no test file changed)
```

PASS = full suite green AND no test file modified: **both true.**

## Observations

1. The reported symptom (`table "books_fts" already exists` at `CREATE
   VIRTUAL TABLE` time) was genuinely two hops from the real defect
   (`detect_fts()`'s LIKE-pattern matching) via `disable_fts()`'s silent
   no-op when detection fails - matches the task's explicit hint exactly.
2. `tests/test_tracer.py::test_with_tracer` is an easy trap: a
   naive fix that detects both quoting styles but swaps which dict key
   (`like` vs `like2`) holds which pattern passes the target test but
   breaks this unrelated-looking, pre-existing test via an exact-match
   assertion on internal SQL args. Caught this only by running the full
   suite, not just the target test, and by the reviewer sub-agent.
3. Process mistake: I should have run `git status`/`git diff` on the target
   repo *before* my first edit, to capture the pre-existing uncommitted bug
   as a clean baseline diff. I overwrote it with an `Edit` call, then
   further confused the picture with `git stash`/`git checkout --` cycles
   that reverted the file to HEAD (which was, unbeknownst to me at the
   time, already the correct/fixed version). I recovered by reconstructing
   the original bug text from my first `Read` output and independently
   re-confirming it reproduces the exact reported symptom, then
   re-verifying the fix via gate + reviewer sub-agent. Net technical result
   is correct and verified; the artifact trail is messier than it should
   have been.
4. A fresh-context `general-purpose` sub-agent stood in for the `reviewer`
   sub-agent (not available in this harness) per the framework's escalation
   path; it independently traced the fix to upstream commit `1a28416`
   ("Fix for detect_fts failing on [], refs #694"), corroborating that this
   was a real, previously-known, already-upstream-fixed bug rather than a
   novel defect.
5. Local venv (host Python 3.14 / SQLite 3.53) and the docker gate (Python
   3.12 / SQLite 3.46) both reproduced the bug and both confirm the fix;
   behavior was consistent across SQLite versions since `sqlite_master.sql`
   stores literal CREATE-statement text regardless of engine version.
