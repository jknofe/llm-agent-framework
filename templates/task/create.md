# /task: Create

Read by `/task` after `tasks.py resolve` printed `CREATE <id>`. Plan the
task; do not work it here.

1. Read `.ai/notes.md` (and any leaf under `.ai/notes/` the task
   touches) and look at the relevant code, logs, or docs first.
2. Set exactly one `type`:
   - `change`: new or altered behavior in the code.
   - `bug`: something misbehaves; find the cause, then fix it or hand
     it on.
   - `investigation`: a question to answer (how something works, why
     it happens, whether an approach or library fits). Covers research.
   - `test`: verify behavior by running scenarios or writing tests.
   Take the type only from the user. If they did not name it, ask which
   of the four it is, and in the same message the questions step 3 would
   ask for a `change`, `bug` or `test`; then wait for the answer. One
   message, not a type question first and the rest after. Do not infer it
   from the title, the id, or the code: the type decides what done
   means, and that is the user's call. In an autonomous run with no
   human, pick one and record it as a numbered assumption in Notes, as
   step 3 does for every open question.
3. For a `change`, `bug` or `test`: run a short, bounded Q&A with the
   user until the done-when criteria are unambiguous. For a bug, ask for
   the symptom, where it shows, and any reproduction or log. For an
   `investigation`: ask nothing more. Resolve each open question (the
   decision the answer feeds, when to stop looking) from the evidence
   and record it as a numbered assumption in Notes; the user redirects
   from the result. The same holds for any type when no human is
   available (autonomous run).
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
   ## Findings    empty; Do appends here
   ## Outcome     empty; Do writes the result here
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

Then, by type:
- `investigation`: do not stop. The planning has done most of the
  reading, so continue into Do in this session: read
  `${task_dir}/do.md` and follow it, without waiting for the user and
  without a fresh session. Keep the two phases apart in the
  record: the plan is written and committed first (`task: create <id>`,
  step 5), then Do runs from its step 1 (`status: in-progress`,
  `.ai/.current`), and its findings go in as they happen. Never write
  plan and result in one go.
- `change`, `bug`, `test`: stop here. Show the plan and wait: a plan
  the user can read and redirect before anything is done is what this
  path is for. The work is `/task do <id>`, in a fresh session: the task
  file is the handoff, so the work starts from it rather than from this
  conversation.
