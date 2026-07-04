# Benchmark Results: sqlite-utils rename-column Feature

## Configuration Table

| Attribute | Value |
|-----------|-------|
| Run ID | py-feature-baseline-2026-07-04 |
| Cell | py-feature |
| Arm | baseline |
| Model | claude-haiku-4-5 |
| Effort | high |
| Start | 2026-07-04T18:59:31 |
| End | 2026-07-04T19:02:56 |
| Duration | 3m 25s |
| Gate Result | **PASS** ✓ |

## Gate Test Output

```
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. Use the --root-user-action option if you know what you are doing.

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
.................ssssssssssss........................................... [ 78%]
........................................................................ [ 85%]
........................................................................ [ 91%]
........................................................................ [ 98%]
.....................                                                    [100%]

=============================== warnings summary ===============================
../usr/local/lib/python3.12/site-packages/_pytest/python.py:124
  /usr/local/lib/python3.12/site-packages/_pytest/python.py:124: PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
  Please convert to a list or tuple.
  See https://docs.pytest.org/en/stable/deprecations.html/parametrize-iterators

-- Docs: https://docs.pytest.org/en/stable/how-to/parametrize-iterators
1085 passed, 16 skipped, 1 warning in 7.99s
EXIT: 0
```

## Premise Verification

All premises in the TASK have been verified against the codebase:

1. ✓ `rename_table()` exists in Database class (db.py:1233) using `ALTER TABLE ... RENAME TO`
2. ✓ CLI command `rename-table` exists in cli.py:1681, mirrors Database.rename_table()
3. ✓ Pattern confirmed: CLI commands take (path, args), call db methods, handle errors with --ignore
4. ✓ SQLite ALTER TABLE ... RENAME COLUMN is supported (standard SQL since SQLite 3.25.0, 2018)
5. ✓ Test suite includes tests for both CLI and API variants

## Target Diff

**Summary (git diff --stat):**
```
docs/cli.rst         | 13 +++++++++++++
docs/python-api.rst  | 23 +++++++++++++++++++++++
sqlite_utils/cli.py  | 27 +++++++++++++++++++++++++++
sqlite_utils/db.py   | 23 +++++++++++++++++++++++
tests/test_cli.py    | 31 +++++++++++++++++++++++++++++++
tests/test_create.py | 20 ++++++++++++++++++++
6 files changed, 137 insertions(+)
```

**Full Diff:**

```diff
diff --git a/docs/cli.rst b/docs/cli.rst
index xxxxx..xxxxx 100644
--- a/docs/cli.rst
+++ b/docs/cli.rst
@@ -2070,6 +2070,19 @@ Yo ucan rename a table using the ``rename-table`` command:
 
 Pass ``--ignore`` to ignore any errors caused by the table not existing, or the new name already being in use.
 
+.. _cli_rename_column:
+
+Renaming columns
+================
+
+You can rename a column using the ``rename-column`` command:
+
+.. code-block:: bash
+
+    sqlite-utils rename-column mydb.db tablename oldcolumn newcolumn
+
+Pass ``--ignore`` to ignore any errors caused by the column not existing.
+
 .. _cli_duplicate_table:
 
 Duplicating tables

diff --git a/docs/python-api.rst b/docs/python-api.rst
index xxxxx..xxxxx 100644
--- a/docs/python-api.rst
+++ b/docs/python-api.rst
@@ -803,6 +803,29 @@ This executes the following SQL:
 
     ALTER TABLE [my_table] RENAME TO [new_name_for_my_table]
 
+.. _python_api_rename_column:
+
+Renaming a column
+=================
+
+The ``db.rename_column(table, old, new)`` method can be used to rename a column in a table:
+
+.. code-block:: python
+
+    db.rename_column("my_table", "old_name", "new_name")
+
+Alternatively, you can use the ``table.rename_column(old, new)`` method:
+
+.. code-block:: python
+
+    db.table("my_table").rename_column("old_name", "new_name")
+
+This executes the following SQL:
+
+.. code-block:: sql
+
+    ALTER TABLE [my_table] RENAME COLUMN [old_name] TO [new_name]
+
 .. _python_api_duplicate:
 
 Duplicating tables

diff --git a/sqlite_utils/cli.py b/sqlite_utils/cli.py
index xxxxx..xxxxx 100644
--- a/sqlite_utils/cli.py
+++ b/sqlite_utils/cli.py
@@ -1704,6 +1704,33 @@ def rename_table(path, table, new_name, ignore, load_extension):
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
+        db.rename_column(table, column, new_name)
+    except sqlite3.OperationalError as ex:
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
index xxxxx..xxxxx 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -1243,6 +1243,20 @@ class Database:
             )
 
 
+    def rename_column(self, table: str, old: str, new: str) -> None:
+        """
+        Rename a column in a table.
+
+        :param table: Table name
+        :param old: Current column name
+        :param new: Name to rename it to
+        """
+        self.execute(
+            "ALTER TABLE {} RENAME COLUMN {} TO {}".format(
+                quote_identifier(table), quote_identifier(old), quote_identifier(new)
+            )
+        )
+
     def create_view(
         self, name: str, sql: str, ignore: bool = False, replace: bool = False
     ) -> "Database":

diff --git a/sqlite_utils/db.py b/sqlite_utils/db.py
index xxxxx..xxxxx 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -2460,6 +2460,15 @@ class Table(Queryable):
             if not ignore:
                 raise
 
+    def rename_column(self, old: str, new: str) -> None:
+        """
+        Rename a column in this table.
+
+        :param old: Current column name
+        :param new: Name to rename it to
+        """
+        self.db.rename_column(self.name, old, new)
+
     def guess_foreign_table(self, column: str) -> str:
         """
         For a given column, suggest another table that might be referenced by this

diff --git a/tests/test_cli.py b/tests/test_cli.py
index xxxxx..xxxxx 100644
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -2537,6 +2537,37 @@ def test_rename_table(tmpdir):
     assert db["two"].columns_dict == previous_columns
 
 
+def test_rename_column(tmpdir):
+    db_path = str(tmpdir / "test.db")
+    db = Database(db_path)
+    db["one"].insert({"id": 1, "name": "Cleo"}, pk="id")
+    # First try a non-existent column
+    result_error = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "missing", "new_col"],
+        catch_exceptions=False,
+    )
+    assert result_error.exit_code == 1
+    assert "Column" in result_error.output and "could not be renamed" in result_error.output
+    # And check --ignore works
+    result_error2 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "missing", "new_col", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_error2.exit_code == 0
+    # Now rename an existing column
+    result = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "name", "full_name"],
+        catch_exceptions=False,
+    )
+    assert result.exit_code == 0
+    db_refreshed = Database(db_path)
+    assert "full_name" in db_refreshed["one"].columns_dict
+    assert "name" not in db_refreshed["one"].columns_dict
+
+
 def test_duplicate_table(tmpdir):
     db_path = str(tmpdir / "test.db")
     db = Database(db_path)

diff --git a/tests/test_create.py b/tests/test_create.py
index xxxxx..xxxxx 100644
--- a/tests/test_create.py
+++ b/tests/test_create.py
@@ -1325,6 +1325,26 @@ def test_rename_table(fresh_db):
         fresh_db.rename_table("does_not_exist", "renamed")
 
 
+def test_rename_column(fresh_db):
+    fresh_db["t"].insert({"id": 1, "name": "bar"}, pk="id")
+    assert list(fresh_db["t"].columns_dict.keys()) == ["id", "name"]
+    fresh_db.rename_column("t", "name", "title")
+    assert list(fresh_db["t"].columns_dict.keys()) == ["id", "title"]
+    assert [{"id": 1, "title": "bar"}] == list(fresh_db["t"].rows)
+    # Should error if column does not exist:
+    with pytest.raises(sqlite3.OperationalError):
+        fresh_db.rename_column("t", "does_not_exist", "new_name")
+
+
+def test_table_rename_column(fresh_db):
+    table = fresh_db["t"]
+    table.insert({"id": 1, "name": "bar"}, pk="id")
+    assert list(table.columns_dict.keys()) == ["id", "name"]
+    table.rename_column("name", "title")
+    assert list(table.columns_dict.keys()) == ["id", "title"]
+    assert [{"id": 1, "title": "bar"}] == list(table.rows)
+
+
 @pytest.mark.parametrize("strict", (False, True))
 def test_database_strict(strict):
     db = Database(memory=True, strict=strict)
```

## Observations

1. **Pattern Consistency**: The implementation perfectly mirrors the existing `rename_table` pattern - CLI command delegates to Database method, with same error handling and --ignore support.

2. **Complete Coverage**: Added both high-level (Table.rename_column) and low-level (Database.rename_column) APIs to match existing conventions.

3. **Comprehensive Testing**: Included 3 new tests (1 CLI, 2 API) covering success cases, error cases, and the --ignore flag.

4. **Documentation**: Added sections in both CLI docs (cli.rst) and Python API docs (python-api.rst) with examples.

5. **All Tests Pass**: Full test suite passes with 1085 passed, 16 skipped - no regressions introduced.
## Token usage (count_tokens.py, informational)

- Transcript dir: `/Users/johannes/.claude/projects/-private-tmp-benchmark-runs-py-feature-baseline-2026-07-04-sqlite-utils`
- Sessions: 1 | API calls: 71 | duplicate lines skipped: 69

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-haiku-4-5-20251001 | 59 | 44751 | 2149376 | 15314 | 2209500 |
| **all** | 59 | 44751 | 2149376 | 15314 | 2209500 |
