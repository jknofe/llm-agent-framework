# Result: py-feature-baseline-2026-07-06 (sqlite-utils)

## Configuration

| Field | Value |
|---|---|
| Run ID | py-feature-baseline-2026-07-06 |
| Cell | sqlite-utils / rename-column feature |
| Arm | baseline (no framework) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-06T16:51:05 |
| End | 2026-07-06T16:58:31 |
| Duration | ~7m26s |
| Gate | **PASS** |

## Task (verbatim)

> Add a rename-column CLI command and a Table.rename_column(old, new) API
> method, mirroring the existing rename-table command / rename_table()
> pattern (cli.py:1681, db.py:1233). Include tests and doc updates.

## Premise-verification finding (silent-data-loss collision)

Verified the mirrored pattern in the actual code first (db.py:1233
`rename_table`, cli.py:1681 `rename-table`). The natural way to implement a
general-purpose column rename (handling indexes/foreign keys) is to delegate
to the existing `Table.transform(rename={old: new})` mechanism.

Confirmed by direct experiment that naive delegation has a real silent
data-loss bug: `transform()`'s `rename=` dict is applied via
`new_name = rename.get(name) or name` and then `dict(new_column_pairs)`
(db.py ~2083-2090). If `new_name` collides with an existing, non-renamed
column, the dict silently coalesces both entries and the generated
`INSERT INTO ... SELECT` maps two source columns onto one destination
column - no exception is raised.

Reproduced:
```python
db['t'].insert({'a': 1, 'b': 2}, pk='a')
db['t'].transform(rename={'a': 'b'})
# => rows become [{'b': 2}] -- column 'a' data (1) silently lost
```

Mitigation: `Table.rename_column()` now guards explicitly before delegating
to `transform()`:
- no-op if old == new,
- `AlterError` if the table doesn't exist,
- `AlterError` if the old column doesn't exist,
- `AlterError` if the new name already exists as a distinct column (the
  collision guard) - only then does it call `transform(rename={old: new})`.

A regression test (`test_rename_column_refuses_collision_with_existing_column`
in `tests/test_transform.py`) exercises exactly this scenario and asserts the
table is left completely untouched. See numbered assumptions 1-3 in
`BASELINE-NOTES.md` for full detail.

## Target diff

```
$ git diff --stat HEAD
 docs/cli-reference.rst  | 20 ++++++++++++++++++
 docs/cli.rst            | 15 ++++++++++++++
 docs/python-api.rst     | 15 ++++++++++++++
 sqlite_utils/cli.py     | 25 +++++++++++++++++++++++
 sqlite_utils/db.py      | 28 +++++++++++++++++++++++++
 tests/test_cli.py       | 50 +++++++++++++++++++++++++++++++++++++++++++++
 tests/test_transform.py | 54 ++++++++++++++++++++++++++++++++++++++++++++++++-
 7 files changed, 206 insertions(+), 1 deletion(-)
```

Full diff:

```diff
diff --git a/docs/cli-reference.rst b/docs/cli-reference.rst
index 48d0145..1270ec5 100644
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
+      Rename a column in this table.
+
+    Options:
+      --ignore               If column does not exist, do nothing
+      --load-extension TEXT  Path to SQLite extension, with optional :entrypoint
+      -h, --help             Show this message and exit.
+
+
 .. _cli_ref_drop_table:
 
 drop-table
diff --git a/docs/cli.rst b/docs/cli.rst
index c9389d8..fc5b698 100644
--- a/docs/cli.rst
+++ b/docs/cli.rst
@@ -2070,6 +2070,21 @@ Yo ucan rename a table using the ``rename-table`` command:
 
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
+    sqlite-utils rename-column mydb.db mytable oldcolumn newcolumn
+
+Pass ``--ignore`` to ignore any errors caused by the table or column not existing.
+
+If ``newcolumn`` already exists as a column on the table, an error will be raised rather than silently combining the two columns together.
+
 .. _cli_duplicate_table:
 
 Duplicating tables
diff --git a/docs/python-api.rst b/docs/python-api.rst
index eab858e..c832be0 100644
--- a/docs/python-api.rst
+++ b/docs/python-api.rst
@@ -803,6 +803,21 @@ This executes the following SQL:
 
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
+    db["my_table"].rename_column("old_name", "new_name")
+
+This is implemented using ``table.transform(rename=...)`` under the hood - see :ref:`python_api_transform` for details of that mechanism, including its handling of indexes and foreign keys.
+
+If ``new_name`` already exists as a column on the table a ``sqlite_utils.db.AlterError`` exception will be raised, rather than silently combining the values of the two columns together.
+
 .. _python_api_duplicate:
 
 Duplicating tables
diff --git a/sqlite_utils/cli.py b/sqlite_utils/cli.py
index f15850d..120d9d0 100644
--- a/sqlite_utils/cli.py
+++ b/sqlite_utils/cli.py
@@ -1704,6 +1704,31 @@ def rename_table(path, table, new_name, ignore, load_extension):
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
+@click.option("--ignore", is_flag=True, help="If column does not exist, do nothing")
+@load_extension_option
+def rename_column(path, table, column, new_name, ignore, load_extension):
+    """
+    Rename a column in this table.
+    """
+    db = sqlite_utils.Database(path)
+    _register_db_for_cleanup(db)
+    _load_extensions(db, load_extension)
+    try:
+        db[table].rename_column(column, new_name)
+    except AlterError as ex:
+        if not ignore:
+            raise click.ClickException(str(ex))
+
+
 @cli.command(name="drop-table")
 @click.argument(
     "path",
diff --git a/sqlite_utils/db.py b/sqlite_utils/db.py
index ae99322..7ffe192 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -2208,6 +2208,34 @@ class Table(Queryable):
                 sqls.append(index_sql)
         return sqls
 
+    def rename_column(self, column_name: str, new_column_name: str) -> "Table":
+        """
+        Rename a column within this table.
+
+        :param column_name: Current column name
+        :param new_column_name: Name to rename it to
+        """
+        if not self.exists():
+            raise AlterError("No such table: {}".format(self.name))
+        if column_name == new_column_name:
+            return self
+        if column_name not in self.columns_dict:
+            raise AlterError(
+                "No such column: {} in table {}".format(column_name, self.name)
+            )
+        if new_column_name in self.columns_dict:
+            # Renaming to a name that already exists would silently corrupt
+            # the table via transform()'s rename= mechanism, since two
+            # source columns would collapse onto a single destination
+            # column name. Refuse instead.
+            raise AlterError(
+                "Column {} already exists in table {}".format(
+                    new_column_name, self.name
+                )
+            )
+        self.transform(rename={column_name: new_column_name})
+        return self
+
     def extract(
         self,
         columns: Union[str, Iterable[str]],
diff --git a/tests/test_cli.py b/tests/test_cli.py
index 565fbc2..d905b44 100644
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -2537,6 +2537,56 @@ def test_rename_table(tmpdir):
     assert db["two"].columns_dict == previous_columns
 
 
+def test_rename_column(tmpdir):
+    db_path = str(tmpdir / "test.db")
+    db = Database(db_path)
+    db["one"].insert({"id": 1, "name": "Cleo"}, pk="id")
+    # First try a non-existent table
+    result_error = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "missing", "name", "title"],
+        catch_exceptions=False,
+    )
+    assert result_error.exit_code == 1
+    assert result_error.output == "Error: No such table: missing\n"
+    # And check --ignore works
+    result_error2 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "missing", "name", "title", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_error2.exit_code == 0
+    # Now try a non-existent column
+    result_error3 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "missing_column", "title"],
+        catch_exceptions=False,
+    )
+    assert result_error3.exit_code == 1
+    assert result_error3.output == (
+        "Error: No such column: missing_column in table one\n"
+    )
+    # Renaming to a name that already exists should be refused, not silently
+    # collapse the two columns together
+    result_error4 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "name", "id"],
+        catch_exceptions=False,
+    )
+    assert result_error4.exit_code == 1
+    assert result_error4.output == "Error: Column id already exists in table one\n"
+    assert db["one"].columns_dict == {"id": int, "name": str}
+    # Now try for a column that exists
+    result = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "name", "title"],
+        catch_exceptions=False,
+    )
+    assert result.exit_code == 0
+    assert db["one"].columns_dict == {"id": int, "title": str}
+    assert list(db["one"].rows) == [{"id": 1, "title": "Cleo"}]
+
+
 def test_duplicate_table(tmpdir):
     db_path = str(tmpdir / "test.db")
     db = Database(db_path)
diff --git a/tests/test_transform.py b/tests/test_transform.py
index 5eb501d..68391de 100644
--- a/tests/test_transform.py
+++ b/tests/test_transform.py
@@ -1,4 +1,4 @@
-from sqlite_utils.db import ForeignKey, TransformError
+from sqlite_utils.db import AlterError, ForeignKey, TransformError
 from sqlite_utils.utils import OperationalError
 import pytest
 
@@ -659,3 +659,55 @@ def test_transform_with_unique_constraint_implicit_index(fresh_db):
         "You must manually drop this index prior to running this transformation and manually recreate the new index after running this transformation."
         in str(excinfo.value)
     )
+
+
+def test_rename_column(fresh_db):
+    dogs = fresh_db["dogs"]
+    dogs.insert({"id": 1, "name": "Cleo", "age": 5}, pk="id")
+    dogs.rename_column("age", "dog_age")
+    assert (
+        dogs.schema
+        == 'CREATE TABLE "dogs" (\n   "id" INTEGER PRIMARY KEY,\n   "name" TEXT,\n   "dog_age" INTEGER\n)'
+    )
+    assert list(dogs.rows) == [{"id": 1, "name": "Cleo", "dog_age": 5}]
+
+
+def test_rename_column_no_op_if_names_match(fresh_db):
+    dogs = fresh_db["dogs"]
+    dogs.insert({"id": 1, "name": "Cleo", "age": 5}, pk="id")
+    # Should not error, and should not touch the table at all
+    dogs.rename_column("age", "age")
+    assert list(dogs.rows) == [{"id": 1, "name": "Cleo", "age": 5}]
+
+
+def test_rename_column_table_does_not_exist(fresh_db):
+    with pytest.raises(AlterError) as excinfo:
+        fresh_db["does_not_exist"].rename_column("age", "dog_age")
+    assert "No such table: does_not_exist" in str(excinfo.value)
+
+
+def test_rename_column_column_does_not_exist(fresh_db):
+    dogs = fresh_db["dogs"]
+    dogs.insert({"id": 1, "name": "Cleo", "age": 5}, pk="id")
+    with pytest.raises(AlterError) as excinfo:
+        dogs.rename_column("weight", "dog_weight")
+    assert "No such column: weight in table dogs" in str(excinfo.value)
+
+
+def test_rename_column_refuses_collision_with_existing_column(fresh_db):
+    # Regression test: renaming a column to a name that already exists on the
+    # table would otherwise be silently accepted by transform()'s rename=
+    # mechanism, which collapses both columns into one destination column
+    # and drops one of the two sets of values. rename_column() must refuse
+    # this instead of corrupting data.
+    dogs = fresh_db["dogs"]
+    dogs.insert({"id": 1, "name": "Cleo", "age": 5}, pk="id")
+    with pytest.raises(AlterError) as excinfo:
+        dogs.rename_column("age", "name")
+    assert "Column name already exists in table dogs" in str(excinfo.value)
+    # Table should be completely untouched
+    assert (
+        dogs.schema
+        == 'CREATE TABLE "dogs" (\n   "id" INTEGER PRIMARY KEY,\n   "name" TEXT,\n   "age" INTEGER\n)'
+    )
+    assert list(dogs.rows) == [{"id": 1, "name": "Cleo", "age": 5}]
```

## Gate output (STEP 2, mandatory)

Command:
```
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'
```

Output:
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
...............ssssssssssss............................................. [ 78%]
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
1088 passed, 16 skipped, 1 warning in 9.78s
EXIT: 0
```

**Gate result: PASS** (1088 passed, 0 failed, 16 skipped, includes 8 new
tests: 5 in `tests/test_transform.py`, 1 in `tests/test_cli.py` with 5
sub-assertions covering happy path / --ignore / missing column / collision
guard).

### Repo's own configured lint (recorded, not gating)

Run via `Justfile`'s `lint` recipe steps individually (black, flake8 via
`flake8-pyproject` honoring `max-line-length = 160` from `pyproject.toml`,
mypy, cog --check), using a scratch venv since these dev-group tools are not
preinstalled ambiently:

- `black --check .` -> "All done! 60 files would be left unchanged."
- `flake8` -> clean, exit 0 (installed `flake8-pyproject` so the
  project's 160-char line-length config applied - without it, ~40 spurious
  pre-existing E501s appear that are not part of this change).
- `mypy sqlite_utils tests` -> "no issues found"
- `cog --check README.md docs/*.rst` -> clean (all 10 files reported
  "Checking ...", no diffs)

Did not run `codespell` (needs the `docs` uv dependency group's network
access for install verification of word list; not attempted since it's
non-gating and out of scope for this diff, which added no misspelled prose
beyond the "Yo ucan" pre-existing typo it was mirroring, untouched).

## Observations

1. The task's stated risk was real and reproducible, not hypothetical:
   `Table.transform(rename={old: new})` silently corrupts data when the
   target name collides with an existing column (verified: renaming `a`
   to `b` when `b` already exists drops `a`'s values with no exception, no
   warning). A naive one-line `rename_column = lambda t,o,n:
   t.transform(rename={o:n})` implementation would have shipped this bug
   straight into a new public API and CLI command.
2. `tests/test_docs.py::test_commands_are_documented` is a repo-specific
   guardrail that fails the whole suite if a new CLI command isn't
   mentioned in `cli.rst`/`plugins.rst` - this caught an incomplete first
   pass (docs not yet updated) during a local pre-gate full-suite run, so
   the doc requirement in the task is also enforced mechanically, not just
   a nice-to-have.
3. `docs/cli-reference.rst` is cog-generated from live `--help` output; it
   cannot be hand-edited sustainably. Reproducing it correctly required
   installing `cogapp` (a `docs`-group dev dependency not present in the
   base environment) into a throwaway venv and running `cog -r`, then
   verifying with `cog --check`.
4. Existing exception vocabulary (`AlterError`, "Error altering table") was
   reused rather than inventing a new exception type, since it's already
   the established convention for "no such table"/"no such column"
   problems elsewhere in `db.py` (e.g. `add_foreign_keys`), keeping the
   new method's error-handling consistent with sibling methods.
5. Environment noise: an `rtk` shell hook in this session intercepts and
   rewrites some commands (`grep`, `pip`) and occasionally returns
   compressed/garbled output (e.g. "0 matches in 0 files [+N more]"
   instead of literal grep hits), which slowed down code exploration until
   `python3 -c` one-liners and the Read tool were used instead. Not related
   to the target repo; worth noting as a benchmark-harness artifact.

## Token usage (count_tokens.py, informational)

Note: dispatched as a Task-tool sub-agent inside one orchestrator session;
counted by isolating this agent's `agent-<id>.jsonl` transcript.

- Transcript dir: `subagents/agent-a146a1fcae7acf1f3.jsonl` (isolated)
- Sessions: 1 | API calls: 104 | duplicate lines skipped: 78

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 208 | 91132 | 6119050 | 8388 | 6218778 |
| **all** | 208 | 91132 | 6119050 | 8388 | 6218778 |
