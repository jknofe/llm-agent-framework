# Baseline notes - seq-B2-2026-09-14 session 2

1. Placed `Table.rename_column(name, new_name)` in sqlite_utils/db.py directly after
   `add_column`, mirroring the existing `Database.rename_table` pattern but as a
   Table method (per task wording) using native `ALTER TABLE ... RENAME COLUMN ... TO ...`
   (supported by SQLite >= 3.25, already the project's floor given other RENAME COLUMN-adjacent
   features and its use of modern ALTER TABLE support elsewhere).
2. Used the existing `AlterError` exception class (already used throughout db.py for
   alter-table validation failures) for both "no such column" and "column already exists"
   cases, rather than relying on sqlite3's raw OperationalError, since the task requires the
   table be left unchanged on the duplicate-name case - validating before executing SQL
   achieves this cleanly and matches the codebase's own AlterError conventions (e.g. add_column's
   foreign-key validation).
3. Added CLI command `rename-column PATH TABLE COLUMN NEW_NAME` with `--ignore`, mirroring
   `rename-table` exactly (same option, same try/except-into-ClickException pattern), catching
   both sqlite3.OperationalError and AlterError.
4. Did not add a changelog.rst entry (unreleased/dev version, no clear "Unreleased" section
   present to append to) - judged out of scope for the explicit ask (CLI command, API method,
   tests, doc updates to python-api.rst / cli.rst / cli-reference.rst).
5. Left the pre-existing uncommitted change to db.py (FTS-related `like` pattern, an apparent
   seeded bug unrelated to this task) untouched, per instructions.
