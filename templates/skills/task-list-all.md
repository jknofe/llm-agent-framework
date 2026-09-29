---
description: Show every task with its type, status, and progress as one table
---
Run `python3 ${tools_dir}/tasks.py`, then copy its complete output into
your reply, verbatim, as the whole reply. The user does not see tool
output, so a reply that only refers to it ("the table is above") shows
them nothing. Add nothing, summarize nothing, and open no file: the
script reads the task files and its output is the whole answer.

Read-only: change no file and commit nothing. Do not start or resume a
task from here; that is `/task-do <id>`, on the user's word.
