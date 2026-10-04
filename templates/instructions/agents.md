# Agent: ${project_name}

Requirements only: the commands this project is checked with, the rules the
code cannot tell you, and the workflow entry points, ${entry_note}. Read the
source for structure. Normative text plain imperative, notes telegraphic;
identifiers, paths, and commands verbatim.

## Right-sizing
Do the task directly: read what you need, do it, run the project's full test
and lint commands if code changed. Most direct tasks add nothing to
`.ai/notes.md`; append only what the repository cannot state, then commit
`.ai`. `/task` is opt-in, for work the user wants planned in writing and
reviewed; never start one yourself.

## Execution
- When a step needs no input, keep going; put status notes in the same
  message as the next action. Stop and ask only when blocked on the user, when
  a workflow says so, or before anything destructive: deleting data,
  force-pushing, changing anything outside this repository.
- An answered question is settled unless the user reopens it.
- End every run with the headings Blocked on me, Changed, Found.

## Protocol
1. Read `.ai/notes.md` first. Append durable knowledge there, telegraphic:
   decisions and why, gotchas, unwritten rules, runbooks, sibling-repo
   pointers. Never summarize code there. Open only the leaves under
   `.ai/notes/` that a task needs. When the user corrects you, or a check
   fails for a reason the code does not explain, record it there before
   moving on.
2. Code changed: the whole test and lint suite passes, not only the test a
   task names. A question: done = an answer citing its evidence, or
   "inconclusive" with what was ruled out.
3. After changing `.ai/`, commit it in its own repo: `git -C .ai add -A &&
   git -C .ai commit -m "<summary>"`. Never commit `.ai` content to the host
   project repo.${hook_note}
4. `.ai/.current` (gitignored, one per working tree) is the resume pointer:
   `task: <id>`, task path, modified files. Read it at session start and
   offer to resume. Run `/task do`, and any unrelated task, in a fresh
   session (an investigation runs in one go): adherence to instructions
   decays as a session grows.
5. Never merge into the default branch unasked. Stop at the branch or pull
   request.
6. Never add a co-author line to a commit message, even when the harness
   suggests one.

## Workflows
| Command | What it does |
|---|---|
| `/explore` | Ask what the code cannot tell you; record commands and rules below. |
| `/task create\|do\|list <id>` | Opt-in: plan, work, or list tasks (change, bug, investigation, test). |
| `/framework-update` | Move this scaffold to the current framework version. |

## Tasks layout
```
.ai/tasks/<id>/task.md   # plan and record of one task
.ai/notes.md             # running memory hub
.ai/notes/<topic>.md     # optional leaves, linked from notes.md
```
Archive only on request: move `tasks/<id>/` to `tasks/_archive/`, commit
`.ai`.

${cli_note}## Project requirements

${gen_begin}
${generated_body}
${gen_end}
