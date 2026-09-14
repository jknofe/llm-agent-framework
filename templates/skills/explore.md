---
description: Record the build/test/lint commands and project rules in AGENTS.md, map the code into .ai/notes/map.md
---
Ground the agent in this project. The always-loaded output is small on
purpose: only what changes how work is done here. A repository overview
does not make later tasks faster, so it is written on demand, not into
AGENTS.md.

1. Run the deterministic inventory: `python3 ${tools_dir}/probe.py`. It
   prints host commit, language mix, detected build/test/lint commands,
   documentation present, a module map (files + LOC), dependency
   manifests, and entry-point candidates.
2. Ask the user first, before sampling code, about what the code cannot
   tell you: the exact commands they run before pushing, tools this
   project must or must not use, unwritten rules, ownership, domain
   terms. If no human is available, record what probe found and note
   that the questions are open.
3. Fill the `GENERATED:project-context` section of `AGENTS.md`, cap ~300
   tokens, with requirements only:
   - build, test, and lint commands, verbatim, one line each (highest
     priority; confirm probe's detection against the real config).
   - tools and versions this project requires or forbids.
   - the user's rules from step 2.
   - if probe reports a README or `docs/` tree, one line pointing at it
     ("architecture: see docs/design.md"). Do not summarize what the
     repository already documents.
   No purpose paragraph, no module map, no glossary here.
4. Write the map to `.ai/notes/map.md`, telegraphic: one line per area
   (path, role, entry point), stack, and core glossary terms. Sample only
   what the map needs: entry points, each area's public API, the tests.
   Where the harness supports sub-agents, dispatch the sampling to them
   and have each return a condensed evidence list, never file dumps.
   Write the map yourself. Skip areas the project's own docs already
   cover; point at the doc instead. Add the pointer
   `- [map](notes/map.md) - module map, stack, glossary` to `.ai/notes.md`.
5. Record the user's answers that are not requirements (gotchas,
   runbooks, decisions) in `.ai/notes.md`, appended, telegraphic.
6. Commit `.ai` (`explore: project context`).
${hook_offer}
${arg_focus}
