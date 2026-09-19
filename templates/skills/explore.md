---
description: Ask what the code cannot tell you and record it as requirements in AGENTS.md
---
Ground the agent in this project. The always-loaded output is small on
purpose: only what changes how work is done here. A repository overview
does not make later tasks faster and is not written at all, here or
anywhere else. What pays is what the repository cannot state itself.

1. Run `python3 ${tools_dir}/probe.py` for a starting point: it prints the
   build/test/lint commands it can detect and the documentation the repo
   already has. Detection is a prompt for step 2, not an answer.
2. Ask the user, and treat their answers as authoritative over anything
   detected:
   - the exact commands they run before pushing, verbatim, flags included.
   - tools and versions this project requires or forbids.
   - unwritten rules: what must not be touched, what always breaks,
     ownership, release or migration order.
   - domain terms an outsider would read wrong.
   Keep it short and bounded. If no human is available, record what probe
   detected and note in `.ai/notes.md` that the questions are open.
3. Fill the `GENERATED:project-context` section of `AGENTS.md`, cap ~300
   tokens, with requirements only:
   - build, test, and lint commands, verbatim, one line each (highest
     priority; confirm probe's detection against the real config).
   - tools and versions this project requires or forbids.
   - the user's rules from step 2.
   - if probe reports a README or `docs/` tree, one line pointing at it
     ("architecture: see docs/design.md"). Do not summarize what the
     repository already documents.
   No purpose paragraph, no module map, no glossary.
4. Record the rest of the user's answers in `.ai/notes.md`, appended,
   telegraphic: gotchas, runbooks, decisions, domain terms, pointers to
   sibling repos. Do not write a summary of the codebase there; the code is
   read on demand and a digest of it was measured to help nothing.
5. Commit `.ai` (`explore: project context`).
${hook_offer}
${arg_focus}
