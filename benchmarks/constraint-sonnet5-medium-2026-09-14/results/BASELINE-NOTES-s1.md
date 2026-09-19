# Baseline notes — con-B2-2026-09-14 / s1

No blocking ambiguities encountered. Root cause was determined directly from
code evidence (test_tracer.py's pinned SQL args for `detect_fts()` and the
sqlite3.OperationalError traceback), so no assumptions were required.

The "Table.transform() must never be called by new public methods" guidance
did not apply: the fix only corrected a `LIKE` pattern string inside the
existing `detect_fts()` method and did not add any new public method or touch
`transform()`, `ALTER TABLE`, or column rename/drop logic.
