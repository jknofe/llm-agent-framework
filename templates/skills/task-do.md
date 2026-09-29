---
description: Work a planned task: follow its steps, record findings, review the result against done-when, finish
---
Work a planned task. Id: ${arg_ticket}

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
   `/task-list-all` shows, and the detail in Findings. Remove the line
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
     question in Goal. A task with both gets both checks.
   - How: one step and a result under roughly one screen, check inline.
     Otherwise have it reviewed in a fresh context. Run the `reviewer`
     sub-agent where the harness supports sub-agents. If it cannot be
     spawned (e.g. you are yourself a sub-agent) and no human is
     available, spawn a fresh general-purpose sub-agent given only the
     task file and the diff; failing that, do a clean-context
     self-review and note that the `reviewer` sub-agent was
     unavailable.
   If the diff touches build, test, or CI wiring, also cross-check
   captured constraints: for each build, test, or CI gotcha in
   `.ai/notes.md`, confirm the diff honors it. Fix gaps that affect
   correctness or the stated criteria; ignore style-only findings.
   Sizing down the gate is allowed; skipping it silently is not.
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
8. Set `status: done` and `updated: <today>`, delete `.ai/.current`,
   and commit `.ai` (`task: done <id>`).

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same step, or
two hypotheses in a row die without a new lead, stop and rethink the
approach rather than make a third blind attempt.
