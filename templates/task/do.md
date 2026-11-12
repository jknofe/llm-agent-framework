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

0. Before anything else, run `python3 ${tools_dir}/tasks.py models`. It
   checks that the `worker` and the `reviewer` each have a model chosen for
   this project, the `model:` line of their agent files. If its first line
   is `MODELS MISSING`, refuse: do not start the task, change no file, pick
   no model yourself, and tell the user which file needs which line, as the
   script prints it. The choice is the user's alone; a session's own model,
   a tier name or a default is never a substitute.
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

Steps 2 to 5 are the work, and a worker does all of it: the code, the
tests, and every step the task names after them, a commit, a push, a
pull request, waiting for CI, a run in a dev environment. You stand in for
the user: you answer its questions, review its code before it ships, and
decide. You never do the work yourself: no host edit, commit or push, not
even to fix a review finding; that goes back to the worker.
The worker is the `worker` agent the framework defines beside
`reviewer`, started fresh, never one that inherits this conversation: it
knows only the files, so anything the user told you that the work depends
on goes into the task's Notes before it starts. Its model is the `model:`
line of its agent file, which `tasks.py models` checked: pass no model,
ever. Its prompt is always this one: `You are the worker for task <id>.
Read ${task_dir}/work.md and follow it.` ${worker_placement}
Work steps 2 to 5 yourself instead when the user asked for `inline`, when
no sub-agent can be spawned (you are one yourself, or the harness has
none), or when the task is small: at most one of its open steps changes
a host file, or none does (an investigation, a test campaign that only
records findings). Count the steps in the task file, not the files they
touch: two steps that edit the same file are two steps. Do not judge size
any other way, and documentation counts like code. Your first line, before
any other tool call, names the decision and the count: `Inline: 1 of 3
steps edits a host file.` or `Worker: 3 of 4 steps edit host files.`
While the worker runs, change no file: wait for its report, the `Worker
round` line it ends with. Judge each report from the files, never from
the worker's message: the report line and every new Finding (a step
ticked without evidence is not done), `git status` and the diff. Trust
recorded evidence: a CI result on the pull request, or a command with its
result line in Findings (`Ran 9 tests ... OK`) is enough. Never run a
check yourself: when a command or its result is missing from Findings,
or contradicts the diff, send it back to the worker in a `Supervisor
round <n>` correction. Then answer by the report:
- `review`: run the review gate (step 6) on the uncommitted diff. If it
  holds, append `- <today> Supervisor check: round <n> accepted: <what
  you checked>`; the worker then commits, pushes and opens the pull
  request. An accepted round is accepted as it is: attach no fixes to it.
  If not, append `- <today> Supervisor round <n>: <each correction: file,
  what is wrong, what done looks like>`. A correction is only what keeps
  a Done-when criterion from being met or breaks something outside the
  task. Everything else the review finds (a nicer structure, an extra
  test, robustness beyond the criteria, style) is one line, `- <today>
  Not sent back: <finding>`, and stays there unless the user asks for it.
- `question`: answer it as the user would, from the Goal, the Notes, the
  criteria and what the user told you, in a `Supervisor round <n>` line.
  Between options, take the smallest one that meets the Goal; never the
  larger one because it is more thorough. When you put a choice to the
  user, give each option with what it costs (rounds, lines, CI runs,
  risk) and recommend the smallest that meets the Goal.
  Ask the user first, and change no file until they have answered, when
  the answer would change the Goal or a criterion, merge, touch
  production, delete data, or decide what the task file leaves open and
  you cannot. Write their answer into Notes and point the worker to it
  in the `Supervisor round <n>` line.
- `done`: check the evidence for every step, and that the one full test
  and lint run (step 5) is recorded and ran on the final code. When it
  was a CI run, read its status yourself (on GitHub `gh pr checks <n>`
  or `gh run view <id>`): reading is not running, and a CI result is the
  one claim you can check without a run. Without CI the worker's
  recorded result line is the only record; take it as given. If
  something is missing or wrong, append a `Supervisor round <n>`
  correction. If code changed after the last accepted review, run the
  gate again first. A `review` report needs only the covering tests:
  do not ask for the full suite before then.
- `stuck`, or the same correction needed a third time: ask the user how
  to go on: another round with a new direction, you taking over, or
  `blocked`. Take over only when they say so, and say so in one line
  before your first edit.
- `waiting`: the worker waits on something slow or on a person (CI that
  outlasts one blocking command, a merge, an approval, a deploy). Check
  that the wait is real, tell the user in one line what the task waits
  for and how to check it, and end your turn. Do not watch it yourself
  and do not do the step yourself. When the user says go on, continue
  the worker.

Commit `.ai`, then continue the same worker with its context (its Herdr
tab, or a sub-agent your harness can send a message to after it
reported); tell it to read Findings and go on. Otherwise spawn a fresh worker with the same
prompt: the file holds everything it needs. When the worker reports
`done` and you accept it, append `- <today> Delegation: <model>,
<reports> report(s), <done|taken over|blocked>` to Findings, where
`<model>` is the `model:` line of the worker's agent file. Then go on at step 7. The Outcome, the notes, the Done-when ticks and `finish` are
yours.

When the user asks for more while the task runs, an ask outside the Goal
and the Done-when criteria as written, one that reopens a criterion
already ticked, or one that adds a repository, a pull request or a
production change: first offer to ship what meets the current criteria
and put the ask into a follow-up task (`/task create`), with what each way
costs. Fold it into this task only when the user says so; then write it
into Notes and the criteria with their words, and log it as `- <today>
User round <n>: <the ask>`, so Findings show the user's changes apart
from corrections.

2. Work the steps in order. Explore the real code, logs, and docs with
   read/search tools as needed; do not load the whole tree. Tick a step
   when it is done (`tasks.py tick <id> steps <n>`). Code ships through
   the review gate: before its first commit, and before a push of code
   changed since the last review, step 6 runs on the uncommitted diff (a
   worker asks for it with a `review` report).
3. Record findings as they happen, not at the end: append each to
   `## Findings`, dated, telegraphic, one line of at most ~200
   characters: the claim and one pointer to its evidence (file and line,
   a command and its result line, a URL), never the evidence itself.
   Group checks of the same kind in one line (`checks: yamllint,
   xmllint, bash -n OK`). Evidence too long for that (a list of
   commands, a log, a summary of a document read) goes into
   `.ai/tasks/<id>/evidence.md`, and the finding points at it; often it
   is not worth keeping at all. Do not restate a rule, or what you did
   not do (`no merge, no push`): the rules hold without it.
   `tasks.py` flags a Findings line over 300 characters, except a
   `Supervisor round` line: a correction stays as long as it must to be
   exact. A finding the file does not hold is lost at the next session. Commit `.ai` after each finding that changes the
   direction of the task.
4. Re-plan openly. When a result invalidates the plan (a hypothesis is
   ruled out, a new lead appears, a scenario cannot run), edit `##
   Steps`: mark the dead step `- [x] ~~H1~~ ruled out: <evidence>`, add
   the new steps, and say so in Findings. Do not drift away from the
   written plan without changing it. If the new direction changes the
   Goal or a Done-when criterion, stop and ask the user: they approved
   the old ones (a worker asks with a `question` report). When the task
   cannot continue without something outside your reach (hardware,
   access, another team), put the detail in Findings and run `python3 ${tools_dir}/tasks.py finish <id> blocked
   <reason in one line>`: it sets `status: blocked` and the `blocked:`
   line `/task list` shows, and keeps the pointer. `tasks.py start`
   clears the block when the task resumes.
5. Whenever the task changes code, whatever its type: iterate with the
   tests that cover the change and lint on the changed files; that is
   also all a review round needs. Run the project's full test and lint
   commands once, on the final code, not after every change: a green CI
   run on the last push is that run; without CI, run them locally after
   the last code change, before `done`. While a task runs in
   parallel, the suite also sees its unfinished edits: a failure in a
   file that task claimed is not yours to fix; record it in Findings and
   rerun once that task finishes.
6. Review gate, sized to the result: before code ships (step 2) and
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
     worker, and the full suite runs once by step 5.
   If the diff touches build, test, or CI wiring, also cross-check
   captured constraints: for each build, test, or CI gotcha in
   `.ai/notes.md`, confirm the diff honors it. Gaps that affect
   correctness or the stated criteria get fixed, by the worker when one
   works the task; the rest is a `Not sent back` line, as above.
   Append one line to Findings, `- <today> Review: <kind>: <result>`,
   where kind is inline or `reviewer` sub-agent; an inline review of a diff over ~30 lines names why it
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
