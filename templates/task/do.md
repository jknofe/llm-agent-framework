# /task: Do

Read by `/task` after `tasks.py resolve` printed `DO <id>`, or by Create
for an investigation. Work the task from its file.

Change the task's status and its pointer only through
`python3 ${tools_dir}/tasks.py start` and `finish`, its `modified:` list
only through `tasks.py claim`, and tick a Done-when
criterion or a step only through `python3 ${tools_dir}/tasks.py tick <id>
done|steps <n> [<n>...]`, naming each item you checked; never with shell
redirects, in-place edits or a script that ticks every box at once. Edit
the task file's sections with your file editing tool. Commit `.ai` from
the project root with the relative form and only your own paths,
`git -C .ai add tasks/<id> && git -C .ai commit -m "<message>"` (add
`notes.md` or a notes leaf when you changed one), never `add -A` and
never an absolute path: another task may be running in parallel, and
those are the forms the permission allowlist matches.

1. Run `python3 ${tools_dir}/tasks.py start <id>`: it sets
   `status: in-progress` and `updated:`, clears a `blocked:` line, and
   writes the task's pointer (gitignored): `.ai/.current`, the resume
   pointer, or `.ai/.current-<id>` when another task is running in
   parallel. It then names every task running in parallel (`PARALLEL`)
   with the files it claimed. Load `.ai/tasks/<id>/task.md`. Its
   `## Tracker` section is the task's issue, already fetched at create
   time: work from what it records, and query the tracker again only when
   the task needs the issue's current state. Read `.ai/notes.md`, and any
   leaf under `.ai/notes/` the task touches. Before you edit a host file,
   claim it: `python3 ${tools_dir}/tasks.py claim <id> <path>...`.
   `CLAIMED ... by running task <other>` means a parallel task owns it:
   do not edit it; ask the user, or wait until that task finishes. If the
   session is compacted, the pointer and the Findings section are the
   backup of exactly what to preserve.

Steps 2 to 5 are the work, and a worker does them; you supervise. The
worker is a fresh general-purpose sub-agent of your harness, never one
that inherits this conversation: it knows only the files, so anything the
user told you that the work depends on goes into the task's Notes before
it starts. Spawn it on a cheaper model than yours where the harness lets
you pick one, with this whole prompt: `You are the worker for task <id>,
round <n>. Read ${task_dir}/work.md and follow it.`, where `<n>` is one
more than the `Worker round` lines in Findings. Work steps 2 to 5 yourself
instead, then go on at step 6, when the user asked for `inline`, when two
or fewer steps are open in the first round, or when no sub-agent can be
spawned (you are one yourself, or the harness has none). Say which way in
one line before you start.
While a worker runs, change no file: wait for it. Then supervise the
round from the files, never from the worker's message: read the
`Worker round` line and every new Finding in the task file (a step
ticked without evidence is not done), read `git status` and the diff,
and if code changed, run the full test and lint commands yourself.
Decide:
- Accept when the report says `done` and your checks hold: go on at
  step 6. To record what you checked, write `- <today> Supervisor
  check: round <n> accepted: <checks>`, never a `Supervisor round` line:
  that form is a correction, and a later worker acts on it.
- Correct otherwise: append `- <today> Supervisor round <n>: <each
  correction: file, what is wrong, what done looks like>` to Findings,
  commit `.ai`, and spawn the next round's worker: every round is a fresh
  sub-agent, so the correction must stand on its own in the file.
- `needs-user`, or `stuck` on something outside the worker's reach (a
  toolchain, access, hardware, a decision): ask the user first, and
  change no file until they have answered. Then write the answer into
  Notes and run the next round, or finish the task as `blocked` if they
  say so.
- `stuck` on the work itself (a test failing twice, hypotheses dead), or
  a fourth round would be needed: stop delegating and ask the user how to
  go on: a corrected round, you taking over, or `blocked`. Take over only
  when they agree, and say so in one line before your first edit.
You edit host code yourself only to fix what the review gate finds
(step 6) or after the user agreed to a takeover; a worker's `stuck` or
`needs-user` alone is never the cue to finish its work.
When delegation ends (the round is accepted, the task is finished, or
the user agreed to a takeover), append `- <today> Delegation: <model>,
<rounds> round(s), <accepted|taken over|blocked>` to Findings. The
review gate, Outcome, notes and `finish` stay yours.

2. Work the steps in order. Explore the real code, logs, and docs with
   read/search tools as needed; do not load the whole tree. Tick a step
   when it is done (`tasks.py tick <id> steps <n>`).
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
   the old ones. When the task cannot continue without something outside
   your reach (hardware, access, another team), put the detail in
   Findings and run `python3 ${tools_dir}/tasks.py finish <id> blocked
   <reason in one line>`: it sets `status: blocked` and the `blocked:`
   line `/task list` shows, and keeps the pointer. `tasks.py start`
   clears the block when the task resumes.
5. Whenever the task changes code, whatever its type: iterate with the
   tests that cover the change, and have the project's full test and
   lint commands green before the review gate. While a task runs in
   parallel, the suite also sees its unfinished edits: a failure in a
   file that task claimed is not yours to fix; record it in Findings and
   rerun once that task finishes.
6. Review gate, sized to the result: before declaring the task done,
   check it against every Done-when criterion.
   - What to check: for a code diff, that it meets the criteria and
     changes nothing outside the task. The task's diff is `git diff --`
     its claimed files; a changed file another running task claimed is
     that task's, not scope creep. For an Outcome (bug cause,
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
   step, with `python3 ${tools_dir}/tasks.py tick <id> done <n>...`
   (`steps` for steps): name only the numbers you confirmed, criterion by
   criterion against the review and your checks. If a criterion stays open, the task is not done: meet it, get
   the user's agreement to drop it (record that in Notes), or finish the
   task as `blocked`. Then run `python3 ${tools_dir}/tasks.py finish <id>
   done`. It refuses while a criterion is unticked or the `Review:` line
   is missing; otherwise it sets `status: done`, deletes the pointer,
   and prints the commit to run (`task: done <id>`). Run it.
   The pointer it deletes is the task's own; a parallel task's stays.

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same step, or
two hypotheses in a row die without a new lead, stop and rethink the
approach rather than make a third blind attempt.
