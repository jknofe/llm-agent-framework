---
description: Opt-in: write a lightweight spec for a change the user wants specified and reviewed: goal, acceptance criteria, tasks
---
Write a spec for a change the user asked to have specified. Id and
title: ${arg_ticket}

1. Read `.ai/notes.md` (and any leaf under `.ai/notes/` the change
   touches) and explore the relevant code first.
2. Run a short, bounded Q&A with the user until the acceptance
   criteria are unambiguous. If no human is available (autonomous
   run), resolve each open question from the evidence and record it
   as a single numbered assumption in the spec Notes, then proceed.
3. Write `.ai/changes/<id>/spec.md`:
   ---
   id: <id>
   title: <title>
   status: planned
   created: <today>
   ---
   ## Goal               one paragraph: what and why
   ## Acceptance criteria
   - [ ] testable criterion
   Always include one criterion that the project's full test and
   lint commands pass, never only the test the task names: a fix
   that satisfies one test and breaks another is not done, and a
   criterion that names one test invites exactly that. Cover
   ecosystem correctness, not just "it runs": where a linter or
   policy check for the ecosystem you touch would catch a
   wrong-but-working result (eslint, mypy/ruff, clippy, shellcheck,
   lintian, a schema validator), name it and make passing it a
   criterion.
   ## Tasks
   - [ ] task - files: <paths>
   ## Notes              Q&A answers, decisions
4. Commit `.ai` (`spec: <id>`).

Do not implement yet; that is `/build <id>`. Show the spec and wait:
a plan the user can read and redirect before any code exists is what
this path is for. This skill runs only because the user asked for a
spec; it is not the default path for a change, and the agent never
starts one on its own.
