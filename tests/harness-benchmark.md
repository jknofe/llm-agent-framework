# Harness benchmark: Claude Code vs OpenCode

How to compare the framework on two harnesses with the same models, tasks
and effort, and what the first rounds found. The scripts are in
`tests/harness-bench/`. This compares harnesses and model mixes; it does not
try to prove that the framework itself pays off (CONCEPT.md Part II says why
that program stopped).

## What one run is

A fresh clone of satty at `f578432` (no Rust toolchain), scaffolded for one
harness, with six canonical task files copied in (`tasks/`). Nine fresh
sessions:

| Step | Task | Type | Expected path |
|---|---|---|---|
| 1 | `/task do input-scale-window` (issue #689) | investigation | inline (no host edit) |
| 2 | `/task do nextrelease-typo` | bug | inline (one editing step) |
| 3 | `/task do readme-troubleshooting` | change | inline (one editing step) |
| 4 | `/task do keybinds-consistency` | test | inline (findings only) |
| 5 | `/task do readme-shortcut-tables` | change | worker (two editing steps) |
| 6 | `/task do readme-config-reference` | change | inline (one editing step) |
| 7, 8 | `/task create` a bug and a change | create | plan only |
| 9 | `/task list` | list | the table |

The expected path follows Do's small-task rule: inline when at most one
open step edits a host file. Task 5 is the Elephant-Goldfish case: the
worker does it, the reviewer reviews it.

## Running it

Requirements: herdr (each harness runs in its own pane), `claude`,
`opencode` (V2), `jq`. Models and effort come from a profile in
`tests/harness-bench/profiles/`:

- `sh.env`: Sonnet 5.5 supervisor, Haiku 5.5 worker, Sonnet 5.5 reviewer.
- `top.env`: Opus 5.5 supervisor and reviewer, Sonnet 5.5 worker (not yet
  run; the next round).

Every role thinks at the profile's `EFFORT` (the supervisor's): Claude Code
gets `--effort` and agent files without an `effort:` line; OpenCode gets the
variant written into each agent's model.

```bash
P=tests/harness-bench
# two herdr panes, one per harness
PC=$(herdr pane split --current --direction right --no-focus | jq -r .result.pane.pane_id)
PO=$(herdr pane split --pane "$PC" --direction down --no-focus | jq -r .result.pane.pane_id)
BENCH_PROFILE=top $P/run.sh claude   "$PC" 1 3 &
BENCH_PROFILE=top $P/run.sh opencode "$PO" 1 3 &
wait
BENCH_PROFILE=top ROLE_MODELS=supervisor=opus,worker=sonnet,reviewer=opus \
  python3 $P/summarize.py claude=r1,r2,r3 opencode=r1,r2,r3
```

Runs, logs, grades and metrics land in `$BENCH_DIR` (default
`~/tmp/harness-bench`), never in this repository. Start every new round at
fresh run numbers: Claude Code files its transcripts by directory, so a
reused run directory mixes two rounds. Claude Code asks once per new run
directory whether to trust it; `run.sh` accepts that only for the run's own
directory and stops on any other dialog.

## How a run is judged

`grade.py` reads only files: each task's status, ticked criteria, the
`Review:` and `Delegation:` lines, whether a worker ran and whether that was
the expected path, whether a worker round ticked a done-when box or wrote
the Outcome, the host diff (only `README.md` may change), and reference
answers computed from satty itself (the #689 cause, the `NEXTRELASE` fix,
the `copy-filepath` drift, every shortcut kept with a valid action name,
one row per `[general]` option with the right default). `metrics.py` takes
tokens, tool calls, the model and the effort of every session and
sub-agent from the transcripts (Claude Code) or the server (OpenCode).
`summarize.py` reports medians and ranges, and an estimated cost at list
prices.

Decision rule, fixed before a round: a cost or time difference counts only
when all runs of one harness beat all runs of the other; a correctness
difference only at two or more tasks.

## Results so far (2026-11-08, sh profile, 3 runs per harness)

| | Claude Code | OpenCode |
|---|---|---|
| Round 1, framework default effort: tasks, decisions | 18/18, 18/18 | 18/18, 18/18 |
| Round 1: cost per run, wall time | $2.22, 564 to 905 s | $1.30, 475 to 495 s |
| Round 2, every role at medium: tasks, decisions | 18/18, 17/18 | 18/18, 17/18 |
| Round 2: cost per run, wall time | $2.18, 514 to 750 s | $1.23, 552 to 609 s |

OpenCode was cheaper in both rounds (no overlap) and faster: clearly in
round 1, by median only in round 2 (563 s against 586 s, ranges overlap).
The cost difference is input, not output: Claude Code re-reads more than
twice the context per run (5.2M against 2.3M cache-read tokens for the
supervisor); output tokens were within a few percent.

## Known confounds

- With the "Claude Agent" login, OpenCode's tool calls run natively behind
  its provider (`executed: false` with a `native` block in the export). The
  comparison is Claude Code's CLI against the Claude engine inside OpenCode,
  with OpenCode's prompts, tools and plugin, not two independent agent
  loops. OpenCode with a direct Anthropic API key would test its own loop.
- Cost is an estimate at list prices; cache writes are taken as 1.25x input
  and Haiku's cache read as 0.1x input. Both harnesses ran on a
  subscription.
- Claude Code's 5-hour usage limit ended one round early; the driver now
  stops on the limit notice. A Sonnet round of three runs fits; a top-tier
  round may not, so run it in two sittings if needed.
- Three runs per harness: differences smaller than the run-to-run spread
  are noise.

## Next round: top tier

Profile `top.env`: Opus 5.5 supervisor and reviewer, Sonnet 5.5 worker,
every role at `medium`. Optionally a Fable 5.1 supervisor (edit the
profile). Same tasks, same decision rule, three runs per harness at fresh
run numbers. Record the result as a row in CONCEPT.md Part II.
