---
description: Show every task with its type, status, and progress as one table
---
Show the user every task in this project and where each one stands.

1. Run `python3 ${tools_dir}/tasks.py` and show its output as it is:
   one markdown table of every live task under `.ai/tasks/`, with
   type, status, title, checked steps, checked done-when criteria, and
   the last update. `>` marks the task `.ai/.current` points at.
   Archived tasks are only counted, never listed.
2. Below the table, add at most three lines, and only for what the
   table cannot show by itself: a task `in-progress` whose `updated`
   date is old, a `blocked` task with its reason from Findings, a
   `done` task with unchecked done-when criteria. Nothing else.

Read-only: change no file and commit nothing. Do not start or resume a
task from here; that is `/task-do <id>`, on the user's word.
