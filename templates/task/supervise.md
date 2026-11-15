# /task: Supervise

Read by `/task do` (`do.md`) when it hands the steps to a worker instead of
working them itself. It holds how you supervise: the hand-over, and how you
judge each report and continue the worker. Step numbers without a file name
are those of `do.md`.

The working steps are in `${task_dir}/steps.md`, and a worker does all of
them: the code, the tests, and every step the task names after them, a
commit, a push, a pull request, waiting for CI, a run in a dev environment. You stand in for
the user: you answer its questions, review its code before it ships, and
decide. You never do the work yourself: no host edit, commit or push, not
even to fix a review finding; that goes back to the worker.
The worker is the `worker` agent the framework defines beside
`reviewer`, started fresh, never one that inherits this conversation: it
knows only the files, so anything the user told you that the work depends
on goes into the task's Notes before it starts. Its model is the `model:`
line of its agent file, which `tasks.py models` checked: pass no model,
ever. Its prompt is always this one: `${worker_prompt}` ${worker_placement}
While the worker runs, change no file: wait for its report, the `Worker
round` line it ends with. Judge each report from the files, never from
the worker's message: the report line and every new Finding (a step
ticked without evidence is not done), `git status` and the diff. Trust
recorded evidence: a CI result on the pull request, or a command with its
result line in Findings (`Ran 9 tests ... OK`) is enough. Never run a
check yourself: when a command or its result is missing from Findings,
or contradicts the diff, send it back to the worker in a `Supervisor
round <n>` correction. Then answer by the report:
- `review`: run the review gate (`do.md` step 2) on the uncommitted diff. If it
  holds, append `- <today> Supervisor check: round <n> accepted: <what
  you checked>`; the worker then commits, pushes and opens the pull
  request. An accepted round is accepted as it is: attach no fixes to it.
  If not, append `- <today> Supervisor round <n>: <each correction: file,
  what is wrong, what done looks like>`. A correction that tells the
  worker to copy or follow something (a file, a sibling repository, a
  pattern) names it only after you have read it: it exists and says what
  you claim. A correction is only what keeps
  a Done-when criterion from being met or breaks something outside the
  task, and two test findings of `steps.md` step 4, which go back too: a
  change-detector test, and new or changed logic without a test.
  Everything else the review finds (a nicer structure, an extra test,
  robustness beyond the criteria, style) is one line, `- <today> Not
  sent back: <finding>`, and stays there unless the user asks for it.
- `question`: answer it as the user would, from the Goal, the Notes, the
  criteria and what the user told you, in a `Supervisor round <n>` line.
  Between options, take the smallest one that meets the Goal; never the
  larger one because it is more thorough. When you put a choice to the
  user, give each option with what it costs (rounds, lines, CI runs,
  risk) and recommend the smallest that meets the Goal.
  Ask the user first, with `${ask_tool}`, and change no file until they
  have answered, when the answer would change the Goal or a criterion, merge, touch
  production, delete data, or decide what the task file leaves open and
  you cannot. Write their answer into Notes and point the worker to it
  in the `Supervisor round <n>` line.
- `done`: check the evidence for every step, and that the covering
  tests and lint (`steps.md` step 4) are recorded and ran on the final code; take
  the worker's result line as given. When a step waited for CI, read
  its status yourself (on GitHub `gh pr checks <n>` or `gh run view
  <id>`): reading is not running. Never ask for the full suite. If
  something is missing or wrong, append a `Supervisor round <n>`
  correction. If code changed after the last accepted review, run the
  gate again first.
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
- No `Worker round` line because the worker hit its turn limit (the
  harness returns its output cut off or marked partial): an unfinished
  round, not a report. Read Findings for what it recorded, then continue
  the worker.

Commit `.ai` and continue the same worker in one turn, the two calls
together: it reads the file, not the commit. Continue it with its context (its Herdr
tab, or a sub-agent your harness can send a message to after it
reported); tell it to read `work.md` again, then Findings, and go on. Otherwise spawn a fresh worker with the same
prompt: the file holds everything it needs. When the worker reports
`done` and you accept it, append `- <today> Delegation: <model>,
<reports> report(s), <done|taken over|blocked>` to Findings, where
`<model>` is the `model:` line of the worker's agent file. Then go on at step 3 of `do.md`. The Outcome, the notes, the Done-when ticks and `finish` are
yours.
