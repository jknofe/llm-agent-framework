---
description: Explore the codebase and fill the AGENTS.md project context plus .ai/notes.md
---
Explore this project to ground the agent.

- Run the deterministic inventory first: `python3
  ${tools_dir}/probe.py`. It prints host commit, language mix,
  detected build/test/lint commands, a module map (files + LOC),
  dependency manifests, and entry-point candidates. Seed the
  mechanical project-context fields from it; use its map to sample.
- Sample the code with your read/search tools (Read, Grep, Glob); do
  not load everything. Read entry points, each area's public API, and
  the tests. At this size the source is the knowledge base. Where the
  harness supports sub-agents, dispatch the sampling fan-out to them:
  each returns a condensed evidence map and keeps raw file dumps out
  of this context. Write the digest yourself; never let a sub-agent
  fill `AGENTS.md` or `notes.md` - digest errors compound across
  every later session.
- Fill the `GENERATED:project-context` section of `AGENTS.md`,
  condensed (cap ~1500 tokens): one-line purpose, tech stack,
  build/test/lint commands (highest priority), top conventions, a
  one-line-per-area module map, and core glossary terms.
- Ask the user about non-derivable knowledge (domain terms, unwritten
  rules, ownership); record the answers in `.ai/notes.md` (if it is
  already a hub with `.ai/notes/` leaves, read the hub first and
  update the matching leaf).
${hook_offer}- Commit `.ai` (`explore: project context`).

${arg_focus}
