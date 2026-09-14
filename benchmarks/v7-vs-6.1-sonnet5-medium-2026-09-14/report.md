# Framework 7.0 vs 6.1, cell 2 rust-package (Satty), Sonnet 5 x medium, 2026-09-14

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
2. **Dispatch.** Both arms ran as Task-tool sub-agents (`model: sonnet`)
   inside one orchestrator session, sequentially (6.1 first, then 7.0), the
   same shape as the 2026-09-14 v6 round. Consequences are unchanged from
   that round: transcripts sit under the orchestrator's `subagents/`
   directory and were counted by isolating each agent's own file plus its
   reviewer sibling (`spawnDepth: 2`); the scaffolded Stop hook and allowlist
   did not fire for either arm, so both ran with the same tool access.
3. **SEED and SCAFFOLD were run by the orchestrator**, not the agent, because
   a sub-agent has no persistent cwd. The 6.1 scaffold was rendered from a git
   worktree at commit `e670e5d` (the last 6.1 commit); the 7.0 scaffold from
   the working tree of commit `6cc6677`. Both agents were told STEP 1 was done
   and verified the SHA and the stamp themselves.
4. **Effort** was encoded in the prompt text; the `--effort` CLI flag is not
   available to a sub-agent.
5. **Arm shape.** The prompt forced STEP 3 (`/spec`) and STEP 4 (`/build`
   plus review), i.e. the opt-in path, on both arms. That keeps this round
   comparable with the 5.26 and 6.0 rows below, but it means the round does
   **not** measure 7.0's default path, which is direct. A C-arm round would.
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

## Deliverable

Both arms produced an equivalent change and an identical package.

| Arm | Diff | Package |
|---|---|---|
| 6.1 | Cargo.toml +14, Makefile +3, .gitignore +1 | `satty_0.21.1-1_arm64.deb` |
| 7.0 | Cargo.toml +15, Makefile +3, .gitignore +1 | `satty_0.21.1-1_arm64.deb` |

`dpkg-deb --contents` output is identical between the arms, path for path: 11
assets including the binary at `usr/bin/satty`, the `.desktop` file, the SVG
icon, all six completions (bash renamed to `satty`, zsh, fish, elvish, nushell,
fig), the man page auto-gzipped to `satty.1.gz`, and the license. The one-line
diff difference is a blank line in `Cargo.toml` and where the `deb:` target was
placed in the `Makefile`; both call `cargo deb --no-build` off `build-release`.

## Observations

1. **No regression.** 7.0 passes the same gate with the same package from a
   four-skill scaffold. The cut commands, the removed map leaf and the reduced
   `probe.py` cost nothing on this cell.
2. **The cost moved in the expected direction and the magnitude is not a
   signal.** Less framework text to read (4 skills instead of 7, AGENTS.md 394
   words instead of about 530, a probe that prints no map) should lower input
   and cache-read tokens, and it did, by 7%. At n=1, with cache reads as the
   dominant term, a 7% delta is within what two runs of the same arm could
   produce. It is a sanity check, not a measurement of savings.
3. **Both arms reported the same honest gap.** Neither could run `cargo fmt`,
   `clippy` or `cargo test` locally (no Rust or GTK toolchain outside the
   packaging container), so the full-suite acceptance criterion was satisfied
   by reasoning rather than execution, and both recorded that in `.ai` rather
   than marking it done silently. 6.1's rule that a failure is only
   pre-existing after a clean-checkout check is what produced the honest note;
   7.0 kept it.
4. **The forced opt-in path is the round's main limitation.** Both arms were
   told to run `/spec` and `/build`, which 6.1 and 7.0 both define as
   user-invoked. The round therefore measures the slimmed scaffold under the
   ceremony path, not the direct path that 7.0 makes the default.
5. **The runbook is stale.** `--size small` in every cell block errors against
   any generator since 5.22. Fixing the cell blocks is a prerequisite for the
   next round, whoever runs it.

## What this round does not show

It does not show that 7.0 is cheaper in general (n=1, one cell, one model), it
does not exercise the direct path, and it does not test the control claim that
section 38 stakes the framework on. That last one needs the constraint-carrying
round described in section 38 under "Next measurement": tasks whose gate can
only be passed by honoring a constraint the repository does not state.
