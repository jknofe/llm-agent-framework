# Baseline notes - seq-B1-2026-09-14 session 2 (T2: rename-column)

## Assumptions

1. `Table.rename_column(old, new)` uses `ALTER TABLE ... RENAME COLUMN ... TO ...`
   (supported natively since SQLite 3.25.0), mirroring how `Database.rename_table`
   uses `ALTER TABLE ... RENAME TO ...`. This repo already assumes a modern SQLite
   (add_column etc. rely on ALTER TABLE), so no fallback path was added.
2. Unlike `rename_table` (a `Database` method, since tables are namespaced at the
   DB level), `rename_column` is placed on `Table` per the task's explicit request
   ("Table.rename_column(old, new)"), consistent with columns being scoped to a
   table.
3. Validation order: raise `sqlite_utils.db.AlterError` (the exception class already
   used elsewhere in this codebase for alter-table style failures, e.g. `add_column`,
   `add_foreign_key`) if: the table doesn't exist, the source column doesn't exist,
   or the target column name already exists. All three checks happen *before* any
   SQL is executed, so a failing rename never touches the table (satisfies "leave
   the table unchanged").
4. CLI command `rename-column PATH TABLE COLUMN NEW_NAME` mirrors `rename-table`'s
   shape but does not add an `--ignore` flag, since `rename-table --ignore` is
   documented as "if table does not exist, do nothing" and the task only asked for
   duplicate-name renames to raise; no ignore semantics were requested for
   rename-column, and adding one wasn't clearly asked for, so it was left out to
   keep scope tight.
5. `docs/cli-reference.rst` is cog-generated. Running `cog -r` in this sandbox also
   rewrote unrelated `--fmt` help text for many other commands, because the
   installed `tabulate` package here is an older version (0.8.10, from apt) than
   whatever produced the currently-committed reference doc (which lists many more
   tabulate format names). To avoid polluting the diff with an environment
   artifact unrelated to this task, I reverted the full cog run and hand-added only
   the `rename-column` section/index entry, keeping the same format cog would have
   produced for that entry (verified via `CliRunner().invoke(cli.cli, ["rename-column", "--help"])`).
6. Left the pre-existing uncommitted seeded change to `sqlite_utils/db.py` (FTS
   `content="{}"` -> `content=[{}]` at the `is_fts` detection dict) untouched, per
   instructions ("leave it alone"). It is unrelated to this task.

## Environment notes

- No project virtualenv was present; `pluggy`, `pytest`, `tabulate`, `dateutil`
  were installed via `sudo apt-get install` (apt reachable), and
  `click-default-group`, `sqlite-fts4`, `cogapp` were already present in
  `~/.local/lib/python3.12/site-packages` (found via `pip install --index-url
  https://pypi.org/simple ...`, since the default configured index
  (artifactory.boschdevcloud.com) returns 401).
