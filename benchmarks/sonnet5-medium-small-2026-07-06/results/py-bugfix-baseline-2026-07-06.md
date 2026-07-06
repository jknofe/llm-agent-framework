# py-bugfix-baseline-2026-07-06 (sqlite-utils, detect_fts bug)

## Configuration

| Field | Value |
|---|---|
| Run ID | py-bugfix-baseline-2026-07-06 |
| Cell | sqlite-utils / test_fts detect_fts bracket-quote bug |
| Arm | baseline (no framework) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-06T16:50:48 |
| End | 2026-07-06T16:52:40 |
| Duration | ~1m52s |
| Gate | PASS |

## Target diff

`git diff --stat HEAD~1` (HEAD~1 = 79117b9, the last commit before the seed
bug-injection commit; this measures the net effect of seed-bug + my fix
combined):

```
(no output — working tree is byte-identical to 79117b9)
```

This empty diff is expected and meaningful: the seed commit (b7a310b)
introduced a 1-line bug into `Table.detect_fts()`, and my fix is the
exact 1-line inverse of that seed change, restoring the original (upstream)
code. Net diff across seed+fix is zero.

For clarity, here is my actual contribution in isolation — the diff between
the working tree and HEAD (b7a310b, the seed/bug commit):

```diff
diff --git a/sqlite_utils/db.py b/sqlite_utils/db.py
index 4aaffb2..ae99322 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -2777,7 +2777,7 @@ class Table(Queryable):
                 )
         """).strip()
         args = {
-            "like": '%VIRTUAL TABLE%USING FTS%content="{}"%'.format(self.name),
+            "like": "%VIRTUAL TABLE%USING FTS%content=[{}]%".format(self.name),
             "like2": '%VIRTUAL TABLE%USING FTS%content="{}"%'.format(self.name),
             "table": self.name,
         }
```

`git diff --stat` against tests/ (test files untouched):

```
(no output)
```

## Root cause

`Table.detect_fts()` (sqlite_utils/db.py, ~line 2765) builds a SQL query with
two `LIKE` patterns (`:like`, `:like2`) meant to recognize two legacy quoting
styles SQLite uses for the `content=` clause of an FTS5 content-table
declaration: modern double-quoted (`content="books"`) and legacy
bracket-quoted (`content=[books]`).

In the seeded (bug) state, both `like` and `like2` were set to the identical
double-quoted pattern, so bracket-quoted content declarations
(`content=[books]`, as SQLite itself normalizes/echoes for tables created
with bracket-quoted syntax) were never matched by `detect_fts()`.

Concretely, this broke `test_enable_fts_replace_handles_legacy_bracket_quoted_content_table`:
the test creates `books_fts` manually via `CREATE VIRTUAL TABLE [books_fts]
USING FTS5 (... content=[books])`, then calls
`db["books"].enable_fts(["title", "author"], replace=True)`. With
`replace=True`, `enable_fts` calls `detect_fts()` to locate and drop any
existing FTS table before creating the new one. Because `detect_fts()`
failed to recognize the bracket-quoted `books_fts` table, the old table was
never dropped, and the subsequent `CREATE VIRTUAL TABLE books_fts ...`
collided with it, raising
`sqlite3.OperationalError: table "books_fts" already exists`.

Fix: restore `like` to the bracket-quoted pattern
(`content=[{}]`) while leaving `like2` as the double-quoted pattern
(`content="{}"`), so the two patterns are distinct and together cover both
legacy quoting styles. This exact assignment (not the reverse) was confirmed
necessary by `tests/test_tracer.py::test_with_tracer`, which asserts the
literal SQL args dict passed through the tracer and expects `like` to hold
the bracket-quoted pattern and `like2` the double-quoted one — i.e. the fix
had to match a specific, test-pinned naming convention, not just deduplicate
the two patterns arbitrarily.

## Full gate output

Docker command:
```
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'
```

```
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

[notice] A new release of pip is available: 25.0.1 -> 26.1.2
[notice] To update, run: pip install --upgrade pip
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
  /usr/local/lib/python3.12/site-packages/_pytest/python.py:124: PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
  Please convert to a list or tuple.
  See https://docs.pytest.org/en/stable/deprecations.html#parametrize-iterators
    metafunc.parametrize(*marker.args, **marker.kwargs, _param_mark=marker)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1080 passed, 16 skipped, 1 warning in 7.94s
EXIT: 0
```

`git diff --stat -- tests/`: no output (no test file modified).

**Gate result: PASS** (1080 passed, 16 skipped, 0 failed; no test files
modified).

## Observations

1. The seed bug was a single-line, semantically subtle duplication (`like2`
   set equal to `like`) rather than an obviously broken pattern — it required
   reading `detect_fts()`'s intent (two distinct legacy quoting styles) to
   recognize that the duplication itself was the defect, not just "some
   string is wrong somewhere."
2. A naive fix based only on the failing test's own literal content
   (`content=[books]`) risks getting the `like`/`like2` variable assignment
   backwards; a second, unrelated test (`test_tracer.py::test_with_tracer`)
   pins the exact named-parameter-to-pattern mapping via a snapshot of the
   executed SQL args, and running the full suite (not just the target test)
   caught this on the first attempt.
3. Running the single target test in isolation first (outside Docker) gave a
   fast, cheap repro loop (`sqlite3.OperationalError: table "books_fts"
   already exists`) before paying the cost of a full Docker suite run.
4. The fix's diff against `HEAD~1` (pre-seed) is empty, i.e. the true fix is
   an exact structural inverse of the seed's injected change — a clean signal
   that the root cause was correctly identified and not just papered over.
5. No test files were modified; the fix is contained to
   `sqlite_utils/db.py`'s `Table.detect_fts()` (2 changed characters:
   swapping which bracket/quote pattern is assigned to `like` vs `like2`).

## Token usage (count_tokens.py, informational)

Note: dispatched as a Task-tool sub-agent inside one orchestrator session;
counted by isolating this agent's `agent-<id>.jsonl` transcript.

- Transcript dir: `subagents/agent-ad530cc369ace270a.jsonl` (isolated)
- Sessions: 1 | API calls: 26 | duplicate lines skipped: 17

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 52 | 26601 | 747620 | 5406 | 779679 |
| **all** | 52 | 26601 | 747620 | 5406 | 779679 |
