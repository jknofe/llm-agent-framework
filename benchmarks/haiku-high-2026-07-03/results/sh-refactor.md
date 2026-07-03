# Benchmark Results: sh-refactor-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | sh-refactor-2026-07-03 |
| Cell | Abort deduplication (bats-core) |
| Profile | small |
| Model | claude-haiku-4-5 |
| Effort | high |
| Start | 2026-07-03T18:43:53 |
| End | 2026-07-03T18:47:29 |
| Duration | 3m 36s (216 seconds) |
| Gate Status | PASS |

## Auto-size Line

```
profile: small | project: bats-core | harness: claude
```

## Spec & Plan

The task was to deduplicate the `abort()` function from three locations:
- libexec/bats-core/bats
- libexec/bats-core/bats-exec-suite
- libexec/bats-core/bats-gather-tests

Into a single shared location: lib/bats-core/common.bash

### Premise Verification (CRITICAL FINDING)

The three definitions are NOT identical as warned:

1. **libexec/bats-core/bats and libexec/bats-core/bats-exec-suite**: Both define abort([--no-print-usage] <msg>):
   - Prints Error: <msg> to stderr
   - Calls usage() unless --no-print-usage given
   - Exits with code 1

2. **libexec/bats-core/bats-gather-tests**: Defines differently-shaped abort():
   - Prints ERROR: (uppercase, different prefix)
   - Uses printf "$@" for multi-arg format-string passthrough
   - Caller supplies its own \n
   - Different contract entirely

### Decision

Only bats and bats-exec-suite were merged into lib/bats-core/common.bash. The bats-gather-tests script retained its own function, renamed to bats_gather_tests_abort() to avoid silent collision when the script transitively re-sources common.bash.

## .ai Commit History

```
90c5bd1 build: dedup-abort
20ceb99 spec: dedup-abort
acd6e32 explore: project context
07e5ca4 init: small-profile scaffold (bats-core)
```

## Target Diff Summary

```
.gitignore                          |  1 +
 lib/bats-core/common.bash           | 18 ++++++++++++++++++
 libexec/bats-core/bats              | 16 +++-------------
 libexec/bats-core/bats-exec-suite   | 11 +++--------
 libexec/bats-core/bats-gather-tests | 14 ++++++++++----
 5 files changed, 35 insertions(+), 25 deletions(-)
```

## Changes

**lib/bats-core/common.bash**: Added 18-line abort() function at top
**libexec/bats-core/bats**: Removed local abort() definition, added source of common.bash
**libexec/bats-core/bats-exec-suite**: Removed local abort(), updated 3 call sites with --no-print-usage flag
**libexec/bats-core/bats-gather-tests**: Renamed abort() to bats_gather_tests_abort(), updated 4 call sites

## Gate Results

### Bats Test Suite: PASS
- Exit code: 0
- All 479 tests passed (ok 1..ok 479)

### Shellcheck: PASS
- All modified scripts pass shellcheck -x
  - libexec/bats-core/bats: OK
  - libexec/bats-core/bats-exec-suite: OK
  - libexec/bats-core/bats-gather-tests: OK
  - lib/bats-core/common.bash: OK

### Test Directory: PASS
- No changes to test/ directory

## Overall Gate Status: PASS

All three checks passed:
1. Bats test suite exit 0
2. Shellcheck exit 0 on all changed scripts
3. test/ directory untouched

## Key Observations

1. **Correct premise detection**: The brief warned the definitions were NOT identical - this was verified and correctly handled.

2. **Transitive sourcing gotcha avoided**: bats-gather-tests re-sources common.bash later via test_functions.bash. Function renaming prevented silent clobbering.

3. **Zero behavior change**: All 479 tests pass unmodified. bats and bats-exec-suite produce identical stderr/exit codes. bats-gather-tests unchanged.

4. **Clean implementation**: Well-documented code with clear comments explaining the design decisions.

5. **Minimal surgical diff**: 35 insertions, 25 deletions net. No refactoring or style changes, focused purely on deduplication.

