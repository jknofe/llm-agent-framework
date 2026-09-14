# Framework 7.0 vs 6.1, cell 2 rust-package (Satty), Sonnet 5 x medium, 2026-09-14

Two arms per version: the framework arm (A, spec plus build plus review) and
the context-only arm (C, scaffold plus explore, then the task solved directly),
which is the path 7.0 makes the default. Four sessions total, all sequential.

Verification round for framework 7.0 (CONCEPT.md section 38: reduction to two
pillars). Same cell, same SEED, TASK, GATE, image, model and effort on both
arms; the only variable is the generator version used at SCAFFOLD. Gates
re-run by the orchestrator; token numbers from `count_tokens.py` on the
isolated sub-agent transcripts. Informational, never gating. n=1 per arm.

## Deviations from the runbook (disclosed)

1. **SCAFFOLD command corrected.** The runbook's cell 2 block still passes
   `--size small`, a flag removed with the large profile in framework 5.22.
   The flag was dropped for both arms; nothing else in the command changed.
   The runbook needs this fix in every cell block.
2. **Dispatch.** All four sessions ran as Task-tool sub-agents
   (`model: sonnet`) inside one orchestrator session, strictly sequentially
   (A 6.1, A 7.0, C 6.1, C 7.0), the same shape as the 2026-09-14 v6 round.
   Consequences are unchanged from that round: transcripts sit under the
   orchestrator's `subagents/` directory and were counted by isolating each
   agent's own file, plus its reviewer sibling (`spawnDepth: 2`) on the A arm,
   which has one; the scaffolded Stop hook and allowlist did not fire for any
   session, so all four ran with the same tool access. Only the Docker gates
   and the git clones were run concurrently; the runbook prohibits parallel
   agent dispatch and none happened.
3. **SEED and SCAFFOLD were run by the orchestrator**, not the agent, because
   a sub-agent has no persistent cwd. The 6.1 scaffold was rendered from a git
   worktree at commit `e670e5d` (the last 6.1 commit); the 7.0 scaffold from
   the working tree of commit `6cc6677`. Both agents were told STEP 1 was done
   and verified the SHA and the stamp themselves.
4. **Effort** was encoded in the prompt text; the `--effort` CLI flag is not
   available to a sub-agent.
5. **Arm shape.** The A arm's prompt forces STEP 3 (`/spec`) and STEP 4
   (`/build` plus review), i.e. the opt-in path, which keeps it comparable with
   the 5.26 and 6.0 rows below. The C arm was added in the same round to cover
   7.0's actual default path; its prompt is the runbook's pinned context-only
   prompt.
6. **Reviewer.** Neither arm could spawn the scaffolded `reviewer` sub-agent
   type from inside a Task-tool agent. Both fell back to a general-purpose
   sub-agent seeded with the reviewer's checklist, which is the escalation
   path the build skill documents. Identical on both arms.

## Configuration

| Field | Value |
|---|---|
| Cell | 2 rust-package (gabm/Satty at `2d18065ea534bd12792865784eed86a617ffbdc7`) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Harness | claude |
| Gate image | satty-deb-builder |
| Date | 2026-09-14 |

## Results

| Arm | Gate | API calls (steps) | Output tokens | Total tokens | Duration |
|---|---|---|---|---|---|
| 6.1 | **PASS** | 43 + 9 reviewer | 5,022 + 1,096 | 2,397,330 + 321,199 = **2,718,529** | 5m58s |
| 7.0 | **PASS** | 40 + 10 reviewer | 6,277 + 413 | 2,172,141 + 354,890 = **2,527,031** | 5m56s |

7.0 against 6.1: **-191,498 tokens (-7.0%)** in total, -225,189 (-9.4%) in the
agent's own session, 52 steps against 50. Output tokens rose (5,022 to 6,277);
the total is dominated by cache reads, which is where the saving sits.

Placed in the cell's existing series (earlier rounds, different orchestrator
sessions, so cross-round comparison is weaker than the 6.1 vs 7.0 pair):

| Version | Gate | Total tokens |
|---|---|---|
| 5.26 | PASS | 2,459,112 |
| 6.0 | PASS | 2,824,321 |
| 6.1 | PASS | 2,718,529 |
| 7.0 | PASS | 2,527,031 |

## Context-only arm (C): the default path

Same SEED, TASK, GATE, image, model and effort; scaffold and `/explore` as in
the A arm, then the task solved directly with no `/spec`, no `/build` and no
reviewer.

| Arm | Gate | API calls | Output tokens | Total tokens | Duration |
|---|---|---|---|---|---|
| C 6.1 | **PASS** | 26 | 2,569 | **1,085,592** | 3m09s |
| C 7.0 | **PASS** | 26 | 3,552 | **1,206,742** | 3m16s |

Both produce a package whose `dpkg-deb --contents` listing is identical to each
other and to the A arm's, 12 files.

**The two arms disagree in direction.** 7.0 is 7.0% cheaper than 6.1 on the A
arm and 11.2% **more expensive** on the C arm, from the same generator change,
the same cell and the same model. Step counts are flat (26 against 26). That
settles the interpretation of the A-arm delta: at n=1 this cell cannot resolve
a difference of that size, and neither number should be read as a saving or a
cost. What both arms do agree on is that nothing regressed.

**The price of the opt-in path, measured within each version.** This is the
round's most useful number and it does not depend on the version comparison at
all:

| Version | C (direct) | A (spec, build, review) | A / C |
|---|---|---|---|
| 6.1 | 1,085,592 | 2,718,529 | **2.5x** |
| 7.0 | 1,206,742 | 2,527,031 | **2.1x** |

The spec-build-review chain costs roughly twice the direct path on this cell.
Section 37 measured +74% to +160% for the same chain on later tasks in a Python
repo; this is +110% to +150% on a one-shot in a Rust packaging task. Different
ecosystem, different task shape, same order of magnitude. It is independent
support for making the chain opt-in, which is what 6.1 did and 7.0 kept.

## Deliverable

Both arms produced an equivalent change and an identical package.

| Arm | Diff | Package |
|---|---|---|
| 6.1 | Cargo.toml +14, Makefile +3, .gitignore +1 | `satty_0.21.1-1_arm64.deb` |
| 7.0 | Cargo.toml +15, Makefile +3, .gitignore +1 | `satty_0.21.1-1_arm64.deb` |

`dpkg-deb --contents` output is identical across all four sessions, path for
path: 12 files, the 11 declared assets plus the `copyright` file cargo-deb
generates. The declared assets are the binary at `usr/bin/satty`, the `.desktop` file, the SVG
icon, all six completions (bash renamed to `satty`, zsh, fish, elvish, nushell,
fig), the man page auto-gzipped to `satty.1.gz`, and the license. The one-line
diff difference is a blank line in `Cargo.toml` and where the `deb:` target was
placed in the `Makefile`; both call `cargo deb --no-build` off `build-release`.

## Observations

1. **No regression.** 7.0 passes the same gate with the same package from a
   four-skill scaffold. The cut commands, the removed map leaf and the reduced
   `probe.py` cost nothing on this cell.
2. **The cost delta is noise, and the C arm is what proves it.** Less framework
   text to read (4 skills instead of 7, AGENTS.md 394 words instead of about
   530, a probe that prints no map) should lower input and cache-read tokens.
   On the A arm it did, by 7%. On the C arm the same change went the other way
   by 11%. Two arms, opposite signs, one generator change: the effect is below
   this cell's resolution at n=1. Report neither as a saving.
3. **Both arms reported the same honest gap.** Neither could run `cargo fmt`,
   `clippy` or `cargo test` locally (no Rust or GTK toolchain outside the
   packaging container), so the full-suite acceptance criterion was satisfied
   by reasoning rather than execution, and both recorded that in `.ai` rather
   than marking it done silently. 6.1's rule that a failure is only
   pre-existing after a clean-checkout check is what produced the honest note;
   7.0 kept it.
4. **The default path is now covered.** The C arm removes the limitation the
   first half of this round had. Both paths pass, both produce the same
   package, and the direct path costs about half.
5. **The runbook is stale.** `--size small` in every cell block errors against
   any generator since 5.22. Fixing the cell blocks is a prerequisite for the
   next round, whoever runs it.

## What this round does not show

It does not show that 7.0 is cheaper or more expensive in general: n=1, one
cell, one model, and the two arms disagree in sign. It does not test the
control claim that section 38 stakes the framework on. That needs the
constraint round, which now has a runbook: `benchmarks/constraint-runbook.md`,
with its four pre-run controls verified and its gate test pinned at
`benchmarks/hidden-tests/test_hidden_constraint.py`. Not yet run.
