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
- `list`, or no arguments at all: List. Read no file first, not the
  script, the task files or the files below.
- `tree`: Tree.
- `create <id> <title...>`: resolve `<id>` and read `create.md` in the
  same turn, then act on the verdict: Create.
- `do [<id>] [inline|herdr]`: resolve `<id>` (none: the resume pointer)
  and read `do.md` in the same turn, then act
  on the verdict: Do. `inline` keeps the work in this session instead of a worker;
  `herdr` runs the worker in a Herdr tab instead of a sub-agent.
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
  exactly as printed. The task file follows in the output, whole
  between two `-----` lines: do not read it again. After `create`, do not overwrite it: say it
  exists and offer to work it.
- `DONE <id>`: finished. Say so with its title and stop; offer a new
  follow-up task instead of reopening it, unless the user asks to
  reopen.
- `ARCHIVED <id>`: archived. Say so and stop; do not create it again.
- `INVALID <text>`: not an id (a title without an id, an issue key
  without its slug, for example). Propose a short kebab-case id that
  keeps an issue key as its prefix (`12345-fix-ci-crash`), confirm it,
  and resolve again.
- `NONE`: `do` without an id and no resume pointer. Ask which task.

Create and Do live in their own files; read the whole file before acting
on it. For `create` and `do` read it in the turn of `resolve`, two tool calls
together; for a bare
id, only when the verdict sends you there:
- Create: `${task_dir}/create.md`
- Do: `${task_dir}/do.md`


## List

Run `python3 ${tools_dir}/tasks.py`, then copy its complete output into
your reply, verbatim, as the whole reply. The user does not see tool
output, so a reply that only refers to it ("the table is above") shows
them nothing. Add nothing, summarize nothing, and open no file: the
script reads the task files and its output is the whole answer. The
closing headings AGENTS.md asks for at the end of a run do not apply: end
on the script's last line. List is read-only: change no file and commit
nothing, and do not start or resume a task from it.

## Tree

Run `python3 ${tools_dir}/tasks.py tree` and answer as List does: its
complete output, verbatim, as the whole reply, no closing headings, no
file opened or changed, no task started or resumed. The tree shows which
live tasks wait on which, built from the `depends:` line of each task
file.
