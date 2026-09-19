# Baseline notes - s1

1. No ambiguity encountered; root cause was clear from git blame/log history
   (commit 1a28416 fixed it, commit 49b1d39 "seed: benchmark bug state"
   reverted it). Applied the minimal one-line fix restoring the bracket-quote
   LIKE pattern in `Table.detect_fts()`.
2. Ran the full test suite (not just tests/test_fts.py) to confirm no
   regressions: 1080 passed, 16 skipped, 0 failed.
3. Did not touch anything outside WORK_DIR; did not commit to repo git per
   instructions.
</content>
