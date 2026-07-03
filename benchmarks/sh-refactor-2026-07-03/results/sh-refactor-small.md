# Benchmark Results: sh-refactor-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | sh-refactor-2026-07-03 |
| Cell | sh-refactor-small |
| Profile | small (auto-selected) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-03T16:37:28 |
| End | 2026-07-03T17:42:26 |
| Duration | 3898 seconds (~65 minutes) |
| Gate status | **PASS** |

## Auto-size outcome

Exact printed line:

```
auto-size: 2470 lines of code across source files -> small profile
```

Confirmed: the framework auto-selected the **small** profile for bats-core
(~2.5k LOC as expected), and scaffolding proceeded on that basis (all
`.claude/skills/*`, `AGENTS.md`, `.ai/` artifacts are the small-profile
variants).

## Spec produced

Full content of `.ai/changes/dedup-abort/spec.md` (final state, `status: done`):

```markdown
---
id: dedup-abort
title: deduplicate abort() into lib/bats-core/common.bash
status: done
created: 2026-07-03
---

## Goal
Three libexec scripts (`bats`, `bats-exec-suite`, `bats-gather-tests`) each
define their own `abort()` helper. The brief asks to move the shared
definition into `lib/bats-core/common.bash` with zero behavior change.
Verifying the premise first (per instructions) shows the three
implementations are not textually identical (see Notes #1). This change
therefore deduplicates only the two implementations that are true
duplicates in effect (`bats` and `bats-exec-suite`), moves that single
definition into `common.bash`, and leaves `bats-gather-tests`'s
implementation untouched since it has a genuinely different contract that
the test suite depends on verbatim.

## Acceptance criteria
- [x] `abort()` used by `libexec/bats-core/bats` and
      `libexec/bats-core/bats-exec-suite` is defined exactly once, in
      `lib/bats-core/common.bash`.
- [x] Both call sites source `lib/bats-core/common.bash` (existing
      `source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"` pattern) before
      their first `abort()` call, and produce byte-identical stderr output
      and exit codes to the pre-change behavior for every existing call site.
- [x] `libexec/bats-core/bats-gather-tests`'s `abort()` keeps its exact
      format-string / `ERROR:`-prefixed contract and output (asserted
      verbatim by `test/bats.bats:429` and `test/tagging.bats:62-65`);
      it is renamed to `bats_gather_tests_abort()` (see Notes #4) but its
      body and every call site's arguments are otherwise unchanged.
- [x] The full test suite (`bin/bats test`) passes unmodified: no file under
      `test/` is edited. Confirmed: `git diff --stat -- test/` is empty;
      479 passed / 0 failed in the container gate (with `TERM` set - see
      Notes #5 for an unrelated container-only artifact without it).
- [x] `shellcheck` (`./shellcheck.sh`, i.e. `shellcheck -x`) is clean on
      every changed script: `lib/bats-core/common.bash`,
      `libexec/bats-core/bats`, `libexec/bats-core/bats-exec-suite`,
      `libexec/bats-core/bats-gather-tests`. Confirmed exit 0 on each
      individually and on the full `./shellcheck.sh` run.

## Tasks
- [x] Add the shared `abort()` (the `bats` version, verbatim: supports
      `--no-print-usage`, calls `usage()` otherwise, `printf 'Error: %s\n'
      "$1" >&2`, `exit 1`) to `lib/bats-core/common.bash`.
- [x] `libexec/bats-core/bats`: remove the local `abort()` definition; add
      `# shellcheck source=lib/bats-core/common.bash` +
      `source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"` near the top of
      the file (before any `abort()` call, after the initial `BATS_VERSION`/
      `VALID_FORMATTERS` assignments). No call-site changes needed here since
      its existing calls already match the shared function's contract
      (some pass `--no-print-usage`, most don't, exactly as before).
- [x] `libexec/bats-core/bats-exec-suite`: remove the local `abort()`
      definition (the existing `source .../common.bash` line, already present
      right after the local definition, covers the shared one once removed).
      Update its 3 `abort(...)` call sites to pass `--no-print-usage` as the
      first argument (this script has no `usage()` function, so without the
      flag the shared abort() would try to call an undefined `usage` command
      instead of exiting cleanly - the flag preserves the exact prior
      output/exit-code).
- [x] `libexec/bats-core/bats-gather-tests`: rename its local `abort()` to
      `bats_gather_tests_abort()` (body unchanged) and update its 3 call
      sites; see Notes #4 for why a rename is required here, not "leave
      untouched" as originally planned.
- [x] Run `./shellcheck.sh` (or per-file `shellcheck -x`) and `bin/bats test`
      locally before declaring done. Also ran both inside the
      `bats-eco-builder` gate container.

## Notes
1. Premise verification: the three `abort()` definitions are NOT identical.
   - `bats`: `abort([--no-print-usage] <msg>)` -> `Error: <msg>` to stderr,
     calls `usage()` unless suppressed, `exit 1`.
   - `bats-exec-suite`: `abort(<msg>)` -> `Error: <msg>` to stderr, `exit 1`.
     No `usage()` concept; behaviorally equal to `bats`'s `--no-print-usage`
     branch, but the literal function bodies differ (no flag parsing, no
     usage call).
   - `bats-gather-tests`: `abort(<printf-fmt> [args...])` -> `ERROR: ` prefix
     (different case) then `printf "$@"` (multi-arg format-string
     passthrough, caller supplies its own newline), `exit 1`. Genuinely
     different call contract, used with 2-arg format strings
     (e.g. `abort 'Duplicate test name(s) in file "%s": %s' "$filename"
     "$file_duplicate_test_names"`), and its exact `ERROR: ...` text is
     asserted by `test/bats.bats:429` and `test/tagging.bats:62-65`. Folding
     it into the other contract would silently break those assertions.
     Decision: keep it local, do not touch it or its call sites.
2. Because `bats-exec-suite` has no `usage()` function, sharing `bats`'s
   richer `abort()` verbatim requires its 3 call sites to pass
   `--no-print-usage` explicitly; this is the only call-site edit in the
   change and is behavior-preserving (verified against
   `test/bats.bats` assertions that check `abort()` stderr text: lines 14,
   21, 716, 725, 735, 1142, 1420, 1495 for `bats`; none for
   `bats-exec-suite`'s "Cannot execute" / "requires at least --jobs 2"
   messages, but output format is unchanged either way).
3. `BATS_ROOT`/`BATS_LIBDIR` are exported once by `bin/bats` before it execs
   `libexec/bats-core/bats`, so sourcing `common.bash` early in that script
   (before its first `abort()` call, well before the existing late
   `validator.bash` source line) is safe and follows the existing pattern
   used by every other libexec script.
4. Discovered while implementing (revises Notes #1's "leave untouched"
   plan): `bats-gather-tests` sources `test_functions.bash` (line ~56),
   which sources `warnings.bash`, which sources `tracing.bash`, which
   sources `common.bash` again. Once `common.bash` defines its own `abort`,
   this transitive re-source silently clobbers `bats-gather-tests`'s local
   `abort()` override for any call after that point (verified by
   reproducing: `bin/bats --tap test/fixtures/bats/duplicate-tests_no_shellcheck.bats`
   printed the *shared* `abort()`'s "Error: ...%s...: %s" text, unexpanded,
   plus a stray "usage: command not found", instead of the expected
   "ERROR: Duplicate test name(s)..." - this is exactly the regression
   `test/bats.bats:429` catches). Same-named-function shadowing across
   re-sourced library files is unsafe in this codebase given its "sourcing
   is always idempotent" design (no load-guards exist anywhere in
   `lib/bats-core/*.bash`). Fix: rename `bats-gather-tests`'s local function
   to `bats_gather_tests_abort` (no collision possible with any name in
   `lib/bats-core/`), leaving its behavior, message text, and call
   arguments byte-for-byte identical. This is a necessary correctness fix,
   not scope creep: without it the acceptance criterion "full test suite
   passes unmodified" fails (confirmed locally: exit 1, 1 failing test,
   before the rename; exit 0, 479 passing, 0 failing, after).
5. Container-only artifact, not a regression: `./bin/bats test` inside the
   `bats-eco-builder` container without `TERM` set produces 13 unrelated
   `not ok` (pretty-formatter tests needing `tput`/a real terminal).
   Verified identical on the pre-change baseline (same container, `git
   stash`) - same 13 test names fail either way. Fix is `-e TERM=xterm` on
   `docker run`, not a code or test change.
6. Fresh-context reviewer (general-purpose sub-agent, given only the diff
   + this spec) ran and reported "mostly PASS": confirmed all 5 acceptance
   criteria implemented, no Bash correctness bugs, all 3
   `bats-gather-tests` call sites consistently renamed, no out-of-scope
   changes. It flagged that in-source comments referenced `.ai/notes.md`
   (agent scratch state, not part of the shipped project) - fixed by
   rewriting both comments (`lib/bats-core/common.bash`,
   `libexec/bats-core/bats-gather-tests`) to be self-contained, and
   corrected stale "keeps its own abort()" wording to reflect the rename.
```

## .ai commit history

```
90c5bd1 build: dedup-abort
20ceb99 spec: dedup-abort
acd6e32 explore: project context
07e5ca4 init: small-profile scaffold (bats-core)
```

## bats-core changes

`git diff --stat HEAD`:

```
 .gitignore                          |  1 +
 lib/bats-core/common.bash           | 18 ++++++++++++++++++
 libexec/bats-core/bats              | 16 +++-------------
 libexec/bats-core/bats-exec-suite   | 11 +++--------
 libexec/bats-core/bats-gather-tests | 14 ++++++++++----
 5 files changed, 35 insertions(+), 25 deletions(-)
```

(`.gitignore`'s `+.ai/` line is a framework scaffold artifact, not part of
the dedup-abort change itself.)

Full `git diff HEAD` (excluding `.gitignore`):

```diff
diff --git a/lib/bats-core/common.bash b/lib/bats-core/common.bash
index 2bd1a5b..15279ff 100644
--- a/lib/bats-core/common.bash
+++ b/lib/bats-core/common.bash
@@ -1,5 +1,23 @@
 #!/usr/bin/env bash
 
+# print an error message and exit 1; call `usage` unless suppressed.
+# Shared by libexec/bats-core/bats and libexec/bats-core/bats-exec-suite.
+# bats-gather-tests has a differently-shaped error helper
+# (bats_gather_tests_abort, format-string based) and is intentionally not
+# using this one.
+abort() { # [--no-print-usage] <msg>
+  local print_usage=1
+  if [[ ${1:-} == --no-print-usage ]]; then
+    print_usage=
+    shift
+  fi
+  printf 'Error: %s\n' "$1" >&2
+  if [[ -n $print_usage ]]; then
+    usage >&2
+  fi
+  exit 1
+}
+
 bats_prefix_lines_for_tap_output() {
   while IFS= read -r line; do
     printf '# %s\n' "$line" || break # avoid feedback loop when errors are redirected into BATS_OUT (see #353)
diff --git a/libexec/bats-core/bats b/libexec/bats-core/bats
index ac7bcda..327230b 100755
--- a/libexec/bats-core/bats
+++ b/libexec/bats-core/bats
@@ -8,19 +8,6 @@ version() {
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
-
 usage() {
   local cmd="${0##*/}"
   local line
@@ -126,6 +113,9 @@ export BATS_LIB_PATH=${BATS_LIB_PATH-/usr/lib/bats}
 BATS_REPORT_OUTPUT_DIR=${BATS_REPORT_OUTPUT_DIR-.}
 export BATS_LINE_REFERENCE_FORMAT=${BATS_LINE_REFERENCE_FORMAT-comma_line}
 
+# shellcheck source=lib/bats-core/common.bash
+source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"
+
 if [[ ! -d "${BATS_TMPDIR}" ]]; then
   printf "Error: BATS_TMPDIR (%s) does not exist or is not a directory" "${BATS_TMPDIR}" >&2
   exit 1
diff --git a/libexec/bats-core/bats-exec-suite b/libexec/bats-core/bats-exec-suite
index 245ba48..988c2da 100755
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
 
@@ -104,7 +99,7 @@ done
 
 if [[ "$num_jobs" != 1 ]]; then
   if ! type -p "${parallel_binary_name}" >/dev/null && "${parallel_binary_name}" --version &>/dev/null && [[ -z "$bats_no_parallelize_across_files" ]]; then
-    abort "Cannot execute \"${num_jobs}\" jobs without GNU parallel"
+    abort --no-print-usage "Cannot execute \"${num_jobs}\" jobs without GNU parallel"
   fi
   # shellcheck source=lib/bats-core/semaphore.bash
   source "${BATS_ROOT}/$BATS_LIBDIR/bats-core/semaphore.bash"
@@ -154,11 +149,11 @@ if [[ -n "$count_only_flag" ]]; then
 fi
 
 if [[ -n "$bats_no_parallelize_across_files" ]] && [[ ! "$num_jobs" -gt 1 ]]; then
-  abort "The flag --no-parallelize-across-files requires at least --jobs 2"
+  abort --no-print-usage "The flag --no-parallelize-across-files requires at least --jobs 2"
 fi
 
 if [[ -n "$bats_no_parallelize_within_files" ]] && [[ ! "$num_jobs" -gt 1 ]]; then
-  abort "The flag --no-parallelize-across-files requires at least --jobs 2"
+  abort --no-print-usage "The flag --no-parallelize-across-files requires at least --jobs 2"
 fi
 
 # only abort on the lowest levels
diff --git a/libexec/bats-core/bats-gather-tests b/libexec/bats-core/bats-gather-tests
index 8234a94..d43bbe4 100755
--- a/libexec/bats-core/bats-gather-tests
+++ b/libexec/bats-core/bats-gather-tests
@@ -9,7 +9,13 @@ source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"
 # shellcheck source=lib/bats-core/preprocessing.bash
 source "$BATS_ROOT/$BATS_LIBDIR/bats-core/preprocessing.bash"
 
-abort() {
+# Named distinctly (not `abort`) because this script also transitively
+# sources lib/bats-core/common.bash (via test_functions.bash -> warnings.bash
+# -> tracing.bash), which defines its own `abort()`; a same-named local
+# function here would get silently clobbered by that re-source. The contract
+# differs from the shared one anyway (format-string passthrough, "ERROR: "
+# prefix, multiple positional args).
+bats_gather_tests_abort() {
   printf 'ERROR: '
   # shellcheck disable=SC2059
   printf "$@"
@@ -44,7 +50,7 @@ while [[ "$#" -ne 0 ]]; do
       break
       ;;
     *)
-      abort "Unknown flag %s in command:\nbats-gather-tests %s" "$1" "${args[*]}"
+      bats_gather_tests_abort "Unknown flag %s in command:\nbats-gather-tests %s" "$1" "${args[*]}"
       ;;
   esac
   shift 1
@@ -344,7 +350,7 @@ export BATS_TEST_FILE_NUMBER=0
 for filename in "$@"; do
   (( ++BATS_TEST_FILE_NUMBER ))
   if [[ ! -f "$filename" ]]; then
-    abort 'Test file "%s" does not exist.\n' "${filename}"
+    bats_gather_tests_abort 'Test file "%s" does not exist.\n' "${filename}"
   fi
 
   BATS_TEST_FILENAME="$filename"
@@ -373,7 +379,7 @@ for filename in "$@"; do
 
   if [[ -n "$file_duplicate_test_names" ]]; then
     trap - EXIT # prevent 1..1 from being printed
-    abort 'Duplicate test name(s) in file "%s": %s' "$filename" "$file_duplicate_test_names"
+    bats_gather_tests_abort 'Duplicate test name(s) in file "%s": %s' "$filename" "$file_duplicate_test_names"
   fi
 
   total_test_count=$((total_test_count + file_test_count))
```

## Premise-verification finding

**No, the three `abort()` were not identical.** The brief's premise ("`abort()`
is defined identically in all three files") was false:

- `libexec/bats-core/bats`: `abort([--no-print-usage] <msg>)` — prints
  `Error: <msg>`, conditionally calls a script-local `usage()`, `exit 1`.
- `libexec/bats-core/bats-exec-suite`: `abort(<msg>)` — prints `Error: <msg>`,
  `exit 1`. No `usage()` concept at all; behaviorally the `--no-print-usage`
  branch of `bats`'s version, but textually a different (shorter) function.
- `libexec/bats-core/bats-gather-tests`: `abort(<printf-fmt> [args...])` —
  prints `ERROR: ` (different case) then does full `printf "$@"` format-string
  expansion (multiple positional args, no forced newline). Genuinely
  different calling contract from the other two, and its exact text is
  asserted verbatim by `test/bats.bats:429` and `test/tagging.bats:62-65`.

**What was done about `bats-gather-tests`:** the plan (from the spec) was to
leave it completely untouched, since forcing its contract into the shared
`abort()` would break the tests that assert its literal output. That plan
had to be revised once during implementation: simply *leaving it alone*
was not sufficient, because `bats-gather-tests` transitively re-sources
`lib/bats-core/common.bash` later in its own execution (via
`test_functions.bash` → `warnings.bash` → `tracing.bash`), and once
`common.bash` defines its own `abort()`, that re-source silently clobbers
`bats-gather-tests`'s local override for every `abort()` call after that
point — a real regression, caught by running the test suite (`not ok` on
`test/bats.bats:429`, "duplicate tests error and generate a warning on
stderr", output showed the wrong/unexpanded shared-abort text plus a stray
"usage: command not found"). Root cause: this codebase has no
load-guard convention anywhere in `lib/bats-core/*.bash` — it assumes
re-sourcing any library file is always idempotent, which is true for every
existing function except a newly-introduced, differently-behaved
same-named one. Fix: renamed `bats-gather-tests`'s local function to
`bats_gather_tests_abort` (its body, message text, and every call site's
arguments are byte-for-byte unchanged) so it can never collide with
anything defined in `lib/bats-core/`. Re-ran the full suite after the
rename: 479 passed, 0 failed.

## Gate output

### 1. bats test suite (in `bats-eco-builder` container, `TERM=xterm`)

```
$ docker run --rm -e TERM=xterm -v <workdir>:/workspace bats-eco-builder bash -c '
cd /workspace
./bin/bats test
echo "exit: $?"
'
...
ok 476 BW02 is printed when run uses parameters without guaranteed version >= 1.5.0
ok 477 BW03 is printed when a test file defines setup_suite and setup_suite is not defined
ok 478 BW03 is not printed when a test file defines setup_suite but setup_suite was completed
ok 479 BW03 can be suppressed by setting BATS_SETUP_SUITE_COMPLETED
exit: 0
```
479 `ok`, 0 `not ok`. **PASS.**

(Without `-e TERM=xterm`, the same container produces 13 `not ok` failures,
all `tput: No value for $TERM and no -T specified` related
(pretty-formatter tests). Verified byte-for-byte identical failing-test list
on the pre-change baseline in the same container via `git stash` — confirms
this is a pre-existing container/TTY artifact, not caused by this change.)

### 2. shellcheck (in container)

```
=== shellcheck -x lib/bats-core/common.bash ===
exit: 0
=== shellcheck -x libexec/bats-core/bats ===
exit: 0
=== shellcheck -x libexec/bats-core/bats-exec-suite ===
exit: 0
=== shellcheck -x libexec/bats-core/bats-gather-tests ===
exit: 0
=== full ./shellcheck.sh ===
full shellcheck.sh exit: 0
```
**PASS** on every changed script individually and on the project's own
`./shellcheck.sh` (`shellcheck -x` over the entire repo).

### 3. `test/` untouched

```
$ git diff --stat -- test/
(empty output)
```
**PASS** — zero changes under `test/`.

**All three checks PASS -> Gate: PASS.**

## Observations

The framework's explore -> spec -> build workflow mapped cleanly onto this
task; auto-size correctly picked the small profile from LOC and the small
skills (explore/spec/build) were sufficient without needing the large
profile's KB machinery. The most valuable discipline was the spec's mandate
to verify the brief's premise before acting: a naive implementation would
have merged all three `abort()` definitions and broken tests, or (subtler)
merged just the two "true duplicates" and still broken a third file through
an indirect same-named-function collision via transitive sourcing — this
was only caught by actually running the test suite locally before declaring
done, not by code inspection alone. The `build` skill's mandatory review gate
(fresh-context sub-agent) caught a real, if minor, issue (a source comment
referencing the agent's own `.ai/notes.md` scratch file, which doesn't
belong in shipped project source) that a self-review likely would have
missed. One point of friction: the deterministic gate's container lacked
`TERM`, producing 13 unrelated failures that required a side investigation
(`git stash` + rerun) to prove were pre-existing rather than introduced by
the change; the runbook could preemptively set `-e TERM=xterm` to avoid this
noise. `docker image inspect` also failed to find the buildx-tagged gate
image even though `docker run` worked against it — a minor host quirk, not
a framework issue.
