# Phase 1: Initialization

Read this before analyzing the project.

## Strategy
- Run the deterministic inventory first: `python3 ${tools_dir}/probe.py`. It
  prints host commit, language mix, detected build/test/lint commands, a
  module map (files + LOC), dependency manifests, and entry-point candidates.
  Seed the mechanical `GENERATED:project-context` fields (stack, commands,
  module map) straight from it, and use its map to decide what to sample.
  Do not re-derive by hand what probe already reports.
- If a project description was seeded at init (overview node summary and the
  Project Context section), treat it as a hint, not a fact: use it to pick
  what to sample first, then verify and refine it against the code.
- Sample, do not scan everything: per module, read entry points, public API,
  and tests.
- Prefer the harness's native read and search tools (Read, Grep, Glob) over
  shell `grep`/`cat`/`awk`: same result, no permission prompts.${perms}
- Run exploration in isolated sub-agent contexts when the harness supports
  them. Each sub-agent returns a condensed summary of at most 2000 tokens.
  Keep raw file dumps out of the synthesizing context. KB nodes and the
  digest stay yours to write: never let a sub-agent fill them - digest
  errors compound across every later session.
- If you cannot spawn sub-agents (you are yourself a sub-agent, or a headless
  run without them), every raw file read lands in this one context, so explore
  is a full session on its own. Do not try to reach planning or implementation
  in the same session: sample the highest-value modules, build the KB, commit,
  and hand off. A fresh session resumes from the committed KB and `.ai/.current`.
- Build KB nodes bottom-up: module nodes first, then the architecture
  overview. Commit `.ai` after each node (or small batch), not once at the
  end: exploration is where the session budget runs out, and a per-node commit
  makes a mid-explore stop resumable instead of lost work.
- Record operational gotchas and runbooks you hit (build quirks, test-setup
  traps, CI requirements) in `.ai/notes.md`; reserve curated nodes for stable
  architecture and conventions.
- After node changes, update `manifest.yaml`. `INDEX.md` regenerates
  automatically: a PostToolUse hook runs `gen_index.py` on every manifest
  write. Never edit `INDEX.md` directly. If no hook fires (non-claude
  harness), run `python3 ${tools_dir}/gen_index.py` yourself.
${rules_line}- Regenerate the `GENERATED:project-context` section in AGENTS.md from the
  hot-tier nodes, condensed: project one-liner, tech stack, build/test/lint
  commands, top conventions, module map (one line per module plus cold-node
  ref), core glossary terms. Cap: 1500 tokens.

## Non-derivable knowledge
Ask the user about domain terms, unwritten conventions, and ownership.
Record the answers directly in the matching KB nodes.

## Autonomous mode
If no human is available to answer (headless or sub-agent run): do not block.
Decide each open question from the evidence in the code and configs, record it
as a single numbered assumption (the resolved decision, not your deliberation),
and proceed. Surface assumptions a maintainer would likely want to revisit.
${hook_offer}
## Incrementality
Record the commit SHA of the host repo in the overview node. A re-init
processes only changes since that SHA (`git log --name-only <sha>..HEAD`).

## Output
Produce a coverage report: areas read vs skipped (lazy-init candidates for
Phase 4).
