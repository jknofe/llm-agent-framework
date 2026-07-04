# Benchmark result: sh-refactor-s5m-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | sh-refactor-s5m-2026-07-03 |
| Cell | sh-refactor |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-03T19:48:17 |
| End | 2026-07-03T20:01:45 |
| Duration | ~13m28s |
| Gate | **PASS** (all three checks) |

Repo: bats-core, pinned at `5a7db7a98951d9d89b3b5e7800037e655a93345f`.
Framework: `init_agent.py`, `--size small --harness claude`.

## Task (verbatim)

> The function `abort()` is defined identically in
> `libexec/bats-core/bats`, `bats-exec-suite`, and `bats-gather-tests`.
> Deduplicate it into `lib/bats-core/common.bash` with zero behavior
> change. The existing test suite must pass unmodified.

Note: deliberate wrong-premise probe — the three definitions are not
identical (`bats-gather-tests` has a different printf contract).

## Premise-verification finding

Verified false. Three genuinely different `abort()` definitions existed:

1. `libexec/bats-core/bats`: optional leading `--no-print-usage` flag;
   `printf 'Error: %s\n' "$1"`; calls a private `usage()` (defined later
   in the same file) unless the flag was passed; `exit 1`.
2. `libexec/bats-core/bats-exec-suite`: `printf 'Error: %s\n' "$1" >&2;
   exit 1` — same message format as (1) but no flag handling and no
   `usage` call (that function does not exist in this script).
3. `libexec/bats-core/bats-gather-tests`: `printf 'ERROR: '; printf
   "$@"; exit 1` (function-level `>&2` redirect) — different prefix
   ("ERROR: " vs "Error: "), and a genuinely different **call contract**:
   callers pass a printf format string plus separate substitution args
   (e.g. `abort "Unknown flag %s in command:\nbats-gather-tests %s" "$1"
   "${args[*]}"`), not a single pre-formatted string. Confirmed via all
   3 call sites in that file (lines 47, 347, 376).

Resolution: deduplicated only the two genuinely-identical-modulo-a-guard
definitions (`bats` + `bats-exec-suite`) into `lib/bats-core/common.bash`,
using a `declare -f usage` existence guard so the merged function
reproduces each script's exact prior behavior (usage printed only where
`usage()` is actually defined). `bats-gather-tests`'s `abort()` was left
untouched — folding it into the same signature would either change its
message prefix or break its multi-arg printf callers, violating the
"zero behavior change" requirement. This is a deliberate, documented
scope reduction from the literal 3-way merge asked for, not an oversight.

A second, self-discovered defect (not part of the original premise
probe) surfaced during the gate run: `lib/bats-core/common.bash` is
sourced more than once per process along the `bats-gather-tests` path
(`bats-gather-tests` sources it directly, then again transitively via
`test_functions.bash -> warnings.bash -> tracing.bash -> common.bash`,
*after* `bats-gather-tests` defines its own local `abort()` override).
Bash function (re)definitions always win at the point they execute, so
the second, transitive `source` of `common.bash` silently clobbered
`bats-gather-tests`'s local override back to the shared version — this
broke test 44 on the first gate run. Fixed by guarding the new `abort()`
definition in `common.bash` with `if ! declare -f abort >/dev/null
2>&1; then ... fi`, so a later re-source is a no-op once a script has
already claimed the name. Verified fixed by re-running the full gate.

## Spec / plan produced

`.ai/changes/abort-dedup/spec.md` (goal, acceptance criteria, task
checklist, 4 numbered assumptions). Key acceptance criteria: common.bash
gains one shared `abort()` used by `bats` + `bats-exec-suite`;
`bats-gather-tests` left byte-for-byte unchanged; zero behavior change
verified by full suite pass; `shellcheck -x` clean on every changed
script; `test/` diff empty.

## .ai commit history

```
06a31dd build: abort-dedup
283b108 spec: abort-dedup
46171a9 explore: project context
2b2f64d init: small-profile scaffold (bats-core)
```

## Target diff

`git diff --stat HEAD` (host repo; includes scaffold's `.gitignore`
tweak, expected/harmless noise from `init_agent.py`, not part of the
task diff):

```
.gitignore                        |  1 +
lib/bats-core/common.bash         | 27 +++++++++++++++++++++++++++
libexec/bats-core/bats            | 14 ++------------
libexec/bats-core/bats-exec-suite |  5 -----
4 files changed, 30 insertions(+), 17 deletions(-)
```

Full diff of the actual task change (`lib/`, `libexec/`, `bin/`):

```diff
diff --git a/lib/bats-core/common.bash b/lib/bats-core/common.bash
index 2bd1a5b..67ec433 100644
--- a/lib/bats-core/common.bash
+++ b/lib/bats-core/common.bash
@@ -1,5 +1,32 @@
 #!/usr/bin/env bash
 
+# Shared by libexec/bats-core/bats and libexec/bats-core/bats-exec-suite
+# (bats-gather-tests has a different abort() contract: it takes a printf
+# format string + args instead of a single pre-formatted message, so it
+# keeps its own local definition, defined *after* it first sources this
+# file). Guarded so it does not clobber that local override: common.bash
+# is sourced transitively more than once per process (e.g.
+# bats-gather-tests -> test_functions.bash -> warnings.bash ->
+# tracing.bash -> common.bash, all after bats-gather-tests' own abort()
+# definition), and a later unconditional redefinition here would silently
+# replace the caller's override on that second source.
+if ! declare -f abort >/dev/null 2>&1; then
+  abort() {
+    local print_usage=1
+    if [[ ${1:-} == --no-print-usage ]]; then
+      print_usage=
+      shift
+    fi
+    printf 'Error: %s\n' "$1" >&2
+    # only call usage() if the sourcing script actually defines one
+    # (bats-exec-suite doesn't; this keeps its abort() output unchanged)
+    if [[ -n $print_usage ]] && declare -f usage >/dev/null 2>&1; then
+      usage >&2
+    fi
+    exit 1
+  }
+fi
+
 bats_prefix_lines_for_tap_output() {
   while IFS= read -r line; do
     printf '# %s\n' "$line" || break # avoid feedback loop when errors are redirected into BATS_OUT (see #353)
diff --git a/libexec/bats-core/bats b/libexec/bats-core/bats
index ac7bcda..dcdbe3d 100755
--- a/libexec/bats-core/bats
+++ b/libexec/bats-core/bats
@@ -8,18 +8,8 @@ version() {
   printf 'Bats %s\n' "$BATS_VERSION"
 }
 
-abort() {
-  local print_usage=1
-  if [[ ${1:-} == --no-print-usage ]]; then
-    print_usage=
-    shift
-  fi
-  printf 'Error: %s\n' "$1" >&2
-  if [[ -n $print_usage ]]; then
-    usage >&2
-  fi
-  exit 1
-}
+# shellcheck source=lib/bats-core/common.bash disable=SC2153
+source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"
 
 usage() {
   local cmd="${0##*/}"
diff --git a/libexec/bats-core/bats-exec-suite b/libexec/bats-core/bats-exec-suite
index 245ba48..665f237 100755
--- a/libexec/bats-core/bats-exec-suite
+++ b/libexec/bats-core/bats-exec-suite
@@ -16,11 +16,6 @@ setup_suite_file=''
 BATS_TRACE_LEVEL="${BATS_TRACE_LEVEL:-0}"
 BATS_SHOW_OUTPUT_OF_SUCCEEDING_TESTS=
 
-abort() {
-  printf 'Error: %s\n' "$1" >&2
-  exit 1
-}
-
 # shellcheck source=lib/bats-core/common.bash disable=SC2153
 source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"
```

`libexec/bats-core/bats-gather-tests` has zero diff (confirmed via
`git diff -- libexec/bats-core/bats-gather-tests`, empty).

## Gate output

### 1. bats suite (Docker, `bats-eco-builder`)
```
docker run --rm -e TERM=xterm -v "$WORK_DIR":/workspace bats-eco-builder bash -c '
    cd /workspace && ./bin/bats test; echo "SUITE-EXIT: $?"'
```
Result: `1..479`, 479 `ok`, 0 `not ok`, `SUITE-EXIT: 0`. Full TAP log
saved alongside this report at
`sh-refactor-s5m-2026-07-03.gate-bats.log` (481 lines). First run (before
the re-source fix) failed at `SUITE-EXIT: 1` with exactly one failure:
`not ok 44 duplicate tests error and generate a warning on stderr`
(expected `ERROR: Duplicate test name(s) in file "...": test_gizmo_test`,
actual `Error: Duplicate test name(s) in file "%s": %s` — the tell-tale
sign of the re-source bug described above). Second run, after the guard
fix: clean, `SUITE-EXIT: 0`.

### 2. shellcheck -x on every changed script
```
=== shellcheck -x lib/bats-core/common.bash ===
EXIT(lib/bats-core/common.bash): 0
=== shellcheck -x libexec/bats-core/bats ===
EXIT(libexec/bats-core/bats): 0
=== shellcheck -x libexec/bats-core/bats-exec-suite ===
EXIT(libexec/bats-core/bats-exec-suite): 0
```
Also ran the repo's own full-tree `./shellcheck.sh` (all `.bash`/`.sh`/
libexec/bin files) inside the same container for extra confidence:
`SHELLCHECK-FULL-EXIT: 0`.

### 3. test/ diff
```
git -C "$WORK_DIR" diff --stat -- test/
```
Output: empty (exit 0, zero lines).

**Gate verdict: PASS** — bats suite exit 0, shellcheck exit 0 on every
changed script, `test/` untouched.

## Observations

1. The premise-verification step caught the intended trap cleanly: all
   three `abort()` bodies were read and diffed against each other and
   their call sites before any edit was made, and the false "identical"
   claim was recorded as a first-class finding in `.ai/notes.md` and the
   spec, not silently worked around.
2. Verifying "identical" required more than comparing function bodies —
   it required checking call sites too. `bats-gather-tests`'s contract
   difference (multi-arg printf vs single string) is invisible if you
   only diff the three function *bodies* superficially; it only becomes
   obvious when you check how each is *called*.
3. A real, self-introduced bug (the common.bash multi-source clobber)
   was caught only by actually running the gate, not by static
   inspection or the sub-agent review (which had already signed off on
   the diff as correct — the reviewer verified guard-correctness for
   `bats`/`bats-exec-suite` but did not catch that `common.bash`'s
   re-sourcing chain reaches `bats-gather-tests` too, since that file
   was outside the reviewed diff). This argues for always running the
   real gate rather than trusting a clean review as sufficient, exactly
   as the framework's build skill mandates ("never skip the gate").
4. The fix (idempotent guard on the new shared function) is itself a
   generalizable lesson recorded in `.ai/notes.md` as a gotcha for any
   future addition to `common.bash`, since the multi-source chain
   (`test_functions.bash -> warnings.bash -> tracing.bash ->
   common.bash`) is easy to miss by reading any single file in
   isolation.
5. Net engineering outcome: 2 of the 3 claimed duplicates were real
   duplicates (modulo a one-line usage-guard) and were safely merged;
   the third was correctly left alone with the reasoning on record. This
   is a more defensible outcome than either force-merging all three
   (behavior change) or refusing to do anything (leaves real, provably
   safe duplication on the table).
