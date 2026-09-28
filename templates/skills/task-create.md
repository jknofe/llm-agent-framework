---
description: Opt-in: plan a task the user names (change, bug, investigation, test): goal, done-when, steps
---
Plan a task the user asked to have planned. Id and title:
${arg_ticket}

A task is any unit of work: a code change, a bug to find and fix, a
question to investigate or research, a test campaign. The plan is the
same for all of them; what differs is what counts as done.

1. Read `.ai/notes.md` (and any leaf under `.ai/notes/` the task
   touches) and look at the relevant code, logs, or docs first. If the
   id is missing, propose a short kebab-case one and confirm it.
2. Classify the task as exactly one `type`:
   - `change`: new or altered behavior in the code.
   - `bug`: something misbehaves; find the cause, then fix it or hand
     it on.
   - `investigation`: a question to answer (how something works, why
     it happens, whether an approach or library fits). Covers research.
   - `test`: verify behavior by running scenarios or writing tests.
   Ask when the user's words fit two types; the type decides done.
3. Run a short, bounded Q&A with the user until the done-when criteria
   are unambiguous. For a bug, ask for the symptom, where it shows, and
   any reproduction or log. For an investigation, ask what decision the
   answer feeds and when to stop looking. If no human is available
   (autonomous run), resolve each open question from the evidence and
   record it as a single numbered assumption in Notes, then proceed.
4. Write `.ai/tasks/<id>/task.md`:
   ---
   id: <id>
   title: <title>
   type: change|bug|investigation|test
   status: planned
   created: <today>
   updated: <today>
   ---
   ## Goal        one paragraph: what and why. Investigation: the
                   question, verbatim, and the decision it feeds.
   ## Done when
   - [ ] testable criterion
   ## Steps
   - [ ] step - where: <paths, logs, systems>
   ## Findings    empty; /task-do appends here
   ## Outcome     empty; /task-do writes the result here
   ## Notes       Q&A answers, decisions, assumptions

   Done-when criteria by type:
   - `change`: the user's criteria, plus one that the project's full
     test and lint commands pass, never only the test the task names: a
     fix that satisfies one test and breaks another is not done, and a
     criterion that names one test invites exactly that. Where a linter
     or policy check for the ecosystem you touch would catch a
     wrong-but-working result (eslint, mypy/ruff, clippy, shellcheck,
     lintian, a schema validator), name it and make passing it a
     criterion.
   - `bug`: the root cause stated with evidence; a reproduction (a
     failing test where the code allows one, exact steps otherwise)
     that fails before the fix and passes after; the full test and lint
     commands pass. If the user wants the cause only, or the fix is out
     of reach, replace the fix criteria with a write-up another person
     could act on.
   - `investigation`: the question answered in Outcome, every claim
     pointing at its evidence (file and line, command and output, log
     excerpt, doc URL with version), or an explicit "inconclusive"
     naming what was ruled out and what would decide it. No code change
     unless the user asks for one.
   - `test`: every named scenario run and its result recorded with
     evidence; tests written by the task pass together with the full
     suite. A failure found is a finding, not something to fix silently.
   Any task that ends up changing code takes the full test and lint
   criterion, whatever its type.

   Steps by type: for a `change`, the edits in order with their files.
   For a `bug` or an `investigation`, hypotheses, each with how to
   confirm or rule it out (`- [ ] H1: <hypothesis> - check: <how>`),
   cheapest check first; the plan is expected to change as they
   resolve. For a `test`, one step per scenario.
5. Commit `.ai` (`task: create <id>`).

Do not start the work yet; that is `/task-do <id>`, and it belongs in a
fresh session: the task file is the handoff, so the work starts from it
rather than from this conversation. Show the plan and wait: a plan the
user can read and redirect before anything is done is what this path
is for. This skill runs only because the user asked for a plan; it is
not the default path for a task, and the agent never starts one on its
own.
