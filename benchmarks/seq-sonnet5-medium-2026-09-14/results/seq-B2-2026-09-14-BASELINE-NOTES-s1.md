# Baseline notes — s1

1. No blocking ambiguities encountered. Root cause was clear from `git log -p`
   on the `detect_fts` method: the seed commit reverted upstream fix
   `1a28416` ("Fix for detect_fts failing on [], refs #694") by duplicating
   the double-quote LIKE pattern into the `like` key that should hold the
   bracket-quoted legacy pattern. Restored the original upstream fix
   verbatim.
2. Assumed "keep the test suite green" means the full suite, not just
   tests/test_fts.py — ran full suite (1080 passed, 0 failed, 16 skipped)
   to confirm no regressions.
3. Did not touch git history/commit; changes left in working tree per
   instructions.
