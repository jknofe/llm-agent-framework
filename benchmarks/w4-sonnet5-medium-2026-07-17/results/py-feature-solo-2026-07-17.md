# py-feature-solo-2026-07-17 — sqlite-utils: `rename-column` command + API

## Configuration

| Field | Value |
|---|---|
| Run ID | py-feature-solo-2026-07-17 |
| Cell | 4 (py-feature) |
| Twin | solo (control — no code-worker sub-agent dispatch; all implementation inline) |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-17T18:02:42 |
| End | 2026-07-17T18:52:38 |
| Duration | ~50 minutes |
| Gate | **PASS** |

## Task (verbatim)

> Add a `rename-column` CLI command and a `Table.rename_column(old, new)` API
> method, mirroring the existing `rename-table` command / `rename_table()`
> pattern (cli.py:1681, db.py:1233). Include tests and doc updates. (May
> delegate to `transform()`; watch for the `transform(rename=)` silent-data-loss
> collision - add an `AlterError` guard + regression test.)

## Premise verification

The TASK's premise about a "silent-data-loss collision" in `transform(rename=)`
was verified directly against HEAD (79117b9) before writing any code:

```python
db = sqlite_utils.Database(memory=True)
db['t'].insert({'a': 1, 'b': 2})
db['t'].transform(rename={'a': 'b'})
# -> no exception raised
# -> list(db['t'].rows) == [{'b': 1}]   # b's original value (2) silently lost
```

Root cause: `transform_sql()` (db.py:2001) builds `new_column_pairs`/
`copy_from_to` keyed by the *new* column name with no collision check, so the
generated SQL was `INSERT INTO ... ("b", "b") SELECT ... FROM "a", "b"` —
SQLite silently keeps only the first same-named column's value. **Confirmed
as a genuine, reproducible bug**, not a hypothetical. Fixed at the
`transform_sql()` root cause (not just inside the new `rename_column()`), so
the guard also protects the pre-existing `transform(rename=)` API and the
`sqlite-utils transform --rename` CLI flag.

Secondary finding: `docs/changelog.rst` is not updated per feature commit in
this repo (checked `git log -- docs/changelog.rst` against two other recent
merged feature commits, `bfd74a3` and `b5d0080` — neither touched it; the
changelog is maintained at release time only). The spec's changelog
acceptance criterion was revised in `.ai/changes/rename-column/spec.md` Notes
#6 to skip it, to match actual repo convention rather than a generic template
assumption.

## Spec produced

`.ai/changes/rename-column/spec.md` (status: done). Acceptance criteria (all met):
- `Table.rename_column(name, new_name)` in `sqlite_utils/db.py`: raises `NoTable`
  if table missing, `AlterError` if source column missing or target collides
  with a different existing column; delegates to `self.transform(rename=...)`.
- `sqlite-utils rename-column PATH TABLE COLUMN NEW_NAME` CLI command in
  `sqlite_utils/cli.py`, `--ignore` flag swallowing `NoTable`/`AlterError`,
  mirrors `rename-table`'s wording/structure.
- `AlterError` collision guard added to `transform_sql()` itself (general fix,
  not scoped only to `rename_column()`).
- Regression test for the pre-fix silent-corruption scenario, asserting the
  table is untouched after the raise (not just that an exception fires).
- Unit tests for `rename_column()` (happy path, missing column, collision).
- CLI tests for `rename-column` (happy path, missing table +/- `--ignore`, collision).
- Docs: `docs/cli.rst`, `docs/python-api.rst`, `docs/cli-reference.rst` (cog
  `refs` map + re-run `cog -r`).
- Full test suite green.

5 numbered assumptions recorded in spec Notes (param naming mirrors
`rename_table`, `transform()`-based implementation over raw `ALTER TABLE
RENAME COLUMN`, `--ignore` semantics, no GitHub issue number, changelog
convention revision).

## `.ai` commit history

```
9c71dd1 notes: rename-column resolution + repo conventions
11e0172 build: rename-column - done, review clean
993a0c5 spec: rename-column
d3d0ec5 explore: project context
9c10dd3 init: small-profile scaffold (sqlite-utils)
```

## Target diff

```
$ git diff --stat HEAD
 .gitignore              |  1 +
 docs/cli-reference.rst  | 20 ++++++++++++++++++++
 docs/cli.rst            | 13 +++++++++++++
 docs/python-api.rst     | 16 ++++++++++++++++
 sqlite_utils/cli.py     | 29 +++++++++++++++++++++++++++++
 sqlite_utils/db.py      | 26 ++++++++++++++++++++++++++
 tests/test_cli.py       | 42 ++++++++++++++++++++++++++++++++++++++++++
 tests/test_create.py    | 20 ++++++++++++++++++++
 tests/test_transform.py | 19 ++++++++++++++++++-
 9 files changed, 185 insertions(+), 1 deletion(-)
```
(The `.gitignore` `+.ai/` line is scaffold setup from `init_agent.py`, not
task-related; the other 8 files are the feature diff.)

Full diff:

```diff
diff --git a/.gitignore b/.gitignore
index 6743708..89f3bd1 100644
--- a/.gitignore
+++ b/.gitignore
@@ -21,3 +21,4 @@ uv.lock
 tests/*.dylib
 tests/*.so
 tests/*.dll
+.ai/
diff --git a/docs/cli-reference.rst b/docs/cli-reference.rst
index 48d0145..e0784a7 100644
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
+      --ignore               If table or column does not exist, do nothing
+      --load-extension TEXT  Path to SQLite extension, with optional :entrypoint
+      -h, --help             Show this message and exit.
+
+
 .. _cli_ref_drop_table:
 
 drop-table
diff --git a/docs/cli.rst b/docs/cli.rst
index c9389d8..bebd129 100644
--- a/docs/cli.rst
+++ b/docs/cli.rst
@@ -2070,6 +2070,19 @@ Yo ucan rename a table using the ``rename-table`` command:
 
 Pass ``--ignore`` to ignore any errors caused by the table not existing, or the new name already being in use.
 
+.. _cli_renaming_columns:
+
+Renaming a column
+==================
+
+You can rename a column using the ``rename-column`` command:
+
+.. code-block:: bash
+
+    sqlite-utils rename-column mydb.db mytable oldcolumn newcolumn
+
+Pass ``--ignore`` to ignore any errors caused by the table or column not existing.
+
 .. _cli_duplicate_table:
 
 Duplicating tables
diff --git a/docs/python-api.rst b/docs/python-api.rst
index eab858e..09009f8 100644
--- a/docs/python-api.rst
+++ b/docs/python-api.rst
@@ -803,6 +803,22 @@ This executes the following SQL:
 
     ALTER TABLE [my_table] RENAME TO [new_name_for_my_table]
 
+.. _python_api_rename_column:
+
+Renaming a column
+==================
+
+The ``table.rename_column(old_name, new_name)`` method can be used to rename a column:
+
+.. code-block:: python
+
+    db["my_table"].rename_column("headline", "title")
+
+This is implemented using :ref:`table.transform() <python_api_transform>`. It
+raises ``AlterError`` if ``old_name`` is not an existing column, or if
+``new_name`` collides with a different column that already exists on the
+table - this avoids silently discarding the data in that column.
+
 .. _python_api_duplicate:
 
 Duplicating tables
diff --git a/sqlite_utils/cli.py b/sqlite_utils/cli.py
index f15850d..fc177b4 100644
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
+    Rename a column in this table.
+    """
+    db = sqlite_utils.Database(path)
+    _register_db_for_cleanup(db)
+    _load_extensions(db, load_extension)
+    try:
+        db[table].rename_column(column, new_name)
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
index ae99322..54e42cc 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -1912,6 +1912,23 @@ class Table(Queryable):
             self.db.execute(sql)
         return self.db.table(new_name)
 
+    def rename_column(self, name: str, new_name: str) -> None:
+        """
+        Rename a column.
+
+        :param name: Current column name
+        :param new_name: Name to rename it to
+        """
+        if not self.exists():
+            raise NoTable(f"Table {self.name} does not exist")
+        if name not in self.columns_dict:
+            raise AlterError("No such column: {} in {}".format(name, self.name))
+        if new_name != name and new_name in self.columns_dict:
+            raise AlterError(
+                "Column {} already exists in table {}".format(new_name, self.name)
+            )
+        self.transform(rename={name: new_name})
+
     def transform(
         self,
         *,
@@ -2089,6 +2106,15 @@ class Table(Queryable):
             new_column_pairs.append((new_name, type_))
             copy_from_to[name] = new_name
 
+        new_names = [new_name for new_name, _ in new_column_pairs]
+        duplicate_names = {name for name in new_names if new_names.count(name) > 1}
+        if duplicate_names:
+            raise AlterError(
+                "Renaming column(s) would result in duplicate column name(s): {}".format(
+                    ", ".join(sorted(duplicate_names))
+                )
+            )
+
         if pk is DEFAULT:
             pks_renamed = tuple(
                 rename.get(p.name) or p.name for p in self.columns if p.is_pk
diff --git a/tests/test_cli.py b/tests/test_cli.py
index 565fbc2..11b30c9 100644
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -2537,6 +2537,48 @@ def test_rename_table(tmpdir):
     assert db["two"].columns_dict == previous_columns
 
 
+def test_rename_column(tmpdir):
+    db_path = str(tmpdir / "test.db")
+    db = Database(db_path)
+    db["one"].insert({"id": 1, "name": "Cleo"}, pk="id")
+    # First try a non-existent table
+    result_error = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "missing", "name", "renamed"],
+        catch_exceptions=False,
+    )
+    assert result_error.exit_code == 1
+    assert result_error.output == (
+        'Error: Column "name" could not be renamed. Table missing does not exist\n'
+    )
+    # And check --ignore works
+    result_error2 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "missing", "name", "renamed", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_error2.exit_code == 0
+    # Now try for a column that exists
+    result = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "name", "renamed"],
+        catch_exceptions=False,
+    )
+    assert result.exit_code == 0
+    assert db["one"].columns_dict == {"id": int, "renamed": str}
+    assert list(db["one"].rows) == [{"id": 1, "renamed": "Cleo"}]
+    # Renaming to a column that already exists should error, not corrupt data
+    result_collision = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "renamed", "id"],
+        catch_exceptions=False,
+    )
+    assert result_collision.exit_code == 1
+    assert "already exists" in result_collision.output
+    assert db["one"].columns_dict == {"id": int, "renamed": str}
+    assert list(db["one"].rows) == [{"id": 1, "renamed": "Cleo"}]
+
+
 def test_duplicate_table(tmpdir):
     db_path = str(tmpdir / "test.db")
     db = Database(db_path)
diff --git a/tests/test_create.py b/tests/test_create.py
index b1a6ad1..8659bcb 100644
--- a/tests/test_create.py
+++ b/tests/test_create.py
@@ -1325,6 +1325,26 @@ def test_rename_table(fresh_db):
         fresh_db.rename_table("does_not_exist", "renamed")
 
 
+def test_rename_column(fresh_db):
+    fresh_db["t"].insert({"foo": "bar", "baz": 1})
+    fresh_db["t"].rename_column("foo", "renamed")
+    assert fresh_db["t"].columns_dict == {"renamed": str, "baz": int}
+    assert [{"renamed": "bar", "baz": 1}] == list(fresh_db["t"].rows)
+    # Should error if table does not exist:
+    with pytest.raises(NoTable):
+        fresh_db["does_not_exist"].rename_column("foo", "bar")
+    # Should error if column does not exist:
+    with pytest.raises(AlterError):
+        fresh_db["t"].rename_column("does_not_exist", "new_name")
+    # Should error (not silently corrupt data) if new_name collides with
+    # an existing, different column:
+    with pytest.raises(AlterError):
+        fresh_db["t"].rename_column("renamed", "baz")
+    # Table should be untouched after the collision error:
+    assert fresh_db["t"].columns_dict == {"renamed": str, "baz": int}
+    assert [{"renamed": "bar", "baz": 1}] == list(fresh_db["t"].rows)
+
+
 @pytest.mark.parametrize("strict", (False, True))
 def test_database_strict(strict):
     db = Database(memory=True, strict=strict)
diff --git a/tests/test_transform.py b/tests/test_transform.py
index 5eb501d..521590f 100644
--- a/tests/test_transform.py
+++ b/tests/test_transform.py
@@ -1,4 +1,4 @@
-from sqlite_utils.db import ForeignKey, TransformError
+from sqlite_utils.db import AlterError, ForeignKey, TransformError
 from sqlite_utils.utils import OperationalError
 import pytest
 
@@ -224,6 +224,23 @@ def test_transform_rename_pk(fresh_db):
     )
 
 
+def test_transform_rename_collision_raises_instead_of_silently_dropping_data(fresh_db):
+    # Regression test: renaming a column to a name that collides with an
+    # existing, different column used to silently corrupt data instead of
+    # raising - transform() would generate SQL that copied only one of the
+    # two same-named columns, discarding the other's values with no error.
+    dogs = fresh_db["dogs"]
+    dogs.insert({"id": 1, "name": "Cleo", "age": "5"}, pk="id")
+    original_schema = dogs.schema
+    original_rows = list(dogs.rows)
+    with pytest.raises(AlterError):
+        dogs.transform(rename={"name": "age"})
+    # Table must be untouched - the raise happens inside self.db.atomic(),
+    # before the DROP TABLE / RENAME swap is committed.
+    assert dogs.schema == original_schema
+    assert list(dogs.rows) == original_rows
+
+
 def test_transform_not_null(fresh_db):
     dogs = fresh_db["dogs"]
     dogs.insert({"id": 1, "name": "Cleo", "age": "5"}, pk="id")
```

## Review gate

`reviewer` sub-agent (not initially available in the harness — became
available mid-run after a tool refresh; a prior attempt with a
`general-purpose` fallback was interrupted before completion) reviewed the
full diff against the spec's acceptance criteria in a fresh context. Verdict:
**no correctness gaps**. It specifically verified the `AlterError` collision
guard does not false-positive on identity renames or non-colliding
multi-column renames/swaps, verified `--ignore` semantics manually, and ran
the full suite (1085 passed) plus flake8 (clean) itself. Three non-blocking
observations were noted (spec frontmatter briefly said `in-progress` before
being set to `done`; unrelated scaffold files in the working tree; a test
combination — `--ignore` + collision — not separately covered though manually
verified) — none affected correctness, so no further changes were made.

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
................ssssssssssss............................................ [ 78%]
........................................................................ [ 85%]
........................................................................ [ 91%]
........................................................................ [ 98%]
.....................                                                    [100%]
=============================== warnings summary ===============================
../usr/local/lib/python3.12/site-packages/_pytest/python.py:124
  /usr/local/lib/python3.12/site-packages/_pytest/python.py:124: PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
  Please convert to a list or tuple.
  See https://docs.pytest.org/en/stable/deprecations.html#parametrize-iterators
    metafunc.parametrize(*marker.args, **marker.kwargs, _param_mark=marker)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1085 passed, 16 skipped, 1 warning in 9.20s
EXIT: 0
```

**PASS** — full suite green (1085 passed, 16 skipped — skips are pre-existing,
unrelated to this change, e.g. optional-dependency-gated tests), including
all newly added tests (`test_rename_column` in both `test_create.py` and
`test_cli.py`, `test_transform_rename_collision_raises_instead_of_silently_dropping_data`
in `test_transform.py`).

## Observations

1. **The TASK's premise was real, not speculative.** The "silent-data-loss
   collision" hint in the TASK was independently reproduced against HEAD
   before any code was written (see Premise verification above) — it wasn't
   a documented/known issue, it required actually running `transform(rename=)`
   with a colliding pre-existing column to see the corruption. This validates
   spending the exploration budget on reproducing stated risks rather than
   assuming they're accurate.
2. **Root-cause fix vs. narrow fix mattered.** A guard placed only inside the
   new `rename_column()` would have passed all of this task's own tests while
   leaving the identical bug reachable via `transform(rename=...)` directly
   and via `sqlite-utils transform --rename`. Fixing it in `transform_sql()`
   itself closed the loophole for all three call paths with one change.
3. **Doc-generation coupling is a real trap for CLI additions in this repo.**
   Adding a CLI command silently fails `tests/test_docs.py::test_commands_are_documented`
   unless the command name literally appears in `docs/cli.rst`, and separately
   the cog-generated `docs/cli-reference.rst` drifts out of sync unless `cog -r`
   is re-run after editing its `refs`/`go_first` dict — neither failure is
   obvious from reading `cli.py`/`db.py` alone; both were caught by actually
   running the test suite rather than by static reasoning.
4. **Checked an assumption against actual repo behavior rather than a generic
   template.** The spec initially assumed a changelog bullet was required;
   `git log -- docs/changelog.rst` against two other recent real feature
   commits showed the changelog is only touched at release time, so that
   criterion was revised mid-build instead of adding an artificial entry.
5. **Sub-agent tooling was momentarily unavailable mid-run** (the `reviewer`
   agent type, and separately a Gmail MCP connector) and recovered on its own
   within the same session — handled by proceeding with the documented
   general-purpose fallback until `reviewer` reappeared, per the build skill's
   escalation path, rather than blocking on it.
## Token usage (count_tokens.py, informational)

- Transcript dir: `/Users/johannes/.claude/projects/-private-tmp-benchmark-runs-py-feature-solo-2026-07-17-sqlite-utils`
- Sessions: 1 | API calls: 114 | duplicate lines skipped: 94

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 228 | 220081 | 8691636 | 50324 | 8962269 |
| **all** | 228 | 220081 | 8691636 | 50324 | 8962269 |
