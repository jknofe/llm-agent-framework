---
description: Tasks, opt-in: create (plan), do (work), list. With an id alone, a script decides whether to create or do it
---
Manage the task the user named. Arguments:
${arg_ticket}

A task is any unit of work: a code change, a bug to find and fix, a
question to investigate or research, a test campaign. The plan is the
same for all of them; what differs is what counts as done. This command
runs only because the user invoked it; it is not the default path for a
task, and the agent never starts one on its own.

## Dispatch

Read the first word of the arguments:
- `list`, or no arguments at all: go to List.
- `create <id> <title...>`: resolve `<id>`, then Create.
- `do [<id>]`: resolve `<id>` (none: the resume pointer), then Do.
- anything else is an id, maybe followed by a title: resolve it, and
  the verdict decides between Create and Do.

Resolve with the script, never by searching yourself:
`python3 ${tools_dir}/tasks.py resolve <id>`. Its first line is the
verdict; act on it:
- `CREATE <id>`: no such task. If `SIMILAR` lines follow, ask the user
  whether they meant one of those before creating a second one. Then
  Create; without a title, ask for one. After `do`, do not create:
  say the task does not exist and offer `create`.
- `DO <id> ...`: the task exists and is not done: Do, with the id
  exactly as printed. After `create`, do not overwrite it: say it
  exists and offer to work it.
- `DONE <id>`: finished. Say so with its title and stop; offer a new
  follow-up task instead of reopening it, unless the user asks to
  reopen.
- `ARCHIVED <id>`: archived. Say so and stop; do not create it again.
- `INVALID <text>`: not an id (a title without an id, for example).
  Propose a short kebab-case id, confirm it, and resolve again.
- `NONE`: `do` without an id and no resume pointer. Ask which task.

## Create

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
   of the four it is, before any other question, and wait for the
   answer. Do not infer it from the title, the id, or the code: the type
   decides what done means, and that is the user's call. In an
   autonomous run with no human, pick one and record it as a numbered
   assumption in Notes, as step 3 does for every open question.
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
  reading, so continue straight into Do in this session, without
  waiting for the user and without a fresh session.
- `change`, `bug`, `test`: stop here. Show the plan and wait: a plan
  the user can read and redirect before anything is done is what this
  path is for. The work is `/task do <id>`, in a fresh session: the task
  file is the handoff, so the work starts from it rather than from this
  conversation.

## Do

1. Load `.ai/tasks/<id>/task.md`; set `status: in-progress` and
   `updated: <today>`. Read `.ai/notes.md`, and any leaf under
   `.ai/notes/` the task touches. Write `.ai/.current` (gitignored, one
   per working tree) starting with the line `task: <id>`, then the task
   path and the date, so the work can be resumed; keep its
   modified-files list current as you go. If the session is compacted,
   that file and the Findings section are the backup of exactly what to
   preserve.
2. Work the steps in order. Explore the real code, logs, and docs with
   read/search tools as needed; do not load the whole tree. Tick a step
   when it is done.
3. Record findings as they happen, not at the end: append each to
   `## Findings`, dated, telegraphic, with its evidence (file and line,
   command and its output, log excerpt, doc URL). A finding the file
   does not hold is lost at the next session. Commit `.ai` after each
   finding that changes the direction of the task.
4. Re-plan openly. When a result invalidates the plan (a hypothesis is
   ruled out, a new lead appears, a scenario cannot run), edit `##
   Steps`: mark the dead step `- [x] ~~H1~~ ruled out: <evidence>`, add
   the new steps, and say so in Findings. Do not drift away from the
   written plan without changing it. If the new direction changes the
   Goal or a Done-when criterion, stop and ask the user: they approved
   the old ones. Mark the task `status: blocked` when it cannot continue
   without something outside your reach (hardware, access, another
   team): add a frontmatter line `blocked: <reason in one line>`, which
   `/task list` shows, and the detail in Findings. Remove the line
   when the task resumes.
5. Whenever the task changes code, keep the project's full test and
   lint commands green, whatever the task's type.
6. Review gate, sized to the result: before declaring the task done,
   check it against every Done-when criterion.
   - What to check: for a code diff, that it meets the criteria and
     changes nothing outside the task. For an Outcome (bug cause,
     investigation answer, test results), that every claim cites
     evidence recorded in Findings, that the evidence was produced in
     this task (the reproduction was run, the command was executed, the
     doc was read) rather than inferred, and that the answer fits the
     question in Goal. A task with both gets both checks. Whoever
     reviews opens every file-and-line citation in Findings and Outcome
     and confirms the source says what the claim says; a citation that
     does not hold is corrected, or its claim withdrawn.
   - How: size decides, not the number of steps. Check inline only
     when both the diff and the Outcome are under ~30 lines each (a task
     with no diff counts only its Outcome). If either is larger, the
     review goes to a fresh context, however simple it looks.
     A fresh context means, in this order: the `reviewer` sub-agent;
     where the harness has none, or it cannot be spawned (e.g. you are
     yourself a sub-agent), a fresh general-purpose sub-agent given only
     the task file and the diff. Try the sub-agent before falling back.
     Only when no sub-agent can be spawned at all, do a self-review, and
     say in the Findings line which option was unavailable and why. A
     self-review is the weakest check: work through the citations one by
     one instead of re-reading your own conclusion.
   If the diff touches build, test, or CI wiring, also cross-check
   captured constraints: for each build, test, or CI gotcha in
   `.ai/notes.md`, confirm the diff honors it. Fix gaps that affect
   correctness or the stated criteria; ignore style-only findings.
   Append one line to Findings, `- <today> Review: <kind>: <result>`,
   where kind is inline, `reviewer` sub-agent, fresh sub-agent, or
   self-review. Sizing down the gate is allowed; skipping it silently is
   not, and `/task list` flags a done task without this line.
7. Record.
   - Write `## Outcome`: the result in a few lines. A bug: the cause,
     the reproduction, the fix or who it was handed to. An
     investigation: the answer, or "inconclusive" with what was ruled
     out and what would decide it. A test: pass or fail per scenario.
   - Distill what the repository cannot state into `.ai/notes.md`,
     appended, telegraphic: decisions, gotchas, root causes, how a
     subsystem really behaves at runtime. Findings of a bug or an
     investigation usually belong there; a summary of code you just
     read does not.
   - Record a failing test as pre-existing only after it fails on a
     clean checkout of the base commit and you have read the test: a
     test that fails before your change because the same bug you are
     fixing also breaks it belongs in this task, not in the notes.
     Later sessions act on what is written here.
   - Once `notes.md` passes ~1-2 screens, move topic clusters (largest
     first) into `.ai/notes/<topic>.md`, each leaving a one-line linked
     pointer (`- [topic](notes/<topic>.md) - hook`), until the hub is
     back under ~1 screen; do not split while notes stay short. If this
     task altered a build, test, or lint command, update that line in
     the `GENERATED:project-context` section of `AGENTS.md` and keep
     the section under ~300 tokens. Last, confirm every leaf under
     `.ai/notes/` is linked from `notes.md` and every pointer resolves.
8. Tick each Done-when criterion the result meets, and each finished
   step. If a criterion stays open, the task is not done: meet it, get
   the user's agreement to drop it (record that in Notes), or mark the
   task `blocked`. Only with every criterion ticked and the `Review:`
   line in Findings, set `status: done` and `updated: <today>`, delete
   `.ai/.current`, and commit `.ai` (`task: done <id>`).

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same step, or
two hypotheses in a row die without a new lead, stop and rethink the
approach rather than make a third blind attempt.

## List

Run `python3 ${tools_dir}/tasks.py`, then copy its complete output into
your reply, verbatim, as the whole reply. The user does not see tool
output, so a reply that only refers to it ("the table is above") shows
them nothing. Add nothing, summarize nothing, and open no file: the
script reads the task files and its output is the whole answer. List is
read-only: change no file and commit nothing, and do not start or resume
a task from it.
