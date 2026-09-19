# Framework 6.0 vs 5.26, cell 2 rust-package (Satty), Sonnet 5 x medium, 2026-09-14

Verification round for framework 6.0 (CONCEPT.md section 36: AGENTS.md as a
requirements file, module map on demand). Same cell, same SEED, TASK, GATE,
image, model and effort on both arms; the only variable is the generator
version used at SCAFFOLD. Gates re-run by the orchestrator; token numbers
from `count_tokens.py` on the isolated sub-agent transcripts. Informational,
never gating. n=1 per arm.

## Deviations from the runbook (disclosed)

1. **Dispatch.** Both arms ran as Task-tool sub-agents (`model: sonnet`,
   which the transcripts record as `claude-sonnet-5`) inside one orchestrator
   session, sequentially (5.26 first, then 6.0), the same shape as the
   2026-07-06 round. A headless `claude -p` launch was blocked by the
   session's permission classifier. Consequences: transcripts sit under the
   orchestrator's `subagents/` directory and were counted by isolating each
   agent's own file plus its reviewer sibling (`spawnDepth: 2`); the
   scaffolded Stop hook and allowlist did not fire for either arm because
   `$CLAUDE_PROJECT_DIR` was the orchestrator's repo, so both arms ran with
   the same tool access and neither had the hook as an advantage.
2. **SEED and SCAFFOLD were run by the orchestrator**, not the agent, because
   a sub-agent has no persistent cwd. The 5.26 scaffold was rendered from a
   git worktree at commit `2e68795` (the last 5.26 commit); the 6.0 scaffold
   from the working tree of this change. Both agents were told STEP 1 was
   done and verified the SHA and the stamp themselves.
3. **Effort** was encoded in the prompt text (the runbook's tier text); the
   `--effort` CLI flag is not available to a sub-agent.

## Configuration

| Field | Value |
|---|---|
| Cell | 2 rust-package (gabm/Satty at `2d18065ea534bd12792865784eed86a617ffbdc7`) |
| Model | claude-sonnet-5 (confirmed from transcript `model` field) |
| Effort | medium |
| Harness | claude |
| Gate image | satty-deb-builder |
| Date | 2026-09-14 |

## Results

| Arm | Gate | API calls (steps) | Output tokens | Total tokens | Duration | Deliverable |
|---|---|---|---|---|---|---|
| 5.26 | **PASS** | 39 + reviewer | 3,864 + 2 | 2,421,384 + 37,728 = **2,459,112** | 2m57s | Cargo.toml +21, Makefile +3 |
| 6.0 | **PASS** | 44 + reviewer | 7,004 + 9 | 2,696,908 + 127,413 = **2,824,321** | 2m36s | Cargo.toml +15, Makefile +3 |

Both gates re-run by the orchestrator: a `target/debian/satty_0.21.1-1_amd64.deb`
is produced on both arms and `dpkg-deb --contents` lists the binary,
`.desktop`, icon, all six completions and the man page on both.

Delta 6.0 vs 5.26: total tokens +15%, output tokens +81%, wall clock -12%.
The total sits inside the runbook's ~30-40% noise guardrail for n=1; the
output delta does not, and is explained below.

### Always-loaded context after `/explore`

| Arm | AGENTS.md words | Requirements/digest section | `.ai/notes.md` | `.ai/notes/map.md` |
|---|---|---|---|---|
| 5.26 | 1,247 | digest, ~240 words (purpose, stack, commands, conventions, module map, glossary) | 323 words | none |
| 6.0 | 655 | requirements, ~180 words (commands, CI gates, packaging, `ci-release` gotcha, doc pointers) | 318 words | 184 words |

6.0 halves what every turn loads and moves the map to a leaf the agent
opens on demand. The 6.0 agent reports reading `map.md` back during spec and
build for the `build.rs` and Makefile pointers, so the leaf was used, not
ignored.

### Where the extra output went

- **Explore wrote two files instead of one** (requirements block plus
  `map.md`), and its requirements block is denser than the 5.26 digest's
  command lines: it captured the `ci-release` gotcha, the CI workflow paths
  and the `make fix` lint line verbatim. That is the intended shape, and it
  costs output tokens once per project.
- **The 6.0 reviewer wrote a line-by-line cross-check** (127k total vs 38k):
  a fresh general-purpose sub-agent on both arms (the scaffolded `reviewer`
  agent type is not spawnable from a sub-agent, the documented fallback was
  used on both arms), but the 6.0 one read the Makefile and Cargo.toml
  itself instead of trusting the diff. Reviewer depth is agent variance, not
  a framework variable.
- **The 5.26 deliverable is larger, not smaller, in the wrong direction:** it
  added `section`, `priority`, `license-file`, `extended-description` and
  `depends`, which the runbook's TASK reserves for EFFORT=high. The 6.0
  deliverable is exactly the task (assets plus the Makefile target). Both
  pass the gate; the 6.0 diff is the one a medium-effort brief asked for.

## Verdict

1. **6.0 does not regress the cell.** Same PASS, same premise verification
   (both arms confirmed the `ci-release` claim against `build.rs` and the
   Makefile), same `.ai` commit chain (init, explore, spec, build), leaner
   deliverable, faster wall clock.
2. **6.0 does not lower the one-shot cost either**, and was not expected
   to: the ETH paper puts the context file's own cost effect at about +20%,
   and this framework's one-shot overhead over a bare agent (+391% on this
   cell in July) is the workflow, not the file. Halving AGENTS.md moved the
   total by +15% in the wrong direction at n=1, inside noise. The claim 6.0
   makes is the paper's: the digest was not paying for itself, so removing
   it costs nothing on the outcome. This cell is consistent with that.
3. **What would settle more:** the C arm added to the runbook (scaffold plus
   `/explore`, no workflow) on this cell and cell 1, and the Sonnet 5
   amortization pair in `amortization-playbook.md`. Neither ran today.

## Files

Raw per-arm results (configuration, spec, `.ai` history, full diff, full
gate output, observations, token blocks) under `results/`. Work dirs at
`/tmp/benchmark/runs/rust-package-{5.26,6.0}-2026-09-14/` are ephemeral.
