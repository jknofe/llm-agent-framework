# Benchmark Report: sh-refactor-small on the v5.9 framework

**Date:** 2026-07-03
**Model/effort:** claude-sonnet-5 x medium
**Framework state:** current HEAD (v5.9: automatic profile selection, plus the
v5.8 notes hub and the `init-agent --update` flow shipped earlier the same day).
**Raw results:** [results/sh-refactor-small.md](results/sh-refactor-small.md)

Purpose: a full end-to-end cell on the framework after the v5.9 changes, chosen
to double as live validation of the new **auto-size** feature. The
`sh-refactor-small` cell (bats-core `abort()` deduplication) is the cheapest in
the multi-eco set and has a clean deterministic gate, so it exercises the whole
small-profile chain (init -> explore -> spec -> build) without a package
install.

## Cell

| Field | Value |
|---|---|
| Target | [bats-core](https://github.com/bats-core/bats-core.git) @ `5a7db7a` (pinned SHA) |
| Task | Deduplicate `abort()` from `libexec/bats-core/{bats,bats-exec-suite,bats-gather-tests}` into `lib/bats-core/common.bash`, zero behavior change, test suite unmodified |
| Profile | small, **auto-selected** (`--size auto`) |
| Gate image | `bats-eco-builder` (ubuntu:24.04 + shellcheck + bash + parallel) |
| Duration | ~65 min |

## Result: PASS (all three gate checks, re-verified independently)

The deterministic gate was re-run by the orchestrator, not just trusted from the
agent's report:

| Check | Result |
|---|---|
| `bin/bats test` in `bats-eco-builder` | exit 0, **479/479 ok** |
| `shellcheck -x` on every changed script | exit 0 on all four |
| `git diff` under `test/` | empty (suite untouched) |

Container note: the suite needs `TERM=xterm` in the image, else 13 unrelated
`tput`/TERM-artifact tests fail identically before and after the change
(confirmed by a `git stash` baseline). That is a container quirk, not a
regression; with `TERM` set the suite is fully green.

## Auto-size validated in the real init flow

Init printed `auto-size: 2470 lines of code across source files -> small
profile` and scaffolded small. The profile was chosen by the v5.9 estimator, not
hardcoded in the prompt. bats-core (2470 LOC) sits well under the ~10k boundary,
so the pick matches the cell's designed profile. Commit chain is a clean
small-profile sequence: `init -> explore -> spec -> build`.

## Premise-verification finding (the key quality signal)

The brief deliberately asserts all three `abort()` definitions are identical.
They are not, and the agent handled it correctly and then some:

- Reconciled the two true variants (`bats`, `bats-exec-suite`) into a shared
  `abort()` in `common.bash` using the existing `--no-print-usage` flag, updating
  `bats-exec-suite`'s three call sites.
- Kept `bats-gather-tests`'s genuinely different contract (printf format-string
  passthrough, `ERROR: ` prefix, asserted verbatim by two existing tests)
  separate. Beyond the initial "leave it alone" plan, it discovered that
  `bats-gather-tests` transitively re-sources `common.bash` (via
  `test_functions.bash` -> `warnings.bash` -> `tracing.bash`), which would
  silently clobber a same-named local override once the shared `abort()` existed
  (it actually broke `test/bats.bats:429` until fixed). It renamed the local
  function to `bats_gather_tests_abort` with a comment explaining the collision
  and the differing contract, byte-for-byte output unchanged.

This is deeper than the round-1 multi-eco agent, which only flagged the
discrepancy. The framework review gate additionally caught a real leak (a source
comment referencing `.ai/notes.md`) and removed it.

## Verdict

The framework at v5.9 HEAD passes a full small-profile cell clean, and automatic
profile selection drove the init end-to-end with the correct pick. No framework
defects surfaced. Single-cell round; the wider multi-eco set is unchanged and
remains the reference for cross-ecosystem coverage.
