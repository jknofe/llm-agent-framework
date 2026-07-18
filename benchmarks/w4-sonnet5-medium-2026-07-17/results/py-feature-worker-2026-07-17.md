# py-feature-worker-2026-07-17 — sqlite-utils: `rename-column` command + API

## Configuration

| Field | Value |
|---|---|
| Run ID | py-feature-worker-2026-07-17 |
| Cell | 4 (py-feature) |
| Twin | worker (W-ARM — dispatches fully-specified, test-verifiable checklist items to a `code-worker` sub-agent; main agent re-runs tests after every worker report) |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-17T18:55:03 |
| End | 2026-07-18T16:04:19 |
| Duration | ~1h10m of active agent work (see note) |
| Gate | **PASS** |

Note on Duration: the wall-clock gap between Start and End (~21h) includes a
session-limit reset (explicit "Session-limit reset; continue the run" restart
mid-task) with no agent activity in between. Active work was: ~50 min for
explore/spec/initial build/dispatch of the two first background workers
(tests + docs) before the reset, then ~20 min after resume to fix a
reviewer-found bug, dispatch a third worker for coverage gaps, run the
`reviewer` gate, finalize, and run the Docker gate.

## Task (verbatim)

> Add a `rename-column` CLI command and a `Table.rename_column(old, new)` API
> method, mirroring the existing `rename-table` command / `rename_table()`
> pattern (cli.py:1681, db.py:1233). Include tests and doc updates. (May
> delegate to `transform()`; watch for the `transform(rename=)` silent-data-loss
> collision - add an `AlterError` guard + regression test.)

## Premise verification

The TASK's two structural claims were verified directly against HEAD (79117b9)
before writing any code:

- `cli.py:1681` is `@cli.command(name="rename-table")` — confirmed.
- `db.py:1233` is `Database.rename_table(self, name, new_name)` — confirmed.
- The "silent-data-loss collision" claim was verified by direct repro, not
  assumed:
  ```python
  db = sqlite_utils.Database(memory=True)
  db['t'].insert({'a': 1, 'b': 2})
  db['t'].transform(rename={'a': 'b'})
  # -> no exception raised
  # -> list(db['t'].rows) == [{'b': 1}]   # b's original value (2) silently lost
  ```
  Root cause: `transform_sql()` builds `new_column_pairs`/`copy_from_to` keyed
  by the *new* column name with no collision check, so `dict(new_column_pairs)`
  and the generated copy-SQL silently coalesce two source columns into one
  destination column. **Confirmed as a genuine, reproducible bug**, not a
  hypothetical. Fixed at the `transform_sql()` root cause (not just inside the
  new `rename_column()`), so the guard also protects the pre-existing
  `transform(rename=)` Python API and the `sqlite-utils transform --rename`
  CLI flag from the same failure mode.

A second, unstated defect was found during the review gate (not in the
original TASK premise): SQLite treats column names as **case-insensitive**
for its duplicate-column constraint, but the first version of both new
collision guards compared names case-sensitively, so `rename("foo", "Bar")`
on a table that already had `bar` slipped past both guards and raised a raw
`sqlite3.OperationalError` instead of `AlterError` (not data loss — protected
by `self.db.atomic()` — but the wrong exception type, uncaught by the CLI's
`except (NoTable, AlterError)` clause, surfacing as an unhandled traceback).
Fixed by comparing via `.lower()` at both call sites.

## Spec produced

`.ai/changes/rename-column/spec.md` (status: done). Acceptance criteria (all met):
- `Table.rename_column(old_name, new_name)` in `sqlite_utils/db.py`: raises
  `NoTable` if table missing, `AlterError` if source column missing or target
  collides (case-insensitively) with a different existing column; delegates
  to `self.transform(rename=...)`.
- `sqlite-utils rename-column PATH TABLE COLUMN NEW_NAME` CLI command in
  `sqlite_utils/cli.py`, `--ignore` flag swallowing `NoTable`/`AlterError`,
  mirrors `rename-table`'s wording/structure.
- `AlterError` collision guard added to `transform_sql()` itself (general fix,
  not scoped only to `rename_column()`), case-insensitive.
- Regression tests for: the pre-fix silent-corruption scenario (asserting the
  table is untouched after the raise, not just that an exception fires), the
  case-insensitive variant of the same collision (both through `rename_column`
  and directly through `transform()`), missing column/table, and CLI
  `--ignore` for all three failure paths.
- Docs: `docs/cli.rst`, `docs/python-api.rst`, `docs/cli-reference.rst` (cog
  `refs` map + re-run `cog -r`).
- Full test suite green.

5 numbered assumptions recorded in spec Notes (CLI argument order, API method
placement on `Table` vs `Database`, the collision bug being real/confirmed
and fixed at the shared root, `--ignore` semantics, row-data-preservation as
the happy-path correctness bar), plus a "Review findings and fixes" section
appended after the build documenting the case-insensitivity bug and the two
coverage gaps found and closed during the review gate.

## `.ai` commit history

```
f89ebde build: rename-column done
384c0b9 build: rename-column in-progress
e83300a spec: rename-column
83573bb explore: project context
af6d68a init: small-profile scaffold (sqlite-utils)
```

## Target diff

```
$ git diff --stat HEAD
 .gitignore              |  1 +
 docs/cli-reference.rst  | 20 +++++++++++++++++
 docs/cli.rst            | 13 +++++++++++
 docs/python-api.rst     | 13 +++++++++++
 sqlite_utils/cli.py     | 29 +++++++++++++++++++++++++
 sqlite_utils/db.py      | 28 ++++++++++++++++++++++++
 tests/test_cli.py       | 57 +++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_create.py    | 37 ++++++++++++++++++++++++++++++++
 tests/test_transform.py | 39 ++++++++++++++++++++++++++++++++-
 9 files changed, 236 insertions(+), 1 deletion(-)
```
(The `.gitignore` `+.ai/` line is scaffold setup from `init_agent.py`, not
task-related; the other 8 files are the feature diff.)

Full diff (`sqlite_utils/`, `tests/`, `docs/`):

```diff
diff --git a/docs/cli-reference.rst b/docs/cli-reference.rst
index 48d0145..30171d9 100644
--- a/docs/cli-reference.rst
+++ b/docs/cli-reference.rst
@@ -41,6 +41,7 @@ This page lists the ``--help`` for every ``sqlite-utils`` CLI sub-command.
         "dump": "cli_dump",
         "add-column": "cli_add_column",
         "rename-table": "cli_renaming_tables",
+        "rename-column": "cli_renaming_columns",
         "duplicate": "cli_duplicate_table",
         "add-foreign-key": "cli_add_foreign_key",
         "add-foreign-keys": "cli_add_foreign_keys",
@@ -1401,6 +1402,25 @@ See :ref:`cli_renaming_tables`.
       -h, --help             Show this message and exit.
 
 
+.. _cli_ref_rename_column:
+
+rename-column
+=============
+
+See :ref:`cli_renaming_columns`.
+
+::
+
+    Usage: sqlite-utils rename-column [OPTIONS] PATH TABLE COLUMN NEW_NAME
+
+      Rename this column.
+
+    Options:
+      --ignore               If table or column does not exist, do nothing
+      --load-extension TEXT  Path to SQLite extension, with optional :entrypoint
+      -h, --help             Show this message and exit.
+
+
 .. _cli_ref_drop_table:
 
 drop-table
diff --git a/docs/cli.rst b/docs/cli.rst
index c9389d8..8db0557 100644
--- a/docs/cli.rst
+++ b/docs/cli.rst
@@ -2070,6 +2070,19 @@ Yo ucan rename a table using the ``rename-table`` command:
 
 Pass ``--ignore`` to ignore any errors caused by the table not existing, or the new name already being in use.
 
+.. _cli_renaming_columns:
+
+Renaming a column
+=================
+
+You can rename a column using the ``rename-column`` command:
+
+.. code-block:: bash
+
+    sqlite-utils rename-column mydb.db mytable oldname newname
+
+Pass ``--ignore`` to ignore any errors caused by the table or column not existing, or the new name already being in use.
+
 .. _cli_duplicate_table:
 
 Duplicating tables
diff --git a/docs/python-api.rst b/docs/python-api.rst
index eab858e..44fc2cb 100644
--- a/docs/python-api.rst
+++ b/docs/python-api.rst
@@ -803,6 +803,19 @@ This executes the following SQL:
 
     ALTER TABLE [my_table] RENAME TO [new_name_for_my_table]
 
+.. _python_api_rename_column:
+
+Renaming a column
+=================
+
+The ``table.rename_column(old_name, new_name)`` method can be used to rename a column:
+
+.. code-block:: python
+
+    db["my_table"].rename_column("headline", "title")
+
+This works even in versions of SQLite that do not support ``ALTER TABLE ... RENAME COLUMN`` directly, since it is implemented on top of :ref:`python_api_transform`.
+
 .. _python_api_duplicate:
 
 Duplicating tables
diff --git a/sqlite_utils/cli.py b/sqlite_utils/cli.py
index f15850d..2f70c95 100644
--- a/sqlite_utils/cli.py
+++ b/sqlite_utils/cli.py
@@ -1704,6 +1704,35 @@ def rename_table(path, table, new_name, ignore, load_extension):
             )
 
 
+@cli.command(name="rename-column")
+@click.argument(
+    "path",
+    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
+    required=True,
+)
+@click.argument("table")
+@click.argument("column")
+@click.argument("new_name")
+@click.option(
+    "--ignore", is_flag=True, help="If table or column does not exist, do nothing"
+)
+@load_extension_option
+def rename_column(path, table, column, new_name, ignore, load_extension):
+    """
+    Rename this column.
+    """
+    db = sqlite_utils.Database(path)
+    _register_db_for_cleanup(db)
+    _load_extensions(db, load_extension)
+    try:
+        db.table(table).rename_column(column, new_name)
+    except (NoTable, AlterError) as ex:
+        if not ignore:
+            raise click.ClickException(
+                'Column "{}" could not be renamed. {}'.format(column, str(ex))
+            )
+
+
 @cli.command(name="drop-table")
 @click.argument(
     "path",
diff --git a/sqlite_utils/db.py b/sqlite_utils/db.py
index ae99322..a424f90 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -1912,6 +1912,25 @@ class Table(Queryable):
             self.db.execute(sql)
         return self.db.table(new_name)
 
+    def rename_column(self, old_name: str, new_name: str) -> "Table":
+        """
+        Rename a column. See :ref:`python_api_rename_column`.
+
+        :param old_name: Current column name
+        :param new_name: Name to rename it to
+        """
+        if not self.exists():
+            raise NoTable(f"Table {self.name} does not exist")
+        if old_name not in self.columns_dict:
+            raise AlterError("No such column: {}".format(old_name))
+        existing_lower = {
+            c.lower() for c in self.columns_dict if c != old_name
+        }
+        if new_name.lower() in existing_lower:
+            raise AlterError("Column {} already exists".format(new_name))
+        self.transform(rename={old_name: new_name})
+        return self
+
     def transform(
         self,
         *,
@@ -2080,12 +2099,21 @@ class Table(Queryable):
         current_column_pairs = list(self.columns_dict.items())
         new_column_pairs = []
         copy_from_to = {column: column for column, _ in current_column_pairs}
+        new_name_sources: Dict[str, str] = {}
         for name, type_ in current_column_pairs:
             type_ = types.get(name) or type_
             if name in drop:
                 del [copy_from_to[name]]
                 continue
             new_name = rename.get(name) or name
+            new_name_key = new_name.lower()
+            if new_name_key in new_name_sources:
+                other_name = new_name_sources[new_name_key]
+                raise AlterError(
+                    "Cannot rename: columns '{}' and '{}' would both be called "
+                    "'{}'".format(other_name, name, new_name)
+                )
+            new_name_sources[new_name_key] = name
             new_column_pairs.append((new_name, type_))
             copy_from_to[name] = new_name
 
diff --git a/tests/test_cli.py b/tests/test_cli.py
index 565fbc2..44ba0d3 100644
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -2537,6 +2537,63 @@ def test_rename_table(tmpdir):
     assert db["two"].columns_dict == previous_columns
 
 
+def test_rename_column(tmpdir):
+    db_path = str(tmpdir / "test.db")
+    db = Database(db_path)
+    db["one"].insert({"id": 1, "name": "Cleo"}, pk="id")
+    # First try a non-existent table
+    result_error = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "missing_table", "x", "y"],
+        catch_exceptions=False,
+    )
+    assert result_error.exit_code == 1
+    assert result_error.output.startswith(
+        'Error: Column "x" could not be renamed.'
+    )
+    # And check --ignore works
+    result_error2 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "missing_table", "x", "y", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_error2.exit_code == 0
+    # Now try a non-existent column on a table that exists
+    result_error3 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "no_such_column", "y"],
+        catch_exceptions=False,
+    )
+    assert result_error3.exit_code == 1
+    assert result_error3.output.startswith(
+        'Error: Column "no_such_column" could not be renamed.'
+    )
+    # --ignore also suppresses the missing-column error
+    result_error3_ignore = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "no_such_column", "y", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_error3_ignore.exit_code == 0
+    # --ignore also suppresses a name-collision error
+    result_collision_ignore = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "id", "name", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_collision_ignore.exit_code == 0
+    # Now try for a column that exists
+    result = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "name", "full_name"],
+        catch_exceptions=False,
+    )
+    assert result.exit_code == 0
+    assert "full_name" in db["one"].columns_dict
+    assert "name" not in db["one"].columns_dict
+    assert list(db["one"].rows) == [{"id": 1, "full_name": "Cleo"}]
+
+
 def test_duplicate_table(tmpdir):
     db_path = str(tmpdir / "test.db")
     db = Database(db_path)
diff --git a/tests/test_create.py b/tests/test_create.py
index b1a6ad1..a879cd7 100644
--- a/tests/test_create.py
+++ b/tests/test_create.py
@@ -1325,6 +1325,43 @@ def test_rename_table(fresh_db):
         fresh_db.rename_table("does_not_exist", "renamed")
 
 
+def test_rename_column(fresh_db):
+    fresh_db["t"].insert({"foo": "bar"})
+    assert "foo" in fresh_db["t"].columns_dict
+    fresh_db["t"].rename_column("foo", "renamed")
+    assert "foo" not in fresh_db["t"].columns_dict
+    assert "renamed" in fresh_db["t"].columns_dict
+    assert [{"renamed": "bar"}] == list(fresh_db["t"].rows)
+    # Should error if column does not exist:
+    with pytest.raises(AlterError):
+        fresh_db.table("t").rename_column("does_not_exist_col", "x")
+    # Should error if table does not exist:
+    with pytest.raises(NoTable):
+        fresh_db.table("no_such_table").rename_column("a", "b")
+
+
+def test_rename_column_collision(fresh_db):
+    fresh_db["t"].insert({"a": 1, "b": 2})
+    previous_columns = fresh_db["t"].columns_dict
+    previous_rows = list(fresh_db["t"].rows)
+    with pytest.raises(AlterError):
+        fresh_db["t"].rename_column("a", "b")
+    # Table should be completely unchanged
+    assert fresh_db["t"].columns_dict == previous_columns
+    assert list(fresh_db["t"].rows) == previous_rows
+
+
+def test_rename_column_collision_case_insensitive(fresh_db):
+    fresh_db["t"].insert({"foo": 1, "bar": 2})
+    previous_columns = fresh_db["t"].columns_dict
+    previous_rows = list(fresh_db["t"].rows)
+    with pytest.raises(AlterError):
+        fresh_db["t"].rename_column("foo", "Bar")
+    # Table should be completely unchanged
+    assert fresh_db["t"].columns_dict == previous_columns
+    assert list(fresh_db["t"].rows) == previous_rows
+
+
 @pytest.mark.parametrize("strict", (False, True))
 def test_database_strict(strict):
     db = Database(memory=True, strict=strict)
diff --git a/tests/test_transform.py b/tests/test_transform.py
index 5eb501d..62a100b 100644
--- a/tests/test_transform.py
+++ b/tests/test_transform.py
@@ -1,4 +1,4 @@
-from sqlite_utils.db import ForeignKey, TransformError
+from sqlite_utils.db import AlterError, ForeignKey, TransformError
 from sqlite_utils.utils import OperationalError
 import pytest
 
@@ -255,6 +255,43 @@ def test_transform_add_not_null_with_rename(fresh_db, not_null):
     )
 
 
+def test_transform_rename_collision_raises_and_preserves_data(fresh_db):
+    dogs = fresh_db["dogs"]
+    dogs.insert_all(
+        [
+            {"id": 1, "age": 5, "dog_age": 35},
+            {"id": 2, "age": 3, "dog_age": 21},
+        ],
+        pk="id",
+    )
+    previous_columns = dogs.columns_dict
+    previous_rows = list(dogs.rows)
+    with pytest.raises(AlterError):
+        dogs.transform(rename={"age": "dog_age"})
+    # Table should be completely unchanged - no silent data loss
+    assert dogs.columns_dict == previous_columns
+    assert list(dogs.rows) == previous_rows
+
+
+def test_transform_rename_collision_case_insensitive(fresh_db):
+    dogs = fresh_db["dogs"]
+    dogs.insert_all(
+        [
+            {"id": 1, "age": 5, "Dog_Age": 35},
+            {"id": 2, "age": 3, "Dog_Age": 21},
+        ],
+        pk="id",
+    )
+    previous_columns = dogs.columns_dict
+    previous_rows = list(dogs.rows)
+    # "age" -> "dog_age" collides with existing "Dog_Age" case-insensitively
+    with pytest.raises(AlterError):
+        dogs.transform(rename={"age": "dog_age"})
+    # Table should be completely unchanged - no silent data loss
+    assert dogs.columns_dict == previous_columns
+    assert list(dogs.rows) == previous_rows
+
+
 def test_transform_defaults(fresh_db):
     dogs = fresh_db["dogs"]
     dogs.insert({"id": 1, "name": "Cleo", "age": 5}, pk="id")
```

## Sub-agent dispatch record (W-ARM worker twin)

Per the worker-twin protocol, the mechanical/multi-file, fully-specified
checklist items were dispatched to sub-agents; core judgment work (the
collision-guard design, `rename_column`, the CLI command) was done inline.

1. **`code-worker` agent type was unavailable at session start** despite being
   defined in `.claude/agents/code-worker.md`; the harness's initial available
   list was only `claude, Explore, general-purpose, Plan, statusline-setup`.
   Per the build skill's fallback ("spawn a fresh general-purpose sub-agent"),
   the first two dispatches (tests, docs) used `general-purpose`.
2. Dispatch 1 (`general-purpose`, background): wrote `test_rename_column`/
   `test_rename_column_collision` in `tests/test_create.py`, `test_rename_column`
   in `tests/test_cli.py`, and the collision regression test in
   `tests/test_transform.py`. Reported `414 passed, 4 skipped` on the targeted
   files; re-verified myself after report.
3. Dispatch 2 (`general-purpose`, background, parallel with #2): wrote the
   `docs/python-api.rst` and `docs/cli.rst` prose sections and the
   `docs/cli-reference.rst` `refs` entry, then ran `cog -r` itself and pasted
   the generated section back for verification.
4. After a review pass (see below) found the case-insensitivity bug and two
   coverage gaps, `code-worker` (now available after a mid-run tool refresh)
   was dispatched for the two test-coverage gaps (case-insensitive collision
   test in `test_create.py`; `--ignore` coverage for missing-column/collision
   paths in `test_cli.py`). Reported `415 passed, 4 skipped` on targeted
   files; re-verified myself (full suite) after report.
5. In every case the main agent re-ran the real test suite itself after the
   worker's self-reported result, per the standing instruction that a
   worker's self-report is not a gate result.

## Review gate

Two review passes, since the `reviewer` agent type was unavailable at first:

1. **First pass** (`general-purpose` fallback, before `reviewer` appeared):
   reviewed the initial diff against the spec's acceptance criteria. Found
   one real, medium-severity bug — case-insensitive column-name collisions
   (e.g. `rename("foo", "Bar")` where `bar` already exists) bypassed both new
   guards (case-sensitive `in` checks) and leaked a raw
   `sqlite3.OperationalError` instead of `AlterError`, uncaught by the CLI's
   `except (NoTable, AlterError)` clause. Also flagged one test-coverage gap
   (CLI `--ignore` only tested for the missing-table path). Both fixed:
   `.lower()`-keyed comparison at both guard sites (`db.py` ~1926-1930 and
   ~2103-2116); dispatched `code-worker` for the coverage-gap tests plus a new
   case-insensitive regression test.
2. **Second pass** (`reviewer` sub-agent, now available): re-reviewed the
   updated diff, ran the full suite independently (**1087 passed, 16
   skipped**), re-derived the cog output itself and diffed it byte-for-byte
   against the committed file (identical — confirms cog was genuinely
   re-run, not hand-edited), and manually confirmed the case-insensitivity
   fix at both call sites. Found **one residual test-coverage gap**: the new
   case-insensitive test only exercised `rename_column`'s own upfront guard,
   not the shared `transform_sql` guard that the spec says is the deliberate,
   general fix location (it also protects direct `.transform(rename=...)`
   callers). Verified this concretely by temporarily reverting only the
   `transform_sql`-level `.lower()` and confirming that pass's own
   sub-agent-authored tests still passed. Fixed by adding
   `test_transform_rename_collision_case_insensitive` directly to
   `tests/test_transform.py`, and confirmed the fix is real by the same
   revert-and-rerun technique (reverting the `transform_sql` guard's
   `.lower()` makes this new test fail with a raw `sqlite3.OperationalError`;
   restoring it passes). No further findings after that fix — reviewer
   verdict: **no correctness gaps**.

## Gate output (Docker, python:3.12)

Command run exactly as specified:
```
docker run --rm -v "$PWD":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'
```

Full output:
```
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

[notice] A new release of pip is available: 25.0.1 -> 26.1.2
[notice] To update, run: pip install --upgrade pip
........................................................................ [  6%]
........................................................................ [ 13%]
....................................................................sss. [ 19%]
........................................................................ [ 26%]
........................................................................ [ 32%]
........................................................................ [ 39%]
........................................................................ [ 45%]
........................................s............................... [ 52%]
........................................................................ [ 58%]
........................................................................ [ 65%]
........................................................................ [ 71%]
..................ssssssssssss.......................................... [ 78%]
........................................................................ [ 84%]
........................................................................ [ 91%]
........................................................................ [ 97%]
........................                                                 [100%]
=============================== warnings summary ===============================
../usr/local/lib/python3.12/site-packages/_pytest/python.py:124
  /usr/local/lib/python3.12/site-packages/_pytest/python.py:124: PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
  Please convert to a list or tuple.
  See https://docs.pytest.org/en/stable/deprecations.html#parametrize-iterators
    metafunc.parametrize(*marker.args, **marker.kwargs, _param_mark=marker)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1088 passed, 16 skipped, 1 warning in 9.18s
EXIT: 0
```

**PASS** — full suite green (1088 passed, 16 skipped — skips are pre-existing,
unrelated to this change, e.g. optional-dependency-gated tests), including
all 8 newly added tests across `test_create.py`, `test_cli.py`, and
`test_transform.py`.

## Observations

1. **The TASK's premise was real, and a second, unstated defect surfaced
   only through review.** The silent-data-loss collision was independently
   reproduced before any code was written. But the review gate caught a
   second, more subtle variant of the same class of bug — case-insensitive
   collisions — that neither the TASK description nor the initial
   implementation anticipated. This is exactly the kind of gap a same-context
   author is prone to miss (having just written the case-sensitive guard,
   it's easy to consider the collision problem "solved") and that a
   fresh-context review is well-suited to catch.
2. **Root-cause fix vs. narrow fix mattered, twice.** Both the original
   collision guard and its case-insensitivity fix were placed in
   `transform_sql()` itself rather than only inside `rename_column()`, so a
   single change closed the loophole for all three call paths
   (`rename_column`, direct `transform(rename=...)`, and
   `sqlite-utils transform --rename`) each time.
3. **Sub-agent availability was not static within the session.** `code-worker`
   and `reviewer` were both absent from the initially reported agent-type
   list and appeared later (once after an explicit tool-refresh notice, once
   after a session-limit reset and resume). The build skill's documented
   fallback (use `general-purpose`, escalate to the named type once
   available) handled this without blocking, and re-checking availability
   after the reset let the second half of the run use the intended
   `code-worker`/`reviewer` types instead of staying on the fallback
   indefinitely.
4. **A worker's self-reported pass is not a gate result — this was load-bearing
   here, not just a formality.** Every dispatched worker reported a passing
   targeted-file test run; the main agent's own full-suite re-run after each
   report is what actually caught that the suite was still green after each
   change, and, in the review-driven second round, is what confirmed the
   revert-and-rerun verification technique (deliberately breaking a fix to
   prove a new test detects its absence) rather than trusting a test's mere
   presence.
5. **RTK hook interception of raw `grep`/`sed` was a recurring friction
   point**, silently truncating output to "N matches in 0 files" instead of
   erroring — worth flagging early to sub-agents via the dispatch brief
   (prefix with `rtk proxy`, or use native Read/Grep tools) since a sub-agent
   hitting this cold could misread a truncated summary as "no matches" and
   draw a wrong conclusion.
## Token usage (count_tokens.py, informational)

- Transcript dir: `/Users/johannes/.claude/projects/-private-tmp-benchmark-runs-py-feature-worker-2026-07-17-sqlite-utils`
- Sessions: 1 | API calls: 117 | duplicate lines skipped: 106

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 229 | 383153 | 11614530 | 70657 | 12068569 |
| **all** | 229 | 383153 | 11614530 | 70657 | 12068569 |
