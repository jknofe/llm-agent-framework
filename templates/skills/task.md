---
description: Tasks, opt-in: create (plan), do (work), list. With an id alone, a script decides whether to create or do it
---
Manage the task the user named. Arguments:
${arg_ticket}

A task is any unit of work: a code change, a bug to find and fix, a
question to investigate or research, a test campaign. The plan is the
same for all of them; what differs is what counts as done. This command
runs only because the user invoked it; it is not the default path for a
task, and the agent never starts one on its own.

## Dispatch

Read the first word of the arguments:
- `list`, or no arguments at all: run `python3 ${tools_dir}/tasks.py`
  and reply with its complete output, verbatim, and nothing else. Do
  not read the script, the task files or the files below first; see
  List for why.
- `create <id> <title...>`: resolve `<id>`, then Create.
- `do [<id>]`: resolve `<id>` (none: the resume pointer), then Do.
- anything else is an id, maybe followed by a title: resolve it, and
  the verdict decides between Create and Do.

Resolve with the script, never by searching yourself:
`python3 ${tools_dir}/tasks.py resolve <id>`. Its first line is the
verdict; act on it:
- `CREATE <id>`: no such task. If `SIMILAR` lines follow, ask the user
  whether they meant one of those before creating a second one. Then
  Create; without a title, ask for one. After `do`, do not create:
  say the task does not exist and offer `create`.
- `DO <id> ...`: the task exists and is not done: Do, with the id
  exactly as printed. After `create`, do not overwrite it: say it
  exists and offer to work it.
- `DONE <id>`: finished. Say so with its title and stop; offer a new
  follow-up task instead of reopening it, unless the user asks to
  reopen.
- `ARCHIVED <id>`: archived. Say so and stop; do not create it again.
- `INVALID <text>`: not an id (a title without an id, for example).
  Propose a short kebab-case id, confirm it, and resolve again.
- `NONE`: `do` without an id and no resume pointer. Ask which task.

Create and Do live in their own files, read only when the verdict sends
you there; read the whole file before acting on it:
- Create: `${task_dir}/create.md`
- Do: `${task_dir}/do.md`


## List

Run `python3 ${tools_dir}/tasks.py`, then copy its complete output into
your reply, verbatim, as the whole reply. The user does not see tool
output, so a reply that only refers to it ("the table is above") shows
them nothing. Add nothing, summarize nothing, and open no file: the
script reads the task files and its output is the whole answer. List is
read-only: change no file and commit nothing, and do not start or resume
a task from it.
