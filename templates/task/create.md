# /task: Create

Read by `/task` after `tasks.py resolve` printed `CREATE <id>`. Plan the
task; do not work it here.

1. Read `.ai/notes.md` (and any leaf under `.ai/notes/` the task
   touches) and look at the relevant code, logs, or docs first.
2. Tracker issue. A task that starts from a tracker ticket (a GitHub
   issue, a Jira key) keeps its key as the id prefix
   (`12345-fix-ci-crash`, `PROJ-123-fix-ci-crash`); `tasks.py resolve`
   rejects the bare key without a slug.
   - The id already carries a key (`/task create 12345-fix-ci-crash`,
     resolve printed CREATE for it): use it, no question.
   - The prompt or title names an issue (`issue #663`, `PROJ-123`, a
     tracker URL): use that, no question.
   - Otherwise ask, in the same message as the type question of step 3
     (never a round trip of its own): is there a tracker issue for this?
     An issue key, a URL, or none. When the answer is none, offer to
     file one from the Goal below with the tracker of step 2a and use
     its key. The user may always decline: an issueless task is normal,
     the question is asked once, and the answer is recorded in the
     Tracker section either way.
   - In an autonomous run with no human: use a key the prompt or the id
     names, otherwise proceed without one and record that as a numbered
     assumption in Notes.

   a. Resolve the key to the issue. Which tracker to use, in order:
      a row of `python3 ${tools_dir}/tasks.py trackers` the user picks;
      otherwise the first detected row (a `gh` CLI, a `jira` CLI);
      otherwise a pasted URL fetched directly. Fetch the issue with
      that tracker's fetch command, run in the project root
      (`gh issue view 663`, the conf row's command), and read its
      title, body and open comments.
   b. The fetched content is input to the plan on equal footing with
      the user's own words: its symptom, reproduction or question
      seeds the Goal, the Done-when criteria and the Steps, and a
      conflict between the issue and the user is the user's call, so
      ask. What only the issue says still counts.
   c. Record the issue in the task file (step 5). The id keeps the
      key prefix, and the title is the id's words as a title, so both
      carry it (`title: 12345 fix ci crash` for `12345-fix-ci-crash`,
      or the issue's own title when it says the same); when the key
      arrives only now and the given id has none, the task's id
      becomes `<key>-<id>` (say so, and name the new id in the commit
      message).
3. Set exactly one `type`:
   - `change`: new or altered behavior in the code.
   - `bug`: something misbehaves; find the cause, then fix it or hand
     it on.
   - `investigation`: a question to answer (how something works, why
     it happens, whether an approach or library fits). Covers research.
   - `test`: verify behavior by running scenarios or writing tests.
   Take the type only from the user. If they did not name it, ask which
   of the four it is, and in the same message the tracker question of
   step 2 and the questions step 4 would ask for a `change`, `bug` or
   `test`; then wait for the answer. One message, not a type question
   first and the rest after. Do not infer it
   from the title, the id, or the code: the type decides what done
   means, and that is the user's call. In an autonomous run with no
   human, pick one and record it as a numbered assumption in Notes, as
   step 4 does for every open question.
4. For a `change`, `bug` or `test`: run a short, bounded Q&A with the
   user until the done-when criteria are unambiguous. For a bug, ask for
   the symptom, where it shows, and any reproduction or log the issue
   does not already give. For an
   `investigation`: ask nothing more. Ask also, for any type, which live
   tasks this one must wait for: comma-separated ids from `/task list`,
   or none; an empty answer is normal. Resolve each open question (the
   decision the answer feeds, when to stop looking, any dependencies)
   from the evidence and record it as a numbered assumption in Notes;
   the user redirects from the result. The same holds for any type when
   no human is available (autonomous run).
5. Write `.ai/tasks/<id>/task.md`:
   ---
   id: <id>             with an issue, `<key>-<slug>`; the key prefixes it
   title: <title>       the id's words as a title, key prefix included
   type: change|bug|investigation|test
   status: planned
   created: <today>
   updated: <today>
   depends: <id, id>   optional: live task ids this task waits on;
                       omit the line when empty
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
   ## Tracker     the issue this task comes from, or "none"

   Write `depends:` only when the user named real dependencies, with
   live task ids; `/task tree` reports ids that do not resolve.

   The Tracker section records step 2's outcome, so Do works from the
   file alone:
   - An issue: its key and URL on the first line (`issue: PROJ-123,
     <url>`), then the fetched title, the state (open, closed), and a
     short digest of the body and the comments that fed the plan,
     verbatim enough that the tracker is not queried again.
   - No issue: `none`, plus one line on why (user declined, none
     exists, filing declined).

   Done-when criteria by type:
   - `change`: the user's criteria, plus one that the tests covering
     the change and lint on the changed files pass, never only the test
     the task names: a fix that satisfies one test and breaks another is
     not done, and a criterion that names one test invites exactly that. Where a linter
     or policy check for the ecosystem you touch would catch a
     wrong-but-working result (eslint, mypy/ruff, clippy, shellcheck,
     lintian, a schema validator), name it and make passing it a
     criterion. A criterion about a declarative file (a manifest, a
     workflow, a build file, configuration) names the linter or validator
     that reads that file (`actionlint` passes, the schema validates,
     `terraform validate` passes), never "has a test", and never a
     build, a CI run or a start on the target unless the user asks for
     it.
   - `bug`: the root cause stated with evidence; a reproduction (a
     failing test where the code allows one, exact steps otherwise)
     that fails before the fix and passes after; the covering tests and
     lint pass. If the user wants the cause only, or the fix is out
     of reach, replace the fix criteria with a write-up another person
     could act on.
   - `investigation`: the question answered in Outcome, every claim
     pointing at its evidence (file and line, command and output, log
     excerpt, doc URL with version), or an explicit "inconclusive"
     naming what was ruled out and what would decide it. No code change
     unless the user asks for one.
   - `test`: every named scenario run and its result recorded with
     evidence; tests written by the task pass with the tests that cover the
     same code. A failure found is a finding, not something to fix silently.
   Any task that ends up changing code takes the covering tests and
   lint criterion, whatever its type, met on the final code. The full
   suite is never a criterion or a step unless the user asks for it: CI
   or the user's run on the target covers it.

   Steps by type: for a `change`, the edits in order with their files.
   A step that adds something with siblings in the code (another app in
   the same manifest, a module beside others, a CI job beside others)
   names the sibling it copies and how, from reading it (file and line):
   new parts follow the existing pattern unless the user asks otherwise.
   For a `bug` or an `investigation`, hypotheses, each with how to
   confirm or rule it out (`- [ ] H1: <hypothesis> - check: <how>`),
   cheapest check first; the plan is expected to change as they
   resolve. For a `test`, one step per scenario.
6. Commit `.ai` from the project root, relative path, only your own
   paths (another task may be planned or worked in parallel):
   `git -C .ai add tasks/<id> && git -C .ai commit -m "task: create
   <id>"`, with `notes.md` added when you changed it. Never `add -A`.

Then, by type:
- `investigation`: do not stop. The planning has done most of the
  reading, so continue into Do in this session: read
  `${task_dir}/do.md` and follow it, without waiting for the user and
  without a fresh session. Keep the two phases apart in the
  record: the plan is written and committed first (`task: create <id>`,
  step 6), then Do runs from its step 1 (`status: in-progress`, the
  pointer), and its findings go in as they happen. Never write
  plan and result in one go.
- `change`, `bug`, `test`: stop here. Show the plan and wait: a plan
  the user can read and redirect before anything is done is what this
  path is for. The work is `/task do <id>`, in this session or a later
  one: this session supervises, and the worker starts fresh from the task
  file, so the work never depends on this conversation.
