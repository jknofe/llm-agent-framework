# Benchmark result: sh-refactor-small

## Configuration

| Field | Value |
|---|---|
| Run ID | sh-refactor-small |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Project | bats-core @ 5a7db7a98951d9d89b3b5e7800037e655a93345f (pin succeeded) |
| Task | dedup-abort: deduplicate abort() into lib/bats-core/common.bash |
| Start | 2026-07-02T19:03:57 |
| End | 2026-07-03T01:38:43 |
| Duration | ~6h35m wall clock (includes a session-limit pause; active work ~35 min) |
| Container status | PASS |

## Spec produced

`.ai/changes/dedup-abort/spec.md` (status: done). Key content:

- Goal records that the task premise ("abort() defined identically in three
  files") does NOT hold, verified before choosing the mechanism:
  - `libexec/bats-core/bats`: superset - `--no-print-usage` flag + calls
    `usage()` (defined only in that script).
  - `libexec/bats-core/bats-exec-suite`: same message/exit contract
    (`printf 'Error: %s\n' "$1" >&2; exit 1`), no usage concept.
  - `libexec/bats-core/bats-gather-tests`: different contract entirely -
    printf format string + args (`printf "$@"`), "ERROR: " prefix, whole
    function redirected `>&2`, call sites rely on multi-arg format
    expansion. Same-name coincidence (like `bats_tap_stream_*`), not
    duplication. Excluded from dedup, left untouched.
- Acceptance criteria name the ecosystem checks explicitly: full bats test
  suite (`bin/bats test`) green in the bats-eco-builder container, and
  `shellcheck -x` on changed files with no NEW findings vs pristine; plus
  the invariant: zero behavior change, `test/` byte-for-byte unmodified.
- 3 numbered assumptions in Notes (scope narrowing to the true duplicate
  pair; `declare -F usage` duck-typing; checks only available via
  container).

## Dedup mechanism

Shared `abort()` added to `lib/bats-core/common.bash`:

```bash
abort() {
  local print_usage=1
  if [[ ${1:-} == --no-print-usage ]]; then
    print_usage=
    shift
  fi
  printf 'Error: %s\n' "$1" >&2
  if [[ -n $print_usage ]] && declare -F usage >/dev/null; then
    usage >&2
  fi
  exit 1
}
```

How it gets sourced (existing project convention - env vars `BATS_ROOT` /
`BATS_LIBDIR` are exported by `bin/bats` before it execs the libexec
scripts):

- `libexec/bats-core/bats`: local `abort()` removed; NEW line
  `source "$BATS_ROOT/$BATS_LIBDIR/bats-core/common.bash"` (with
  `# shellcheck source=lib/bats-core/common.bash` directive) inserted after
  the script's own function definitions, before main logic and before every
  abort call site - matching the placement convention of bats-exec-file /
  bats-preprocess / bats-exec-test.
- `libexec/bats-core/bats-exec-suite`: local `abort()` removed; it ALREADY
  sourced common.bash (line 25, before all abort call sites) so no new
  source line needed.
- `libexec/bats-core/bats-gather-tests`: untouched (different contract; its
  local def is after its `source common.bash`, so it continues to shadow
  the shared one - no collision).
- The `declare -F usage >/dev/null` guard makes the shared function
  behave exactly like the old `bats` version where `usage` exists (only
  `bats`) and exactly like the old `bats-exec-suite` version where it
  doesn't - one body, zero behavior change for both callers.

## .ai commit history

```
8be5f9d build: dedup-abort
2ef0c11 spec: dedup-abort
a916480 explore: project context
65f9bec init: small-profile scaffold (bats-core)
```

4 commits.

## Diff stat (host repo, uncommitted working tree)

```
 .gitignore                        |  1 +
 lib/bats-core/common.bash         | 19 +++++++++++++++++++
 libexec/bats-core/bats            | 16 +++-------------
 libexec/bats-core/bats-exec-suite |  5 -----
 4 files changed, 23 insertions(+), 18 deletions(-)
```

The `.gitignore` line (`+.ai/`) is framework scaffolding from
init_agent.py (Step 1), not part of the dedup change. Nothing under
`test/` (also confirmed via `git status --porcelain | grep test/`: empty).

## Container output (Step 5)

`docker run --rm -v ...:/workspace -w /workspace bats-eco-builder` -
bats tail + shellcheck:

```
ok 472 invalid warning is an error
ok 473 BW01 is printed when `run`ing a (non-existent) command with exit code 127 without exit code check
ok 474 BW01 is not printed when `run`ing a (non-existent) command with exit code 127 with exit code check
ok 475 BW01 is not printed when `run`ing a command with exit code !=127 without exit code check
ok 476 BW02 is printed when run uses parameters without guaranteed version >= 1.5.0
ok 477 BW03 is printed when a test file defines setup_suite and setup_suite is not defined
ok 478 BW03 is not printed when a test file defines setup_suite but setup_suite was completed
ok 479 BW03 can be suppressed by setting BATS_SETUP_SUITE_COMPLETED
=== shellcheck changed files ===
(no output - zero findings)
```

A prior full run captured the suite exit code explicitly: 479/479 `ok`,
`=== EXIT CODE === 0`. Shellcheck baseline comparison: `git stash` +
`shellcheck -x` on the pristine files also produced zero findings
(exit 0), so no-new-errors holds trivially (0 before, 0 after).

Container verdict: **PASS** (suite green, shellcheck clean, test/ clean).

## Invariance evidence (zero behavior change)

1. Static: the shared abort() body is textually the old `bats` body plus
   one added conjunct (`&& declare -F usage >/dev/null`) on the usage
   branch. Where `usage` is defined (only `bats`), the conjunct is always
   true -> identical control flow. Where it is not (`bats-exec-suite`), the
   branch is dead and the remaining lines are exactly the old
   bats-exec-suite body (`printf 'Error: %s\n' "$1" >&2; exit 1`); no
   caller there ever passes `--no-print-usage`, so the flag check is inert.
2. Dynamic smoke tests on host bash, byte-compared against the exact
   strings the test suite asserts:
   - `bats` (no args) -> `Error: Must specify at least one <test>` + Usage
     block (matches test/bats.bats:14-15).
   - `bats --invalid-option` -> `Error: Bad command line option
     '--invalid-option'` + Usage block (matches test/bats.bats:21-22).
   - `bats --no-parallelize-across-files a.bats` -> `Error: The flag
     --no-parallelize-across-files requires at least --jobs 2` with NO
     usage block (bats-exec-suite path).
   - `bats --gather-test-outputs-in <non-empty>` -> `Error: Directory ...
     must be empty for --gather-test-outputs-in` with NO usage block
     (--no-print-usage path).
3. Ecosystem: full self-hosted suite (479 tests, which includes exact
   string assertions on these abort messages) green in the container.
4. test/ untouched: `git diff --stat -- test/` empty; git status shows no
   test/ entries.

## Project-context refresh (build skill step 5)

Fired: yes. probe.py re-run after the change; compared against
AGENTS.md GENERATED:project-context:
- Build/test/lint commands: unchanged (`npm run test` / `bin/bats test`).
- Module map: no new/removed/renamed module. Only drift: `lib` LOC
  1606 -> 1625 (+19, exactly the added abort() block) - a bare LOC delta
  on an existing module, which the skill says is not actionable.
- AGENTS.md changed: no (correctly left alone per the skill's rule).

## Review gate

Fresh general-purpose sub-agent, given only the diff file and the
acceptance criteria (no prior conversation context), plus the relevant
env facts (BATS_ROOT/BATS_LIBDIR lifetime). Verdict: PASS on every
criterion, no behavior-changing bugs found. Specifically confirmed the
new source line in `bats` precedes all abort() call sites (first call at
line ~275, source at ~100) and bats-exec-suite's existing source precedes
all of its call sites.

## Observations

- The task's premise was a deliberate trap: the three abort() definitions
  are NOT identical. Blindly unifying all three would have broken
  bats-gather-tests (printf-format contract, different prefix) or changed
  bats-exec-suite behavior (usage() undefined -> would need the guard
  anyway). The explore/spec discipline (read all bodies + all call sites
  before choosing a mechanism) caught this before any edit.
- bats-exec-suite already sourcing common.bash made half the change free;
  the only structural addition was one source line in `bats`.
- `declare -F usage` duck-typing was chosen over exporting a flag or
  keeping a thin wrapper because it needs zero caller-side changes and is
  provably equivalent in both sourcing contexts.
- No shellcheck/bats on the host; all ecosystem checks ran in the
  bats-eco-builder container. Host-side `bash -n` used as a fast syntax
  gate before the (slow, minutes-long) container suite.
- Session hit a limit mid-run (after container validation, before final
  .ai commit); resume worked cleanly off `.ai/.current` + git state, which
  is exactly what the framework's task-cursor design is for.
- .ai repo: 4 commits (init, explore, spec, build), all green hooks.
