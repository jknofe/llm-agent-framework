# Benchmark Runbook: Two-Register Language A/B

Validates (or falsifies) CONCEPT.md §8: normative instructions in plain
imperative English + telegraphic KB content beats the alternatives. The claim
has two halves, so the A/B has three arms — same ticket, same model, same
effort, only the language register of the scaffold varies.

Status: specified, not yet run. Added in v5.6 (§17): §8 promised this
validation since v4; a spec'd-but-never-run validation is dead weight, so it
is now a runnable benchmark instead of a standing intention.

## Hypothesis

- H1 (content register): telegraphic KB content costs nothing — arm B
  (telegraphic content) shows no more escalations/re-plans than arm A
  (plain content), at ~20-30% fewer KB tokens.
- H2 (instruction register): telegraphic *instructions* are harmful — arm C
  (telegraphic normative docs) shows more misread-rule incidents (skipped
  gates, wrong artifact paths, missed commits) than A and B.

§8 predicts: B wins overall; C loses on process fidelity despite the lowest
token count. If B shows more escalations than A, the telegraphic content
register is falsified and §8 must be revised.

## Configuration (filled by user/orchestrator)

| Key | Value |
|---|---|
| RUN_ID | two-register-ab-YYYY-MM-DD |
| TARGET | reuse the Satty Debian-packaging task (satty-deb runbook) or another ticket with a known-good reference result |
| MODEL | one mid-tier model (e.g. sonnet); register effects drown in a strong model's error correction |
| EFFORT | medium (satty-deb tiers) |
| PROFILE | large (the KB is the subject under test) |
| REPEATS | ≥2 per arm; single runs cannot separate register effect from run noise |

## Arms

All arms start from the same `init-agent` scaffold and the same filled KB
content; only register differs. Prepare by rewriting the affected files once
per arm and committing each variant as a branch of `.ai`.

| Arm | Normative docs (AGENTS.md, phase docs) | KB content (nodes, ticket, summaries) |
|---|---|---|
| A | plain imperative (as scaffolded) | plain prose (rewrite: articles, sentences) |
| B | plain imperative (as scaffolded) | telegraphic (as §8 prescribes; the framework default) |
| C | telegraphic (rewrite: drop articles, symbols over words) | telegraphic |

Keep identifiers, paths, commands, and code blocks verbatim in every arm
(§8 exceptions). The rewrites must be information-preserving: same facts,
different register. Have a second model verify equivalence before running.

## Procedure

1. Scaffold the target repo (large profile), run /explore once, freeze the
   resulting `.ai` as the base commit.
2. Create the three arm variants as `.ai` branches (rewrites per table).
3. Per arm × repeat: fresh session, run /plan then /implement on the same
   ticket, autonomous mode (assumptions recorded, no human answers).
4. Collect per run: escalation count by type, re-plan events, review-gate
   findings, process-fidelity checklist (phase doc read? gates run? `.ai`
   committed? artifacts at the right paths?), total tokens (KB + docs +
   session), wall time, and the task result quality per the target's
   evaluation checklist.

## Evaluation

- Primary: escalation + re-plan rate per arm (H1: B ≤ A), process-fidelity
  violations per arm (H2: C > A,B).
- Secondary: token totals (expected ordering C < B < A) — only meaningful if
  the primary metrics hold; a cheaper arm that misreads rules is a loss.
- Write `report.md` in this folder, add the row to `benchmarks/README.md`,
  and update CONCEPT.md §8 with the outcome (confirm, or revise the policy).
