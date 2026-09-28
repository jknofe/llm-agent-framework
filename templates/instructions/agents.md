# Agent: ${project_name}

Requirements only: the commands this project is checked with, the rules the
code cannot tell you, and the workflow entry points, ${entry_note}. Read the
source for structure. Normative text plain imperative, notes telegraphic;
identifiers, paths, and commands verbatim.

## Right-sizing
Do the task directly: read what you need, do it, run the project's full test
and lint commands if code changed, append to `.ai/notes.md` if a decision,
gotcha, or finding emerged, commit `.ai`. `/task-create` and `/task-do` are
opt-in, for a task the user wants planned in writing and reviewed. Never start
one on your own.

## Protocol
1. Read `.ai/notes.md` first. Durable knowledge goes there, appended,
   telegraphic: decisions and why, gotchas, unwritten rules, runbooks,
   pointers to sibling repos. The test for what belongs: the repository
   cannot state it itself. Never summarize code there. Open only the leaves
   under `.ai/notes/` that a task needs. When the user corrects you, or a
   check fails for a reason the code does not explain, record it there
   before moving on.
2. Code changed: the whole test and lint suite passes, not only the test a
   task names. A question: done = an answer citing its evidence, or
   "inconclusive" with what was ruled out.
3. `/task-create` and `/task-do` only when the user invokes them.
4. After changing `.ai/`, commit it in its own repo: `git -C .ai add -A &&
   git -C .ai commit -m "<summary>"`. Never commit `.ai` content to the host
   project repo.${hook_note}
5. `.ai/.current` (gitignored, one per working tree) is the resume pointer:
   `task: <id>`, task path, modified files. Read it at session start and
   offer to resume. Run `/task-do` in a fresh session, not the one that
   planned the task, and start an unrelated task in a fresh session:
   adherence to instructions decays as a session grows.
6. Never merge into the default branch unasked. Stop at the branch or pull
   request; the user merges.
7. Never add a co-author line to a commit message, even when the harness
   suggests one.

## Workflows
| Command | What it does |
|---|---|
| `/explore` | Ask what the code cannot tell you; record commands and rules below. |
| `/task-create <id> <title>` | Opt-in: plan a change, bug, investigation, or test. |
| `/task-do <id>` | Opt-in: work that plan, record findings, review, finish. |
| `/task-list-all` | Table of every task with type, status, progress. |
| `/framework-update` | Move this scaffold to the current framework version. |

## Tasks layout
```
.ai/tasks/<id>/task.md   # goal, done when, steps, findings, outcome, notes
.ai/notes.md             # running memory hub
.ai/notes/<topic>.md     # optional leaves, linked from notes.md
```
Frontmatter: `type: change|bug|investigation|test`,
`status: planned|in-progress|blocked|done`. Archive only on request: move
`tasks/<id>/` to `tasks/_archive/`, commit `.ai`.

${cli_note}## Project requirements

${gen_begin}
${generated_body}
${gen_end}
