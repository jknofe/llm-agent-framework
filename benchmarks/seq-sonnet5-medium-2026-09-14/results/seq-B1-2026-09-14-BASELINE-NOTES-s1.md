# Baseline notes — s1

1. Assumed the test suite should be run with the project's own pytest
   config (pyproject.toml) rather than any custom invocation; created an
   isolated venv outside the repo (`/tmp/benchmark/runs/seq-B1-2026-09-14/venv`)
   since no venv/pytest was preinstalled and system pip is externally
   managed (PEP 668). This venv is outside WORK_DIR but under the allowed
   `/tmp/benchmark/runs/seq-B1-2026-09-14/` tree.
2. pip's configured index (artifactory.boschdevcloud.com) returned 401s for
   every package but pip fell back to PyPI successfully for all needed
   packages (pytest, hypothesis, cogapp, black, and the project's own
   runtime deps via `pip install -e .`), so no proxy/auth workaround was
   needed.
3. Fixed `like2` in `Table.detect_fts()` (sqlite_utils/db.py) to use the
   bracket-quoted `content=[name]` pattern instead of duplicating the
   double-quoted `like` pattern. Chose `like` = bracket / `like2` = quoted
   assignment (rather than the reverse) to match the literal SQL params
   already asserted in `tests/test_tracer.py::test_with_tracer`, which
   was otherwise going to fail with the reverse assignment.
4. Did not modify any test files — the fix in `sqlite_utils/db.py` alone
   made both the target test and the full suite pass.
