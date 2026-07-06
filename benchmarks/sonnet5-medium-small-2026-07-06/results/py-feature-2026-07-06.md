# Benchmark run: py-feature-2026-07-06 (sqlite-utils)

## Configuration

| Field | Value |
|---|---|
| Run ID | py-feature-2026-07-06 |
| Cell | sqlite-utils / rename-column feature |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-06T16:50:58 |
| End | 2026-07-06T17:07:25 |
| Duration | ~16m27s |
| Gate PASS/FAIL | **PASS** |

## Auto-size line

`--size small` was passed explicitly to `init_agent.py`, so the auto-size
estimator is skipped in that code path (no line printed). Computed
separately for the record:

```
auto-size: 20868 lines of code -> large profile
```

i.e. the repo's own heuristic would have recommended the **large** profile;
this run was deliberately pinned to **small** per the task instructions.
Framework files reflect the small profile throughout. Recorded as a gotcha
in `.ai/notes.md`.

## Spec produced

`.ai/changes/rename-column/spec.md` (status: done). Full text:

```markdown
---
id: rename-column
title: Add rename-column CLI command and Table.rename_column() API method
status: done
created: 2026-07-06
---

## Goal

Add a way to rename a single column on an existing table, both from the
Python API (`Table.rename_column(old_name, new_name)`) and the CLI
(`sqlite-utils rename-column PATH TABLE COLUMN NEW_COLUMN`), mirroring the
existing table-rename feature (`Database.rename_table()` at `db.py:1233`,
`sqlite-utils rename-table` command at `cli.py:1681`). Users currently must
reach for the much heavier `Table.transform(rename={...})` (a full
copy-and-rebuild of the table) just to rename one column; a thin, native
`ALTER TABLE ... RENAME COLUMN` wrapper is cheaper, atomic, and matches how
`rename_table` itself is implemented (a single `ALTER TABLE` statement, not a
`transform()` delegation).

## Premise verification

- `Database.rename_table` (`db.py:1233`): `self.execute("ALTER TABLE {} RENAME TO {}".format(quote_identifier(name), quote_identifier(new_name)))`.
  No existence pre-check; relies on SQLite raising `sqlite3.OperationalError`
  for a missing table.
- `rename-table` CLI command (`cli.py:1681`): `@cli.command(name="rename-table")`,
  args `path`, `table`, `new_name`, `--ignore` flag, `@load_extension_option`.
  Catches `sqlite3.OperationalError`, raises `click.ClickException` unless
  `--ignore`.
- Confirmed empirically (`python3 -c ...` against stdlib sqlite3 3.53.2) that
  native `ALTER TABLE t RENAME COLUMN a TO b` already raises
  `sqlite3.OperationalError` for: missing column ("no such column"), missing
  table ("no such table"), and - critically - a new name that collides with
  an existing column ("duplicate column name: b"). So a `rename_table`-style
  raw-SQL implementation of `rename_column` is safe from silent data loss by
  construction; no additional guard is needed in the new method itself.
- **Bug found while checking the sibling delegation path the task asked to
  watch for**: `Table.transform()` / `Table.transform_sql()` (`db.py:1915`,
  `db.py:2001`), which accepts a `rename: Optional[dict]` and is the
  alternative implementation strategy for column renames, does NOT guard
  against a rename target colliding with another column that is left
  unchanged (or with another simultaneous rename target). Repro: table with
  columns `id, name, email`; `table.transform(rename={"name": "email"})`
  builds `CREATE TABLE ... (id ..., email ...)` (the untouched `email`
  column's type silently overwritten by dict-collapse) plus
  `INSERT INTO new (id, email, email) SELECT id, name, email FROM old`,
  which SQLite executes without error, silently discarding one of the two
  values that map to `email`. Verified with a minimal stdlib-sqlite3 repro:
  the INSERT succeeds silently and only one value per duplicated target
  survives - real, silent data loss, not merely an ambiguous read. No
  existing test in `tests/test_create.py` exercises a colliding `rename`.
  Since this repo's `rename_column` will not delegate to `transform()`, the
  new method is unaffected, but the underlying bug is real, adjacent to this
  feature, and directly matches the collision class the task asked to check
  for - fixing it is in scope for this change (small, well-isolated guard +
  regression test in `transform_sql`, not a redesign).

## Acceptance criteria

- [x] `Table.rename_column(old_name: str, new_name: str) -> None` exists in
      `sqlite_utils/db.py`, implemented as a single
      `ALTER TABLE ... RENAME COLUMN ... TO ...` statement via
      `self.db.execute(...)` (mirrors `rename_table`'s raw-SQL style, no
      `transform()` delegation), with a `:param:`-style docstring.
- [x] `sqlite-utils rename-column PATH TABLE COLUMN NEW_COLUMN` CLI command
      exists in `sqlite_utils/cli.py`, mirroring `rename-table`: same
      argument shape (`path`, `table`, then old/new names), `--ignore` flag
      (do nothing if the rename fails), `@load_extension_option`, catches
      `sqlite3.OperationalError` and raises `click.ClickException` with a
      formatted message unless `--ignore`.
- [x] `Table.transform_sql()` raises `TransformError` (not silent data loss)
      when the `rename` dict's targets collide with each other or with an
      untouched/kept column name, instead of quietly dropping data. Existing
      valid uses of `rename` (no collisions) are unaffected.
- [x] Python API tests in `tests/test_create.py`: happy path (rename via
      `Table.rename_column`, data preserved, `columns_dict` updated),
      missing-column error (`sqlite3.OperationalError`), missing-table error,
      new-name-collides-with-existing-column error (regression test for the
      guard above, both via `rename_column`'s native path and directly via
      `transform(rename=...)` to prove the `transform_sql` guard fires).
- [x] CLI tests in `tests/test_cli.py` mirroring `test_rename_table`: error
      + exact message for missing column, `--ignore` swallows the error,
      success path renames and preserves data/other columns.
- [x] Docs updated: `docs/python-api.rst` new `.. _python_api_rename_column:`
      section (mirrors `python_api_rename_table`, includes the executed SQL);
      `docs/cli.rst` new `.. _cli_renaming_columns:` section (mirrors
      `cli_renaming_tables`) under/near the existing renaming-a-table
      section; `docs/cli-reference.rst` `refs` dict gets a
      `"rename-column": "cli_renaming_columns"` entry, file regenerated via
      `cog` if the toolchain is available (else hand-edited to match the
      `--help` output exactly, matching the format used by `duplicate` /
      `rename-table` entries); `docs/changelog.rst` gets a bullet in the
      Unreleased/top section mirroring the `rename_table` changelog entries.
- [x] `python -m pytest -q` passes (full suite, including new tests) inside
      the `python:3.12` Docker gate described in the runbook.
- [x] `flake8` / `black --check` / `mypy sqlite_utils tests` pass if the
      lint toolchain is available locally (recorded, non-gating per the
      benchmark runbook; the Docker gate container does not have `uv`/lint
      deps installed).

## Tasks

- [x] Add `Table.rename_column` to `sqlite_utils/db.py` (near
      `rename_table`/`transform`) - files: `sqlite_utils/db.py`
- [x] Add `TransformError` guard for colliding rename targets to
      `Table.transform_sql` - files: `sqlite_utils/db.py`
- [x] Add `rename-column` CLI command to `sqlite_utils/cli.py` (near
      `rename-table`) - files: `sqlite_utils/cli.py`
- [x] Python API tests - files: `tests/test_create.py`
- [x] CLI tests - files: `tests/test_cli.py`
- [x] Docs: python-api, cli narrative, cli-reference, changelog - files:
      `docs/python-api.rst`, `docs/cli.rst`, `docs/cli-reference.rst`,
      `docs/changelog.rst`
- [x] Review diff against acceptance criteria (reviewer sub-agent or
      documented self-review)
- [x] Run Docker pytest gate, record output: `python:3.12` container,
      `pip install -e . pytest hypothesis && python -m pytest -q` ->
      1087 passed, 16 skipped, 0 failed, EXIT: 0. PASS.

## Notes

Assumptions (autonomous run, no human available - resolved from code
evidence):

1. `rename_column` lives on `Table`, not `Database` (per the task's literal
   API name `Table.rename_column(old, new)`), even though the mirrored
   `rename_table` lives on `Database`. This is consistent with the codebase:
   table-scoped structural ops (`transform`, `duplicate`, `create_index`,
   `add_column`) already live on `Table`; only whole-database ops
   (`rename_table`, `create_view`, `create_table`) live on `Database`.
   Renaming one column is table-scoped, so `Table` is correct.
2. Implementation strategy is raw `ALTER TABLE ... RENAME COLUMN`, not
   `transform(rename=...)` delegation - chosen because (a) it mirrors the
   literal pattern the task named (`rename_table`'s raw-SQL style), (b) it is
   verified safe against the collision class the task warned about, without
   needing extra guard code in the new method, and (c) it is cheap
   (no table rebuild) vs. `transform()`'s full copy.
3. CLI argument order: `PATH TABLE COLUMN NEW_COLUMN` (table name before old
   column name before new column name), mirroring `rename-table PATH TABLE
   NEW_NAME`'s `path, table, new_name` shape extended by one argument.
4. The `--ignore` flag on the new CLI command swallows any
   `sqlite3.OperationalError` from the rename (missing table, missing
   column, or name collision alike) - this exactly mirrors `rename-table`'s
   existing `--ignore` semantics (it also swallows any `OperationalError`,
   not just "table missing"), so it is not a new, narrower design; consistent
   behavior across both commands was preferred over inventing a stricter
   variant for only the new command.
5. The `transform_sql` collision guard is scoped narrowly: raise
   `TransformError` only when two distinct source columns would resolve to
   the same final column name after rename/keep (i.e. an actual collision),
   not a broader schema-validation pass. This matches the existing
   `TransformError` usage style in the same function (index-column
   collisions) and keeps the fix minimal and low-risk.
```

## `.ai` commit history

```
0efe81e 2026-07-06 17:07:05 +0200  gate: docker pytest PASS (1087 passed, 16 skipped)
0cc4996 2026-07-06 17:06:19 +0200  build: rename-column
a1afc1b 2026-07-06 16:56:10 +0200  spec: rename-column
3209c0f 2026-07-06 16:54:59 +0200  explore: project context (sqlite-utils)
ea24bfe 2026-07-06 16:51:05 +0200  init: small-profile scaffold (sqlite-utils)
```

## Premise-verification finding (planted-bug check)

The task explicitly asked to watch for a silent-data-loss collision if the
new feature delegated to an existing `transform()`-style method with a
`rename` argument. Investigation found:

- `Table.transform()` / `Table.transform_sql()` (`sqlite_utils/db.py:1915`
  and `:2001` pre-change) accepts `rename: Optional[dict]` and, before this
  change, did **not** validate that a rename target collides with another
  surviving column. Repro (verified against stdlib sqlite3 3.53.2, table
  `id, name, email`): `table.transform(rename={"name": "email"})` builds
  `CREATE TABLE new (id .., email ..)` (dict-collapse silently drops one
  column definition) and
  `INSERT INTO new (id, email, email) SELECT id, name, email FROM old`
  (duplicate target column in the INSERT list). SQLite executes this
  **without raising an error** and silently keeps only one of the two source
  values - genuine, silent data loss, reproduced directly against a raw
  `sqlite3.connect(":memory:")` connection before touching any
  sqlite-utils code.
- Chosen implementation for the new feature (`rename_column` = raw
  `ALTER TABLE ... RENAME COLUMN`, mirroring `rename_table`'s own style
  rather than delegating to `transform()`) is **not** exposed to this bug:
  native SQLite already raises `sqlite3.OperationalError` (`duplicate
  column name: ...`) for a colliding native `RENAME COLUMN`, verified
  empirically.
- Because the collision class is real, pre-existing, and directly adjacent
  to this feature, a `TransformError` guard was added to `transform_sql()`
  (raises before any SQL is built/executed when two source columns would
  resolve to the same final name) plus three regression tests in
  `tests/test_transform.py` covering: collision with an untouched column,
  collision between two simultaneous rename targets, and a false-positive
  check (a legitimate two-column name swap must NOT trip the guard).

## Target diff

`git diff --stat HEAD`:

```
 .gitignore              |  1 +
 docs/changelog.rst      |  6 ++++++
 docs/cli-reference.rst  | 20 ++++++++++++++++++++
 docs/cli.rst            | 13 +++++++++++++
 docs/python-api.rst     | 17 +++++++++++++++++
 sqlite_utils/cli.py     | 27 +++++++++++++++++++++++++++
 sqlite_utils/db.py      | 34 ++++++++++++++++++++++++++++++++++
 tests/test_cli.py       | 48 ++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_create.py    | 23 +++++++++++++++++++++++
 tests/test_transform.py | 45 +++++++++++++++++++++++++++++++++++++++++++++
 10 files changed, 234 insertions(+)
```

(`.gitignore`'s `+.ai/` line is scaffold hygiene from Step 1 `init_agent.py`,
not part of the feature; called out by the reviewer sub-agent as a minor
scope note, confirmed harmless.)

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
diff --git a/docs/changelog.rst b/docs/changelog.rst
index 765b0e0..4329859 100644
--- a/docs/changelog.rst
+++ b/docs/changelog.rst
@@ -4,6 +4,12 @@
  Changelog
 ===========
 
+Unreleased
+----------
+
+- New ``table.rename_column(old_name, new_name)`` method for renaming a column.
+- ``sqlite-utils rename-column my.db table_name old_name new_name`` command for renaming a column.
+
 .. _v4_0rc1:
 
 4.0rc1 (2026-06-21)
diff --git a/docs/cli-reference.rst b/docs/cli-reference.rst
index 48d0145..d06f447 100644
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
+    Usage: sqlite-utils rename-column [OPTIONS] PATH TABLE COLUMN NEW_COLUMN
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
index c9389d8..77a8721 100644
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
+    sqlite-utils rename-column mydb.db mytable oldcolumn newcolumn
+
+Pass ``--ignore`` to ignore any errors caused by the column not existing, or the new name already being in use by another column.
+
 .. _cli_duplicate_table:
 
 Duplicating tables
diff --git a/docs/python-api.rst b/docs/python-api.rst
index eab858e..abb94d8 100644
--- a/docs/python-api.rst
+++ b/docs/python-api.rst
@@ -803,6 +803,23 @@ This executes the following SQL:
 
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
+This executes the following SQL:
+
+.. code-block:: sql
+
+    ALTER TABLE [my_table] RENAME COLUMN [headline] TO [title]
+
 .. _python_api_duplicate:
 
 Duplicating tables
diff --git a/sqlite_utils/cli.py b/sqlite_utils/cli.py
index f15850d..893d3b1 100644
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
+@click.argument("new_column")
+@click.option("--ignore", is_flag=True, help="If column does not exist, do nothing")
+@load_extension_option
+def rename_column(path, table, column, new_column, ignore, load_extension):
+    """
+    Rename a column in this table.
+    """
+    db = sqlite_utils.Database(path)
+    _register_db_for_cleanup(db)
+    _load_extensions(db, load_extension)
+    try:
+        db[table].rename_column(column, new_column)
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
index ae99322..0edaa84 100644
--- a/sqlite_utils/db.py
+++ b/sqlite_utils/db.py
@@ -1912,6 +1912,21 @@ class Table(Queryable):
             self.db.execute(sql)
         return self.db.table(new_name)
 
+    def rename_column(self, old_name: str, new_name: str) -> None:
+        """
+        Rename a column in this table.
+
+        :param old_name: Current column name
+        :param new_name: Name to rename it to
+        """
+        self.db.execute(
+            "ALTER TABLE {} RENAME COLUMN {} TO {}".format(
+                quote_identifier(self.name),
+                quote_identifier(old_name),
+                quote_identifier(new_name),
+            )
+        )
+
     def transform(
         self,
         *,
@@ -2089,6 +2104,25 @@ class Table(Queryable):
             new_column_pairs.append((new_name, type_))
             copy_from_to[name] = new_name
 
+        # Guard against a rename target colliding with another surviving
+        # column (renamed or not) - without this check the CREATE TABLE and
+        # INSERT statements built below would silently collapse two columns
+        # into one, discarding data with no error raised.
+        seen_names: Dict[str, str] = {}
+        for original_name, (final_name, _) in zip(
+            (name for name, _ in current_column_pairs if name not in drop),
+            new_column_pairs,
+        ):
+            if final_name in seen_names:
+                raise TransformError(
+                    "Cannot transform table '{}': columns '{}' and '{}' would "
+                    "both be named '{}' after this transform. Rename or drop "
+                    "one of them first.".format(
+                        self.name, seen_names[final_name], original_name, final_name
+                    )
+                )
+            seen_names[final_name] = original_name
+
         if pk is DEFAULT:
             pks_renamed = tuple(
                 rename.get(p.name) or p.name for p in self.columns if p.is_pk
diff --git a/tests/test_cli.py b/tests/test_cli.py
index 565fbc2..5fc5893 100644
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -2537,6 +2537,54 @@ def test_rename_table(tmpdir):
     assert db["two"].columns_dict == previous_columns
 
 
+def test_rename_column(tmpdir):
+    db_path = str(tmpdir / "test.db")
+    db = Database(db_path)
+    db["one"].insert({"id": 1, "name": "Cleo"}, pk="id")
+    # First try a non-existent column
+    result_error = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "missing", "renamed"],
+        catch_exceptions=False,
+    )
+    assert result_error.exit_code == 1
+    assert result_error.output == (
+        'Error: Column "missing" could not be renamed. ' 'no such column: ""missing""\n'
+    )
+    # And check --ignore works
+    result_error2 = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "missing", "renamed", "--ignore"],
+        catch_exceptions=False,
+    )
+    assert result_error2.exit_code == 0
+    previous_rows = list(db["one"].rows)
+    # Now try for a column that exists
+    result = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "one", "name", "renamed"],
+        catch_exceptions=False,
+    )
+    assert result.exit_code == 0
+    assert list(db["one"].columns_dict.keys()) == ["id", "renamed"]
+    assert [{"id": r["id"], "renamed": r["name"]} for r in previous_rows] == list(
+        db["one"].rows
+    )
+    # Renaming to a name that collides with an existing column should error,
+    # not silently drop data
+    db["two"].insert({"id": 1, "name": "Cleo", "email": "cleo@example.com"}, pk="id")
+    result_collision = CliRunner().invoke(
+        cli.cli,
+        ["rename-column", db_path, "two", "name", "email"],
+        catch_exceptions=False,
+    )
+    assert result_collision.exit_code == 1
+    assert "could not be renamed" in result_collision.output
+    assert list(db["two"].rows) == [
+        {"id": 1, "name": "Cleo", "email": "cleo@example.com"}
+    ]
+
+
 def test_duplicate_table(tmpdir):
     db_path = str(tmpdir / "test.db")
     db = Database(db_path)
diff --git a/tests/test_create.py b/tests/test_create.py
index b1a6ad1..eed8d34 100644
--- a/tests/test_create.py
+++ b/tests/test_create.py
@@ -1325,6 +1325,29 @@ def test_rename_table(fresh_db):
         fresh_db.rename_table("does_not_exist", "renamed")
 
 
+def test_rename_column(fresh_db):
+    fresh_db["t"].insert({"foo": "bar"})
+    assert ["foo"] == list(fresh_db["t"].columns_dict.keys())
+    fresh_db["t"].rename_column("foo", "renamed")
+    assert ["renamed"] == list(fresh_db["t"].columns_dict.keys())
+    assert [{"renamed": "bar"}] == list(fresh_db["t"].rows)
+    # Should error if column does not exist:
+    with pytest.raises(sqlite3.OperationalError):
+        fresh_db["t"].rename_column("does_not_exist", "renamed2")
+    # Should error if table does not exist:
+    with pytest.raises(sqlite3.OperationalError):
+        fresh_db["does_not_exist"].rename_column("foo", "renamed2")
+    # Should error, not silently corrupt data, if new_name collides with an
+    # existing column:
+    fresh_db["t2"].insert({"id": 1, "name": "Cleo", "email": "cleo@example.com"})
+    with pytest.raises(sqlite3.OperationalError):
+        fresh_db["t2"].rename_column("name", "email")
+    # Original data should be untouched
+    assert list(fresh_db["t2"].rows) == [
+        {"id": 1, "name": "Cleo", "email": "cleo@example.com"}
+    ]
+
+
 @pytest.mark.parametrize("strict", (False, True))
 def test_database_strict(strict):
     db = Database(memory=True, strict=strict)
diff --git a/tests/test_transform.py b/tests/test_transform.py
index 5eb501d..6599740 100644
--- a/tests/test_transform.py
+++ b/tests/test_transform.py
@@ -659,3 +659,48 @@ def test_transform_with_unique_constraint_implicit_index(fresh_db):
         "You must manually drop this index prior to running this transformation and manually recreate the new index after running this transformation."
         in str(excinfo.value)
     )
+
+
+def test_transform_rename_collision_with_existing_column_errors(fresh_db):
+    # Regression test: renaming a column to the name of another, untouched
+    # column used to silently corrupt data instead of raising an error - the
+    # CREATE TABLE for the new table would silently collapse the two columns
+    # into one (dict overwrite) and the copy INSERT would list the same
+    # target column twice, which SQLite executes without complaint, keeping
+    # only one of the two original values.
+    people = fresh_db["people"]
+    people.insert({"id": 1, "name": "Cleo", "email": "cleo@example.com"}, pk="id")
+
+    with pytest.raises(TransformError) as excinfo:
+        people.transform(rename={"name": "email"})
+
+    assert "columns 'name' and 'email' would both be named 'email'" in str(
+        excinfo.value
+    )
+    # No data should have been touched - original table is untouched
+    assert people.columns_dict == {"id": int, "name": str, "email": str}
+    assert list(people.rows) == [{"id": 1, "name": "Cleo", "email": "cleo@example.com"}]
+
+
+def test_transform_rename_collision_between_two_renamed_columns_errors(fresh_db):
+    people = fresh_db["people"]
+    people.insert({"id": 1, "first": "Cleo", "last": "Cat"}, pk="id")
+
+    with pytest.raises(TransformError) as excinfo:
+        people.transform(rename={"first": "full_name", "last": "full_name"})
+
+    assert "would both be named 'full_name'" in str(excinfo.value)
+
+
+def test_transform_rename_swap_two_columns_is_not_a_false_positive_collision(
+    fresh_db,
+):
+    # A rename that swaps two columns' names is legitimate - the final name
+    # sets don't actually collide - and must not trip the collision guard.
+    people = fresh_db["people"]
+    people.insert({"id": 1, "a": "A-value", "b": "B-value"}, pk="id")
+
+    people.transform(rename={"a": "b", "b": "a"})
+
+    assert people.columns_dict == {"id": int, "a": str, "b": str}
+    assert list(people.rows) == [{"id": 1, "a": "B-value", "b": "A-value"}]
```

## Review gate

Spawned the `reviewer` sub-agent (fresh context) with only the diff + spec
acceptance criteria. Verdict: **PASS**. It traced the collision-guard logic
by hand for four cases (untouched-column collision, two-rename-target
collision, legitimate swap false-positive check, interaction with `drop`)
and confirmed all four behave correctly; it ran the test suite, flake8,
black, and mypy independently and confirmed all green. One non-blocking
note: the `.gitignore` `+.ai/` line is scaffold hygiene, not feature scope
(confirmed correct/expected: it's the Step-1 `init_agent.py` scaffold, not
introduced during the build step).

## Full gate output (Docker: `python:3.12`)

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
................ssssssssssss............................................ [ 78%]
........................................................................ [ 84%]
........................................................................ [ 91%]
........................................................................ [ 97%]
.......................                                                  [100%]
=============================== warnings summary ===============================
../usr/local/lib/python3.12/site-packages/_pytest/python.py:124
  /usr/local/lib/python3.12/site-packages/_pytest/python.py:124: PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
  Please convert to a list or tuple.
  See https://docs.pytest.org/en/stable/deprecations.html#parametrize-iterators
    metafunc.parametrize(*marker.args, **marker.kwargs, _param_mark=marker)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1087 passed, 16 skipped, 1 warning in 8.46s
EXIT: 0
```

**Result: PASS** - 1087 passed, 16 skipped, 0 failed, exit code 0.

### Lint (recorded, not gating per runbook - Docker gate image has no `uv`/lint deps)

Run locally in a venv with `black`, `flake8`, `mypy`, `codespell`, `cogapp`
installed:

- `black . --check` (after auto-formatting the two touched test files) - clean.
- `flake8` - clean, no output.
- `mypy sqlite_utils tests` - "Success: no issues found in ... source files".
- `cog --check README.md docs/*.rst` - clean, all files up to date (the
  `docs/cli-reference.rst` change was produced by actually running
  `cog -r docs/cli-reference.rst`, not by hand-editing the generated block).
- `codespell docs/*.rst --ignore-words docs/codespell-ignore-words.txt` -
  clean, no output.

## Observations

1. **Planted-bug detection worked as intended.** The task's warning about a
   "silent-data-loss collision if you delegate to a transform()-style
   method" pointed at a real, reproducible bug in `Table.transform_sql()`
   that predates this change and has no existing test coverage. Verifying
   it empirically (a 10-line raw-sqlite3 repro) before touching any
   sqlite-utils code was decisive - it turned a vague warning into a
   concrete, testable fact and a design decision (avoid `transform()`
   delegation entirely; separately patch the sibling method since it's
   real and in-scope).
2. **Mirroring beats inventing.** Every design question (which class the
   method lives on, CLI argument order, `--ignore` semantics, error-message
   format, doc anchor naming, changelog style) was resolved by reading the
   exact code/docs being mirrored rather than picking a "cleaner" design -
   this kept the diff minimal (10 files, 234 insertions) and consistent
   with existing conventions, and made review fast (single-pass PASS).
3. **`cog`-generated docs are a real trap for hand-edits.** `docs/cli-reference.rst`
   is machine-generated from live `--help` output; the test suite
   (`test_docs.py::test_commands_are_documented`) independently enforces
   that every CLI command appears in `docs/cli.rst`/`plugins.rst` via a
   regex over code blocks - a doc update that only touched narrative prose
   would have passed a naive review but failed the actual test suite. Both
   gaps were only caught by actually running the full local test suite
   before the Docker gate, not by trusting the acceptance criteria as
   already satisfied on paper.
4. **The auto-size mismatch (large vs. pinned small) is a persistent
   condition of this benchmark cell**, not a one-time note: the repo is
   ~21k LOC and will keep recommending "large" every time `/explore` or
   `probe.py` runs. Recorded once in `.ai/notes.md` and in AGENTS.md's
   project-context rather than re-flagging it at every step, per the build
   skill's guidance to propose-not-migrate and avoid repeated noise.
5. **`--ignore` on both rename commands is intentionally broad** (swallows
   *any* `sqlite3.OperationalError`, not just "not found" errors) - this is
   inherited, pre-existing behavior from `rename-table`, kept identical for
   `rename-column` rather than narrowed, since introducing an inconsistency
   between two structurally-identical commands would be a bigger design
   smell than the (pre-existing, documented) broad catch.

## Token usage (count_tokens.py, informational)

Note: reviewer sub-agent is a sibling transcript (spawnDepth 2), counted
separately and added per the runbook rule ("reviewer cost stays in").

Main agent (`agent-aa4a071dc0a98de75.jsonl`):

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 272 | 141280 | 10631054 | 10340 | 10782946 |

Reviewer sub-agent (`agent-a9ede73f386b43a3b.jsonl`, "Review rename-column diff against spec"):

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 44 | 35305 | 620551 | 1826 | 657726 |

**Combined total (framework price, incl. reviewer): 11,440,672 tokens**
(input 316, cache write 176585, cache read 11251605, output 12166)
