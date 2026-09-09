---
description: Write a lightweight spec for a non-trivial change: goal, acceptance criteria, task checklist
---
Write a spec for a non-trivial change. Id and title: ${arg_ticket}

1. Read `.ai/notes.md` and explore the relevant code first.
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
   Cover ecosystem correctness, not just "it runs": where a linter
   or policy check for the ecosystem you touch would catch a
   wrong-but-working result (eslint, mypy/ruff, clippy, shellcheck,
   lintian, a schema validator), name it and make passing it a
   criterion.
   ## Tasks
   - [ ] task - files: <paths>
   ## Notes              Q&A answers, decisions
4. Commit `.ai` (`spec: <id>`).

Do not implement yet; that is `/build <id>`. A change you can
describe in one sentence touching one or two files needs no spec:
edit it directly and update `.ai/notes.md` if a decision emerged.
