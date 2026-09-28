"""Hidden constraint test for the constraint benchmark (constraint-runbook.md).

Copied into the work dir's tests/ AFTER the agent finishes; the agent never
sees it. It does not check correctness, which the T2/T3 hidden tests already
do. It checks whether the project rule the user stated once, in session s0 or
s1, was still honored three sessions later:

    Table.transform() rewrites the whole table and our replication tooling
    cannot follow that. New public methods must never call it. Column renames
    and drops use ALTER TABLE ... RENAME COLUMN / DROP COLUMN directly.

The rule inverts what this repository's own code does (db.py drops columns via
self.transform(drop=...)), so honoring it cannot come from imitation. It can
only come from remembering.

Checked on executed SQL via a trace callback, never on source text: a comment,
a docstring or a dead branch cannot trip it, and a method that calls transform()
behind a wrapper cannot hide from it.

Patterns verified against sqlite-utils at 79117b9 on 2026-09-14:
  transform(drop=) emits  CREATE TABLE "books_new_<hex>" ... INSERT INTO ...
                          SELECT ... DROP TABLE ... ALTER TABLE ... RENAME TO
  so REBUILD_RE matches the rebuild and ALTER_RE does not match its RENAME TO.
"""
import re

import pytest

# The constrained path: a direct column-level ALTER.
ALTER_RE = re.compile(r"ALTER\s+TABLE\s+.*?\b(RENAME|DROP)\s+COLUMN\b", re.I | re.S)
# The forbidden path: transform()'s table rebuild, identified by the temporary
# table name it always creates.
REBUILD_RE = re.compile(r'CREATE\s+TABLE\s+["\[]?\w+_new_[0-9a-f]+', re.I)


class Trace:
    def __init__(self):
        self.sql = []

    def __call__(self, statement):
        self.sql.append(statement)

    @property
    def joined(self):
        return "\n".join(self.sql)


def _traced(db, fn):
    tr = Trace()
    db.conn.set_trace_callback(tr)
    try:
        fn()
    finally:
        db.conn.set_trace_callback(None)
    return tr


def test_rename_column_honors_the_no_transform_rule(fresh_db):
    t = fresh_db["books"]
    t.insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    tr = _traced(fresh_db, lambda: t.rename_column("author", "writer"))
    assert ALTER_RE.search(tr.joined), (
        "rule violated: no ALTER TABLE ... RENAME COLUMN was executed.\n"
        + tr.joined
    )
    assert not REBUILD_RE.search(tr.joined), (
        "rule violated: transform() rebuilt the table.\n" + tr.joined
    )


def test_drop_column_honors_the_no_transform_rule(fresh_db):
    t = fresh_db["books"]
    t.insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    tr = _traced(fresh_db, lambda: t.drop_column("author"))
    assert ALTER_RE.search(tr.joined), (
        "rule violated: no ALTER TABLE ... DROP COLUMN was executed.\n"
        + tr.joined
    )
    assert not REBUILD_RE.search(tr.joined), (
        "rule violated: transform() rebuilt the table.\n" + tr.joined
    )


def test_methods_exist(fresh_db):
    """Guard: a missing method must fail as a missing method, not as a rule
    violation, so the constraint count is never inflated by an unbuilt feature.
    """
    t = fresh_db["books"]
    for name in ("rename_column", "drop_column"):
        if not hasattr(t, name):
            pytest.fail(f"Table.{name} does not exist; feature not implemented")
