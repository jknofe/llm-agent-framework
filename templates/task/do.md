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
   with the files it claimed. Load `.ai/tasks/<id>/task.md`. Read
   `.ai/notes.md`, and any leaf under `.ai/notes/` the task touches.
   Before you edit a host file, claim it: `python3 ${tools_dir}/tasks.py
   claim <id> <path>...`. `CLAIMED ... by running task <other>` means a
   parallel task owns it: do not edit it; ask the user, or wait until that
   task finishes. If the session is compacted, the pointer and the
   Findings section are the backup of exactly what to preserve.

Steps 2 to 5 are the work, and a worker does them; you supervise. The
worker starts in a fresh context on a cheaper model and knows only the
files, so anything the user told you that the work depends on goes into
the task's Notes before it starts. Run `python3 ${tools_dir}/delegate.py
plan <id>` (add `inline` when the user asked for it) and act on MODE:
- `inline`: work steps 2 to 5 yourself, then go on at step 6.
- `herdr`: run `python3 ${tools_dir}/delegate.py launch <id>`, then the
  `herdr agent wait` command it prints. If launch prints `FAILED`, use
  `subagent` instead.
- `subagent`: spawn a fresh general-purpose sub-agent, never one that
  inherits this conversation, on MODEL where the harness lets you pick a
  model, with PROMPT as its whole prompt. Where no sub-agent can be
  spawned (you are one yourself, or the harness has none), work inline.
A worker on your own tier costs more than doing the work yourself, so
delegate only when MODEL is a cheaper tier than the model you run on.
When it is not, or you cannot tell (`auto`), work inline, unless the
user set `LLM_AGENT_WORKER_MODEL`. Whichever way, say the mode in one
line before you start.
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
  commit `.ai`, and run the next round (`plan`, then launch or spawn):
  every round is a fresh worker, so the correction must stand on its own
  in the file.
- `needs-user`: ask the user, write the answer into Notes, next round.
- `stuck`, or a fourth round would be needed: stop delegating. Work the
  rest yourself, ask the user, or finish the task as `blocked`.
- A Herdr wait that returns `blocked` is a dialog in the worker's tab:
  read it (`herdr agent read <name> --source recent-unwrapped --lines
  60`), never answer it for the user, tell them the tab and what it
  asks, and wait again. The wait fits one shell call (9 minutes; give
  the call that long a timeout). One that times out while the worker is
  still `working` is no failure: wait again. After an hour with no new
  Finding, read the tab and decide as for `stuck`.
After the last round, run `python3 ${tools_dir}/delegate.py close <id>`
(herdr only) and append `- <today> Delegation: <mode> <kind>/<model>,
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
