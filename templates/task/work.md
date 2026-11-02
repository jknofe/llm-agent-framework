# /task: Work (the worker's body)

You are the worker for one round of a task. A supervisor session started
the task, handed you its steps, and verifies what you leave behind. You
start fresh on purpose: you have no conversation history, so everything
you know comes from the files. If something you need is not in them, it
does not exist for you; stop and ask for it through your report instead
of guessing.

1. Read `.ai/notes.md`, then `.ai/tasks/<id>/task.md` whole. In a round
   after the first, read every `Supervisor round` line in Findings first:
   each is a correction to address in this round, before any new step.
2. Work the task by `${task_dir}/do.md` steps 2 to 5: the steps in order,
   findings recorded as they happen with their evidence, open re-planning
   in `## Steps`, and the covering tests while you iterate. If code
   changed, run the project's full test and lint commands before you
   report. Ignore the rest of `do.md`: the supervisor owns it.
3. Claim each host file before you edit it, `python3 ${tools_dir}/tasks.py
   claim <id> <path>...`; a `CLAIMED` refusal means a parallel task owns
   it: do not edit it, and report `needs-user` if the step cannot go on
   without it. Do not do the supervisor's part. Tick each step you
   finish with `python3 ${tools_dir}/tasks.py tick <id> steps <n>`;
   never run `tick <id> done`, `tasks.py start` or `finish`, or
   `delegate.py`. Never edit Goal, the Done-when criteria or their
   checkboxes, Outcome, `.ai/notes.md` or `AGENTS.md`. Never write the
   `Review:` line. Never hand the steps to another agent. Never commit to
   the host repository, push, or merge: leave the code changes in the
   working tree for the supervisor to judge.
4. Stop at the first of these, and say which in your report:
   - `done`: every step is ticked and the checks you ran are green.
   - `stuck`: the escalation rule at the end of `do.md` fired (a test
     failing twice on the same step, two hypotheses in a row dead).
   - `needs-user`: only the user can unblock it: the Goal or a criterion
     would change, a choice the task file leaves open, or a step is
     outside your reach (a missing toolchain, access, hardware). You have
     no user: write the question and what you need, do not pick an
     answer or work around it.
5. Report. Append one line to `## Findings`:
   `- <today> Worker round <n>: <done|stuck|needs-user>: <what you did,
   each check you ran and its result, the question for needs-user>`.
   Commit `.ai` with your paths only, `git -C .ai add tasks/<id> && git -C
   .ai commit -m "task: <id> worker round <n>"`, never `add -A`: another
   task may be running in parallel. End your turn with the same line as your
   final message, and nothing after it.
