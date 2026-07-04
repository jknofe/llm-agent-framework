# Benchmark Result: py-feature-s5m-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | py-feature-s5m-2026-07-03 |
| Cell | sqlite-utils rename-column (py-feature) |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-03T20:23:05 |
| End | 2026-07-04T03:52:40 |
| Duration | wall-clock ~7h30m spanning a session-limit reset (idle gap); active working time was a fraction of that |
| Gate | PASS (1086 passed, 16 skipped, EXIT 0) |

## Task

Add a `rename-column` CLI command and a `Table.rename_column(old, new)` API
method, mirroring the existing `rename-table` command / `rename_table()` pattern
(cli.py:1681, db.py:1233). Include tests and doc updates. Watch the
`transform(rename=)` silent-data-loss collision; add an `AlterError` guard +
regression test.

## Spec / plan produced

`.ai/changes/rename-column/spec.md` (status: done). Goal: add `rename-column`
CLI + `Table.rename_column(column, new_name)` API, preserving data and never
silently clobbering a column. Acceptance criteria covered the API method
(rename+preserve+chainable), the two `AlterError` guard cases (missing column,
name collision), the CLI command with `--ignore` parity, the five new tests,
full pytest green, `flake8` clean, and doc updates (python-api.rst, cli.rst,
cli-reference.rst cog, changelog).

Six numbered assumptions recorded in the spec Notes (autonomous run, no human):
1. Use native `ALTER TABLE ... RENAME COLUMN` (the true structural mirror of
   `rename_table`'s native `ALTER TABLE ... RENAME TO`), not `transform()`.
2. `transform(rename=)` collision verified empirically to silently drop the
   target column; we avoid that path AND add a pre-mutation guard + regression.
3. Missing-column pre-check raises clean `AlterError` (matches Table API style).
4. Param names `column`, `new_name` (positionally old/new) to match codebase.
5. CLI catches `(AlterError, sqlite3.OperationalError)`, `--ignore` swallows,
   error message mirrors rename-table.
6. cli-reference.rst is cog-generated; added `refs` entry + `cli_renaming_columns`
   anchor and regenerated with cog.

## .ai commit history

```
ff17f03 build: rename-column
66a75b2 spec: rename-column
1278d90 explore: project context
f2fb0c0 init: small-profile scaffold (sqlite-utils)
```

## Target diff (git diff --stat HEAD)

```
 .gitignore             |  1 +   (scaffold: adds .ai/)
 docs/changelog.rst     |  1 +
 docs/cli-reference.rst | 24 ++++++++++++++++++++++++   (cog-regenerated)
 docs/cli.rst           | 13 +++++++++++++
 docs/python-api.rst    | 22 ++++++++++++++++++++++
 sqlite_utils/cli.py    | 36 ++++++++++++++++++++++++++++++++++++
 sqlite_utils/db.py     | 30 ++++++++++++++++++++++++++++++
 tests/test_cli.py      | 41 +++++++++++++++++++++++++++++++++++++++++
 tests/test_create.py   | 33 +++++++++++++++++++++++++++++++++
 9 files changed, 201 insertions(+)
```

### Full diff

#### sqlite_utils/db.py — Table.rename_column

```python
    def rename_column(self, column: str, new_name: str) -> "Table":
        """
        Rename a column on this table.

        This uses SQLite's native ``ALTER TABLE ... RENAME COLUMN`` and so
        preserves all row data, indexes and constraints.

        :param column: Current column name
        :param new_name: Name to rename it to
        """
        if column not in self.columns_dict:
            raise AlterError("No such column: {}".format(column))
        # Guard against silently clobbering an existing column - renaming onto
        # a name already used by a different column would lose that column's
        # data (this is the trap that ``transform(rename=)`` falls into).
        if new_name != column and new_name in self.columns_dict:
            raise AlterError(
                "Cannot rename column {} to {}: column {} already exists".format(
                    column, new_name, new_name
                )
            )
        self.db.execute(
            "ALTER TABLE {} RENAME COLUMN {} TO {}".format(
                quote_identifier(self.name),
                quote_identifier(column),
                quote_identifier(new_name),
            )
        )
        return self
```

#### sqlite_utils/cli.py — rename-column command

```python
@cli.command(name="rename-column")
@click.argument("path", type=click.Path(file_okay=True, dir_okay=False, allow_dash=False), required=True)
@click.argument("table")
@click.argument("column")
@click.argument("new_name")
@click.option("--ignore", is_flag=True, help="If table or column does not exist, do nothing")
@load_extension_option
def rename_column(path, table, column, new_name, ignore, load_extension):
    """
    Rename a column in the specified table.

    Example:

    \b
        sqlite-utils rename-column chickens.db chickens name title
    """
    db = sqlite_utils.Database(path)
    _register_db_for_cleanup(db)
    _load_extensions(db, load_extension)
    try:
        db[table].rename_column(column, new_name)
    except (AlterError, sqlite3.OperationalError) as ex:
        if not ignore:
            raise click.ClickException(
                'Column "{}" could not be renamed. {}'.format(column, str(ex))
            )
```

#### tests

- tests/test_create.py: `test_rename_column` (rename preserves data + returns
  self), `test_rename_column_missing_column` (AlterError, table unchanged),
  `test_rename_column_collision_does_not_lose_data` (rename `age`->`name` raises
  AlterError, both columns + values intact).
- tests/test_cli.py: `test_rename_column` (missing-column error message,
  `--ignore` swallow, collision -> exit 1 with table unchanged, success +
  data preserved).

#### docs

- docs/python-api.rst: new "Renaming a column" section (`python_api_rename_column`).
- docs/cli.rst: new "Renaming a column" section (`cli_renaming_columns`).
- docs/cli-reference.rst: `refs` entry + cog-regenerated `rename-column --help`.
- docs/changelog.rst: changelog line under 4.0rc1.

(Full unified diff also saved at
/tmp/benchmark/runs/py-feature-s5m-2026-07-03/full-diff.txt)

## Premise / collision finding

**Confirmed the `transform(rename=)` silent-data-loss collision empirically.**
`db['t'].transform(rename={'age':'name'})` where a `name` column already exists
silently DROPS the original `name` column and keeps the renamed value, with no
error: `{id,age,name}` -> `{id,name}` where `name` now holds the old `age`
value. Also found `transform(rename={...})` with a non-existent source column is
a silent no-op.

**How it was handled:** `rename_column` uses native `ALTER TABLE ... RENAME
COLUMN` (not `transform`), so the data-loss path is avoided entirely. On top of
that, an explicit pre-mutation `AlterError` guard rejects renaming onto the name
of an existing distinct column (and rejects a missing source column), so a
future refactor to `transform` cannot reintroduce the loss. A regression test
(`test_rename_column_collision_does_not_lose_data`) asserts the guard fires and
that both columns and both values remain intact. Note: native SQLite is itself
doubly safe here (`RENAME COLUMN a TO b` aborts with a duplicate-column
OperationalError), but the guard converts that to a clean `AlterError` before
any mutation.

## Review gate

Reviewer sub-agent (harness `reviewer` not spawnable via the SDK Agent tool);
used a fresh general-purpose sub-agent given only the diff + acceptance
criteria. Verdict: **PASS**, all six criteria met, no correctness bugs in the
guard, SQL-injection surface (all identifiers via `quote_identifier`), or the
rename-to-self / collision edge cases. One minor out-of-scope note:
`columns_dict` membership is case-sensitive while SQLite column names are
case-insensitive (no data risk; not required by criteria).

## Full gate output (STEP 5)

Command:
```
docker run --rm -v "$WORK_DIR":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis && python -m pytest -q; echo "EXIT: $?"'
```

Output (tail):
```
........................................................................ [ 98%]
......................                                                   [100%]
=============================== warnings summary ===============================
  PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is
  deprecated. (pre-existing, tests/test_sniff.py)
1086 passed, 16 skipped, 1 warning in 8.96s
EXIT: 0
```

**Gate: PASS** — full suite green including the five new tests. EXIT 0.

## Repo-configured lint (non-gating)

`flake8 sqlite_utils/ tests/` (config: pyproject `[tool.flake8]`, max-line 160)
-> exit 0, clean.

## Observations

1. The task's "you may delegate to `transform()`" framing is a trap: the true
   structural mirror of `rename_table` (native `ALTER TABLE RENAME TO`) is
   native `ALTER TABLE RENAME COLUMN`, which sidesteps the flagged data-loss
   entirely. Choosing the native path made the AlterError guard a belt-and-
   suspenders safeguard rather than the sole defense.
2. Empirically verifying the collision (rather than trusting the note) paid off:
   it confirmed both the silent clobber AND a second silent no-op on a
   non-existent source column, which shaped the two guard branches.
3. The docs-completeness test (`tests/test_docs.py::test_commands_are_documented`)
   is an ecosystem gate that a naive implementation would miss: it scans
   `cli.rst` for `    sqlite-utils <cmd>` lines. The cli.rst example line
   satisfies it; adding the command without a doc example would have failed the
   suite even though the code worked.
4. cli-reference.rst is cog-generated; new commands auto-appear via
   `list(cli.cli.commands.keys())`, so regenerating with cog kept the rendered
   `--help` block in sync without hand-editing.
5. Small-profile flow (explore -> spec -> build) fit the change cleanly; the
   spec's numbered assumptions captured every autonomous decision, and the
   probe-refresh check confirmed no module-map/command drift in AGENTS.md.
