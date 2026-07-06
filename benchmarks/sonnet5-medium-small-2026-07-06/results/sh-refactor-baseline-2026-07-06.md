# sh-refactor-baseline-2026-07-06

## Configuration

| Field | Value |
|---|---|
| Run ID | sh-refactor-baseline-2026-07-06 |
| Cell | sh-refactor |
| Arm | baseline (no framework) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-06T16:50:08 |
| End | 2026-07-06T16:55:47 |
| Duration | ~5m39s |
| Gate | **PASS** |

## Task

> The function abort() is defined identically in libexec/bats-core/bats, bats-exec-suite, and
> bats-gather-tests. Deduplicate it into lib/bats-core/common.bash with zero behavior change. The
> existing test suite must pass unmodified.

## Premise verification (finding)

**The premise is FALSE.** The three `abort()` definitions are not identical:

| File | Message form | Prefix | Usage-flag / `usage()` call |
|---|---|---|---|
| `libexec/bats-core/bats` | single `%s` message | `Error: ` | supports `--no-print-usage`; calls `usage` (defined in same file) unless suppressed |
| `libexec/bats-core/bats-exec-suite` | single `%s` message | `Error: ` | no usage handling at all (no `usage` function exists there) |
| `libexec/bats-core/bats-gather-tests` | variadic printf format + args, no auto-newline | `ERROR: ` (capitalized differently) | no usage handling |

Additionally, `libexec/bats-core/bats` did not source `lib/bats-core/common.bash` at all prior to
this change (unlike the other two, which already did).

Since a literal "extract the identical body" is impossible without changing at least one caller's
visible output, one generalized `abort()` was written into `lib/bats-core/common.bash`, configurable
via two optional variables (`BATS_ABORT_PREFIX`, `BATS_ABORT_PRINTF_ARGS`) that each script sets
(or leaves at defaults) before calling `abort()`, plus a `declare -F usage` guard so `usage` is only
invoked where it is actually defined (`bats`). No call site of `abort()` was modified anywhere in the
codebase — only the three duplicate function bodies were removed. Behavior was verified byte-for-byte
identical to the three originals for every existing call pattern (see numbered assumptions in
`/tmp/benchmark/runs/sh-refactor-baseline-2026-07-06/BASELINE-NOTES.md`).

## Diff

```
$ git diff --stat HEAD
 lib/bats-core/common.bash           | 41 +++++++++++++++++++++++++++++++++++++
 libexec/bats-core/bats              | 14 ++-----------
 libexec/bats-core/bats-exec-suite   |  5 -----
 libexec/bats-core/bats-gather-tests | 12 +++++------
 4 files changed, 48 insertions(+), 24 deletions(-)
```

Full diff:

```diff
diff --git a/lib/bats-core/common.bash b/lib/bats-core/common.bash
index 2bd1a5b..95f9b24 100644
--- a/lib/bats-core/common.bash
+++ b/lib/bats-core/common.bash
@@ -1,5 +1,46 @@
 #!/usr/bin/env bash
 
+# Print an error message to stderr and exit with status 1.
+#
+# This is shared by bats, bats-exec-suite and bats-gather-tests, whose
+# original abort() implementations differed slightly in message prefix,
+# argument handling and whether a `usage` function was invoked afterwards.
+# Those differences are preserved exactly via two optional variables that a
+# sourcing script may set *before* abort() is called (typically near the top
+# of the script, where the old inline definition used to live):
+#
+#   BATS_ABORT_PREFIX      - text printed before the message.
+#                             Default: 'Error: '
+#   BATS_ABORT_PRINTF_ARGS - if set to a non-empty value, all arguments are
+#                             passed straight through to `printf` as a format
+#                             string plus arguments (no implicit trailing
+#                             newline is added). Otherwise exactly one
+#                             argument is expected and printed via '%s\n'.
+#
+# An optional leading `--no-print-usage` flag suppresses calling a `usage`
+# function afterwards; if the sourcing script doesn't define `usage`, it is
+# never called regardless of the flag.
+abort() { # [--no-print-usage] <message> | <format> [args...]
+  local print_usage=1
+  if [[ ${1:-} == --no-print-usage ]]; then
+    print_usage=
+    shift
+  fi
+
+  printf '%s' "${BATS_ABORT_PREFIX-Error: }"
+  if [[ -n ${BATS_ABORT_PRINTF_ARGS:-} ]]; then
+    # shellcheck disable=SC2059
+    printf "$@"
+  else
+    printf '%s\n' "$1"
+  fi
+
+  if [[ -n $print_usage ]] && declare -F usage >/dev/null; then
+    usage
+  fi
+  exit 1
+} >&2
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
 
diff --git a/libexec/bats-core/bats-gather-tests b/libexec/bats-core/bats-gather-tests
index 8234a94..333bf63 100755
--- a/libexec/bats-core/bats-gather-tests
+++ b/libexec/bats-core/bats-gather-tests
@@ -4,17 +4,15 @@ set -eET
 args=("$@")
 filter_tags_list=()
 
-# shellcheck source=lib/bats-core/common.bash disable=SC2153 
+# shellcheck source=lib/bats-core/common.bash disable=SC2153
 source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"
 # shellcheck source=lib/bats-core/preprocessing.bash
 source "$BATS_ROOT/$BATS_LIBDIR/bats-core/preprocessing.bash"
 
-abort() {
-  printf 'ERROR: '
-  # shellcheck disable=SC2059
-  printf "$@"
-  exit 1
-} >&2
+# select the abort() message style ('ERROR: ' prefix, printf-style
+# format+args) matching this script's original abort() implementation
+BATS_ABORT_PREFIX='ERROR: '
+BATS_ABORT_PRINTF_ARGS=1
 
 read_tags() {
   local IFS=,
```

(Note: one line of the diff is a whitespace-only fix — a trailing space on the pre-existing
shellcheck directive comment in `bats-gather-tests` — picked up incidentally while touching that
block.)

## Gate output

### `test/` diff (must be empty)

```
$ git diff --stat -- test/
(empty)
```
PASS — no test file changed.

### shellcheck (run inside `bats-eco-builder` docker image, since shellcheck isn't installed locally)

```
=== bats ===
exit=0
=== bats-exec-suite ===
exit=0
=== bats-gather-tests ===
exit=0
=== common.bash ===
exit=0
```
PASS on all four touched/added files.

### bats suite (docker)

```
docker run --rm -e TERM=xterm -v "$WORK_DIR":/workspace bats-eco-builder bash -c '
  cd /workspace && ./bin/bats test; echo "SUITE-EXIT: $?"'
```

Result: `1..479`, all 479 lines `ok`, zero `not ok`, `SUITE-EXIT: 0`.

Full TAP output saved at
`/tmp/benchmark/runs/sh-refactor-baseline-2026-07-06/gate-output.txt` (481 lines).

### Overall gate: **PASS**
(bats suite exit 0, AND shellcheck exit 0 on all changed scripts, AND empty diff under `test/`)

## Observations

1. The task's stated premise ("defined identically") was factually wrong for all three call sites —
   prefix text, argument-passing convention (single message vs. printf format+args), and
   usage-callback behavior all differed. A baseline agent without a mandated verification step could
   easily have skipped checking this and either (a) silently changed observable error-message text
   for one or more scripts, or (b) picked one of the three bodies arbitrarily and pasted it
   everywhere, both of which would violate "zero behavior change" without any test coverage in this
   repo's suite catching it (no test in `test/bats.bats`, `test/bats-exec-suite`-adjacent, or
   `test/bats-gather-tests`-adjacent suites appears to assert the exact literal prefix text of these
   error paths byte-for-byte across all three binaries in a way that would fail loudly on a wrong
   choice — worth flagging as a coverage gap, not just an agent risk).
2. `libexec/bats-core/bats` silently lacked a `source lib/bats-core/common.bash` line even though it
   is the primary entry point and the other two internal scripts already sourced it — this looks like
   organic drift/inconsistency rather than intentional design, and the dedup was a natural place to
   fix it.
3. Making the shared function configurable via two plain shell variables (`BATS_ABORT_PREFIX`,
   `BATS_ABORT_PRINTF_ARGS`) set at each call site avoided touching any of the ~15 actual `abort(...)`
   invocations scattered across the three scripts, which kept the diff minimal and the risk of
   subtly breaking an individual call's argument list very low.
4. The full 479-test bats suite passed unmodified and shellcheck was clean on all four touched files
   on the first attempt; no iteration/fix-up cycle was needed after the initial implementation and
   isolated (non-docker) behavioral spot-check.
5. Isolated unit-level verification (sourcing `common.bash` directly and manually invoking `abort`
   with each of the three original calling conventions, with/without a `usage` function defined) was
   done before running the expensive docker gate, to catch discrepancies cheaply — this caught one
   red herring (an apparent `exit=0` from a subshell) that turned out to be a test-harness artifact
   (an intervening `echo` between the subshell and the `$?` check), not a real bug.

## Token usage (count_tokens.py, informational)

Note: dispatched as a Task-tool sub-agent inside one orchestrator session;
counted by isolating this agent's `agent-<id>.jsonl` transcript.

- Transcript dir: `subagents/agent-a6262a671bbcc2185.jsonl` (isolated)
- Sessions: 1 | API calls: 35 | duplicate lines skipped: 27

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 70 | 65761 | 1612185 | 3458 | 1681474 |
| **all** | 70 | 65761 | 1612185 | 3458 | 1681474 |
