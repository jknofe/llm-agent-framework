# /task: Do

Read by `/task` after `tasks.py resolve` printed `DO <id>`, or by Create
for an investigation. Work the task from its file.

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
5. Whenever the task changes code, whatever its type: iterate with the
   tests that cover the change, and have the project's full test and
   lint commands green before the review gate.
6. Review gate, sized to the result: before declaring the task done,
   check it against every Done-when criterion.
   - What to check: for a code diff, that it meets the criteria and
     changes nothing outside the task. For an Outcome (bug cause,
     investigation answer, test results), that every claim cites
     evidence recorded in Findings, that the evidence was produced in
     this task (the reproduction was run, the command was executed, the
     doc was read) rather than inferred, and that the answer fits the
     question in Goal. A task with both gets both checks. Whoever
     reviews opens every file-and-line citation the Outcome rests on and
     confirms the source says what the claim says; citations in Findings
     that the Outcome does not use (a ruled-out hypothesis, a side note)
     are spot-checked, up to three. A citation that does not hold is
     corrected, or its claim withdrawn.
   - How: size and kind decide, not the number of steps. Check inline
     when both the diff and the Outcome are under ~30 lines each (a task
     with no diff counts only its Outcome), or when the diff is
     mechanical: a rename, a move, a reformat, or a regenerated file,
     with no logic changed. Otherwise the review goes to a fresh context,
     however simple it looks.
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
   self-review; an inline review of a diff over ~30 lines names why it
   is mechanical (`inline (mechanical: rename)`). Sizing down the gate is allowed; skipping it silently is
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
