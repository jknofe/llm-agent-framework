# W-arm comparison (W4: solo vs code-worker dispatch), sonnet-5 x medium, 2026-07-17

First execution of the runbook's worker arm. Both twins framework-scaffolded
(small profile), identical SEED (`sqlite-utils` @ `79117b9`), identical cell-4
TASK, identical `python:3.12` gate, MODEL claude-sonnet-5 x EFFORT medium,
bypass permissions, same round. Only variable: the /build execution mode
(one added prompt line per twin). Worker model from scaffolded frontmatter:
`model: sonnet` (same tier as MODEL, so this pair isolates delegation
mechanics/context hygiene, not a tier price gap). Gates re-verified by the
orchestrator; tokens from `count_tokens.py`. Informational, never gating.

## Comparison table

| Pair | Twin | Gate | Output tokens | Total tokens | API calls | Active duration | Cost (est.) |
|---|---|---|---|---|---|---|---|
| 4 py-feature | solo (control) | **PASS** (1085 passed, EXIT 0, re-verified) | 50,324 | 8,962,269 | 114 | ~16.3 min | ~$4.19 |
| 4 py-feature | worker | **PASS** (1088 passed, EXIT 0, re-verified) | 70,657 | 12,068,569 | 117 | ~14.1 min | ~$5.98 |

Delta worker vs solo: **+35% total, +40% output, +43% cost**, wall-parallel
active time slightly lower (-14%). Cost estimate at sonnet-5 list prices
(in $3/M, cache write $3.75/M, cache read $0.30/M, out $15/M).

## Dispatch evidence (transcript-verified, not self-reported)

- Solo twin: 0x `code-worker` (control held), 3x `reviewer` attempts (one
  flaky connection-error retry), 1x `general-purpose` (review fallback).
- Worker twin: 3x `code-worker`, 3x `general-purpose`, 1x `reviewer`.
  The scaffolded agent types were not visible at the resumed session's start,
  so early dispatches used the documented general-purpose fallback; when
  `code-worker` became available mid-run it closed two coverage gaps. Net
  effect: parts of the dispatch ceremony ran twice.

## Verdict (per the runbook's own criterion)

The worker twin cost more in BOTH total and output tokens at an equal gate
outcome, so **the strong delegation claim (net token win) FAILS this test** -
exactly the outcome CONCEPT SS23 flagged as possible ("the token saving is a
hypothesis, not a measurement") and SS13 predicts for small repos: dispatch
ceremony (brief construction, worker cold context, report-back,
re-verification) exceeded the discovery noise it kept out of the orchestrator
context on a ~10k-LOC repo.

Confounds that keep this one anecdote, not a closed case (deltas sit at the
~30-40% noise guardrail):

1. **Session-limit interruption.** The worker twin died at the usage limit
   after spec and resumed ~21h later; the resume replayed context (cache
   writes 383k vs solo's 220k are partly resume overhead, not delegation
   overhead).
2. **Agent-type availability lag** forced the double dispatch path
   (general-purpose first, code-worker later) - a harness artifact, not a
   framework property.
3. **Unequal deliverable.** The worker twin shipped MORE: 1088 vs 1085 tests,
   and its review chain found and fixed a second real bug the solo twin never
   saw (case-insensitive rename-collision leaking a raw
   `sqlite3.OperationalError` past the new `AlterError` guard, fixed at both
   guard sites). Equal-gate is not equal-scope here.

## Correctness divergence (reported alongside, same weight)

Both twins PASS, both confirmed the TASK's silent-data-loss premise by
reproduction before coding, both fixed it at the `transform_sql()` root. The
worker twin's independent review pass additionally caught the
case-insensitivity gap and verified the fix via a deliberate
revert-and-rerun. On this pair, delegation cost tokens and bought review
depth.

## Protocol deviations (recorded, honest)

- Solo twin paused for permission before its review gate despite the
  AUTONOMOUS RUN instruction; resumed with a reminder (same session).
- Worker twin hit the session limit mid-run; resumed after reset (same
  session, runbook rule).
- Both twins otherwise followed the small-profile chain
  (init -> explore -> spec -> build) with clean `.ai` commit sequences.

## Open

A W-pair on a medium/large repo (W5-class) and a tier-gap round (stronger
MODEL orchestrating the pinned sonnet worker) remain unmeasured; this pair
only prices delegation mechanics at constant tier on a small repo. A repeat
of W4 without a session-limit interruption would remove confound 1 cheaply.
