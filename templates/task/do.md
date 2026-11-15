# /task: Do

Read by `/task` after `tasks.py resolve` printed `DO <id>`, or by Create
for an investigation. Work the task from its file.

Change the task's status and its pointer only through
`python3 ${tools_dir}/tasks.py start` and `finish`, its `modified:` list
only through `tasks.py claim`, and tick a Done-when
criterion or a step only through `python3 ${tools_dir}/tasks.py tick <id>
done|steps <n> [<n>...]`, naming each item you checked; never with shell
redirects, in-place edits or a script that ticks every box at once.
`finish` takes the ticks and the commit along (step 4). Edit
the task file's sections with your file editing tool. Commit `.ai` from
the project root with the relative form and only your own paths,
`git -C .ai add tasks/<id> && git -C .ai commit -m "<message>"` (add
`notes.md` or a notes leaf when you changed one), never `add -A` and
never an absolute path: another task may be running in parallel, and
those are the forms the permission allowlist matches.

0. Before anything else, run `python3 ${tools_dir}/tasks.py models`, with
   `start` (step 1) behind it in the same command line:
   `python3 ${tools_dir}/tasks.py models && python3 ${tools_dir}/tasks.py
   start <id>`. `models` exits 1 on `MODELS MISSING`, so `start` then does
   not run. `models`
   checks that the `worker` and the `reviewer` each have a model chosen for
   this project, the `model:` line of their agent files. If its first line
   is `MODELS MISSING`, refuse: do not start the task, change no file, pick
   no model yourself, and tell the user which file needs which line, as the
   script prints it. The choice is the user's alone; a session's own model,
   a tier name or a default is never a substitute.
1. `tasks.py start <id>`, run with the models gate as step 0 says, sets
   `status: in-progress` and `updated:`, clears a `blocked:` line, and
   writes the task's pointer (gitignored): `.ai/.current`, the resume
   pointer, or `.ai/.current-<id>` when another task is running in
   parallel. It then names every task running in parallel (`PARALLEL`)
   with the files it claimed. The task file `.ai/tasks/<id>/task.md` is
   already in your context: `tasks.py resolve` printed it whole after its
   `DO` line, and a task Create just wrote you wrote yourself. Read it
   again only when that output was cut off. Its
   `## Tracker` section is the task's issue, already fetched at create
   time: work from what it records, and query the tracker again only when
   the task needs the issue's current state. Read `.ai/notes.md` unless it
   is in context, and any leaf under `.ai/notes/` the task touches.
   Decide worker or inline from the task file you have (below) and say
   which first; then run the models gate with `start`, and those reads,
   and `steps.md` (you work the task yourself) or `supervise.md` (a
   worker does) too, all in one turn.
   Before you edit a host file, claim it:
   `python3 ${tools_dir}/tasks.py claim <id> <path>...`.
   `CLAIMED ... by running task <other>` means a parallel task owns it:
   do not edit it; ask the user, or wait until that task finishes. If the
   session is compacted, the pointer and the Findings section are the
   backup of exactly what to preserve.

The working steps are in `${task_dir}/steps.md`. Work them yourself when
the user asked for `inline`, when no sub-agent can be spawned (you are one yourself, or the harness has
none), or when the task is small: at most one of its open steps changes
a host file, or none does (an investigation, a test campaign that only
records findings). Count the steps in the task file, not the files they
touch: two steps that edit the same file are two steps. Do not judge size
any other way, and documentation counts like code. When you work them
yourself, read `steps.md` in the turn of step 1, not in one of its own; where it says the
review gate runs, that is step 2 here. Your first line, before
any other tool call, names the decision and the count: `Inline: 1 of 3
steps edits a host file.` or `Worker: 3 of 4 steps edit host files.`
Otherwise a worker does the steps and you supervise: read
`${task_dir}/supervise.md` (in the turn of step 1) and follow it. It
holds how you hand the task over and how you judge, answer and continue
each report; a session that works the task itself never reads it.

When the user asks for more while the task runs, an ask outside the Goal
and the Done-when criteria as written, one that reopens a criterion
already ticked, or one that adds a repository, a pull request or a
production change: first offer to ship what meets the current criteria
and put the ask into a follow-up task (`/task create`), with what each way
costs. Fold it into this task only when the user says so; then write it
into Notes and the criteria with their words, and log it as `- <today>
User round <n>: <the ask>`, so Findings show the user's changes apart
from corrections.
A user redirect of how something is built makes the old design moot,
whether or not it changes a criterion: start no review of it, stop one
that is still running where your harness can, and carry none of its
findings into the new direction. Record it as `- <today> Dropped: the
round <n> design, replaced by User round <m>`.
A workaround for a denied permission (the user runs a push with `!`, does
a step by hand) is not a pattern for the rest of the task: record it with
its cause, `- <today> Workaround: <what>, because <the denial>`, and let
the worker take the normal way again in the next round, a new session or
after the user changed a setting; drop the workaround once that goes
through. Do not retry a denied action yourself: auto mode treats that as
a bypass.

2. Review gate, sized to the result: before code ships (`steps.md` step 1) and
   before declaring the task done, check it against every Done-when
   criterion.
   - What to check: for a code diff, that it meets the criteria and
     changes nothing outside the task. The task's diff is `git diff --`
     its claimed files, against the branch's base once committed; a
     changed file another running task claimed is that task's, not scope
     creep. For an Outcome (bug cause,
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
     A fresh context means the `reviewer` sub-agent, whose model is the
     `model:` line of its agent file: pass no model at spawn. If it cannot
     be spawned (you are yourself a sub-agent, or the harness has none),
     stop and ask the user: there is no fallback to another agent and no
     self-review of a result that needs a fresh context.
   - A review reads and runs nothing: no test, lint, build or run of the
     code. It judges the diff, the task file, the results recorded in
     Findings and the `evidence.md` a finding points at; a missing or contradicted result is a finding for the
     worker.
   If the diff touches build, test, or CI wiring, also cross-check
   captured constraints: for each build, test, or CI gotcha in
   `.ai/notes.md`, confirm the diff honors it. Gaps that affect
   correctness or the stated criteria get fixed, by the worker when one
   works the task; the rest is a `Not sent back` line, as above.
   Append one line to Findings, `- <today> Review: <kind>: <result>`,
   where kind is inline or `reviewer` sub-agent; an inline review of a diff over ~30 lines names why it
   is mechanical (`inline (mechanical: rename)`). Sizing down the gate is allowed; skipping it silently is
   not, and `/task list` flags a done task without this line.
3. Record. Everything this step and the review gate write into the task
   file (the Outcome, a `Review:` line or a `Delegation:` line not yet
   written) goes in with one edit, and the notes edits in the same turn.
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
4. Close the task in one call, after the edits of step 3:
   `python3 ${tools_dir}/tasks.py finish <id> done --tick-steps <n>...
   --tick <n>... --commit`, then give the final answer. `--tick` names each
   Done-when criterion the result meets, `--tick-steps` each finished step
   not yet ticked: only numbers you confirmed, criterion by criterion
   against the review and your checks, never all. Add `--add notes.md` (or
   `--add notes/<leaf>.md`) for each notes file you changed. `--commit`
   commits `.ai` with `tasks/<id>` and those paths only, as `task: done
   <id>` (`-m` sets another message). The call changes nothing and refuses
   when a number does not exist, a criterion stays unticked or the
   `Review:` line is missing; otherwise it ticks, sets `status: done`,
   deletes the task's own pointer (a parallel task's stays) and commits. If
   a criterion stays open, the task is not done: meet it, get the user's
   agreement to drop it (record that in Notes), or finish the task as
   `blocked`. Without `--commit`, `finish` prints the commit to run, and
   `tick <id> done|steps <n>...` stays available on its own.
