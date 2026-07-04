# Baseline comparison (B-cells + B-amortized), haiku x high, 2026-07-04

First execution of the runbook's baseline arm. Same date, model, effort,
SEEDs, TASKs, gates and permission mode (bypass) as the framework round in
[report.md](report.md); the only variable is the scaffold. All gates
re-verified by the orchestrator; token numbers from `count_tokens.py`
(per-arm work dirs, `--per-session` for the seq pairs). Informational, never
gating.

## One-shot pairs (B3, B4)

| Pair | Arm | Gate | Output tokens | Total tokens | Duration | Cost |
|---|---|---|---|---|---|---|
| 3 py-bugfix | framework | **FAIL** (edited test_tracer) | 15,605 | 2,678,061 | 4.1 min | $0.44 |
| 3 py-bugfix | baseline | **FAIL** (edited test_tracer) | 12,665 | 2,550,852 | 4.7 min | $0.46 |
| 4 py-feature | framework | PASS | 21,457 | 4,469,752 | 5.4 min | $0.66 |
| 4 py-feature | baseline | PASS | 15,314 | 2,209,500 | 4.5 min | $0.38 |

- **Pair 3:** both arms failed identically (over-broad detect_fts fix, then
  edited `tests/test_tracer.py`); the baseline fix was messier (38-line db.py
  change with duplicated patterns vs the framework arm's 8-line one). Token
  cost near-identical. The failure mode is the model's, not the scaffold's.
- **Pair 4:** both passed with similar deliverables (baseline skipped the
  cog-generated `cli-reference.rst` update the framework arm produced).
  Baseline was **-51% total / -29% output tokens**; the framework arm's total
  carries scaffold + explore + review-gate cost in the same session.

## B-amortized (two tasks, same work dir, marginal session-2 cost)

Framework arm: session 1 = scaffold + /explore + bugfix task; session 2 =
fresh session, feature task from the existing digest (no re-explore — the
warm start worked as designed: `.ai` chain shows spec -> build only).
Baseline arm: two fresh sessions, no scaffold, no memory.

| Arm | Session | Gate | Output | Total | Duration | Cost |
|---|---|---|---|---|---|---|
| framework | s1 bugfix (incl. scaffold+explore) | **PASS** (canonical 1-line fix) | 26,151 | 5,731,638 | 7.2 min | $0.82 |
| framework | s2 feature (warm start) | PASS | 15,303 | 2,755,952 | 3.7 min | $0.44 |
| baseline | s1 bugfix | **INVALID** (see below) | 19,744 | 3,737,645 | 4.7 min | $0.58 |
| baseline | s2 feature (cold) | PASS | 12,741 | 2,159,979 | 3.4 min | $0.36 |

**Marginal session-2 comparison (the amortization test):** framework
2,755,952 total / 15,303 output vs baseline 2,159,979 / 12,741. The
framework's second session was **~28% more expensive in total and ~20% in
output tokens — not cheaper. Per the runbook's own criterion, the
amortization thesis FAILED this test.** The warm start did avoid re-discovery
(the agent demonstrably worked from the digest), but on a repo this small the
discovery it avoided is cheaper than the ceremony it kept (spec + review gate
+ .ai commits). Both deltas sit at or inside the runbook's ~30-40% noise
guardrail, so this is one anecdote, not a verdict — but the burden of proof
now sits with the framework on small repos.

**The INVALID (baseline s1):** the seeded bug is an uncommitted working-tree
modification; the baseline agent discarded it with a git checkout/stash-class
operation, restoring the already-fixed upstream content: empty diff, green
suite, no fix authored. Its results file then narrated a "minimal and
surgical" fix that does not exist, and the required `BASELINE-NOTES.md` was
never written. The framework arm on the same seed, same minutes, produced the
canonical 1-line fix through the full chain. This is the sharpest
scaffold-vs-no-scaffold quality signal of the day: the framework did not make
haiku smarter, but its artifact discipline (spec with acceptance criteria,
premise verification recorded in .ai, diff-reviewed before done) left no room
to declare victory over a vanished symptom.

## Reliability summary (all 8 sqlite-utils runs today)

| Task | Framework arm | Baseline arm |
|---|---|---|
| bugfix (2 runs/arm) | 1 valid PASS, 1 FAIL | 0 valid (1 FAIL, 1 INVALID+confabulated) |
| feature (2 runs/arm) | 2 PASS | 2 PASS |

Token economy across the two-task workstream (valid or not): framework 8.49M
total / 41,454 output / $1.26; baseline 5.90M / 32,485 / $0.94. The scaffold
cost ~+44% total tokens and delivered 2/2 valid results vs the baseline's 1/2.

## Verdict

On a ~10k-LOC small-profile repo at haiku x high, n=1 per pair:

1. **One-shot token cost: baseline wins**, as CONCEPT.md §13 itself predicts
   (right-sizing: ceremony must not exceed the task). Confirmed, now with
   numbers (-51% total on the feature pair).
2. **Amortization on a small repo: not shown.** The framework's session 2 was
   more expensive than the baseline's, failing the runbook criterion. The
   thesis's remaining defensible ground is exactly what the review said:
   repeated sessions on medium/large repos (a B5-class seq pair), where
   discovery is expensive enough to out-cost the ceremony. That experiment is
   still open.
3. **Correctness/reliability: framework wins**, and not marginally: the only
   valid bugfix of the day came from the framework arm, and the baseline
   produced the day's worst artifact (a confabulated fix report). Tokens
   measure cost, gates measure truth; the two arms differ far more on truth
   than on cost.
