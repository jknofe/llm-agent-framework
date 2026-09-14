# Agent: ${project_name}

Requirements only: the commands this project is checked with, the rules the
code cannot tell you, and the workflow entry points, ${entry_note}. Read the
source for structure. Normative text plain imperative, notes telegraphic;
identifiers, paths, and commands verbatim.

## Right-sizing
Do the task directly: read what you need, change it, run the project's full
test and lint commands, append to `.ai/notes.md` if a decision or gotcha
emerged, commit `.ai`. `/spec` and `/build` are opt-in, for a change the user
wants written down and reviewed before it is called done. Never start one on
your own.

## Protocol
1. Read `.ai/notes.md` first. Durable knowledge goes there, appended,
   telegraphic: decisions and why, gotchas, unwritten rules, runbooks,
   pointers to sibling repos. The test for what belongs: the repository
   cannot state it itself. Never summarize code there. Open only the leaves
   under `.ai/notes/` that a task needs.
2. Tests and lint must pass, the whole suite, not only the test a task
   names. Done = checks green.
3. `/spec <id>` writes `.ai/changes/<id>/spec.md`; `/build <id>` implements
   it and reviews the diff against its criteria. Both user-invoked, never a
   default.
4. After changing `.ai/`, commit it in its own repo: `git -C .ai add -A &&
   git -C .ai commit -m "<summary>"`. Never commit `.ai` content to the host
   project repo.${hook_note}
5. `.ai/.current` (gitignored, one per working tree) is the resume pointer:
   change id, spec path, modified files. Read it at session start and offer
   to resume.

## Workflows
| Command | What it does |
|---|---|
| `/explore` | Ask what the code cannot tell you; record commands and rules below. |
| `/spec <id> <title>` | Opt-in: specify a change the user names. |
| `/build <id>` | Opt-in: implement that spec, review the diff, finish. |
| `/framework-update` | Move this scaffold to the current framework version. |

## Changes layout
```
.ai/changes/<id>/spec.md   # goal, acceptance criteria, tasks, notes
.ai/notes.md               # running memory hub
.ai/notes/<topic>.md       # optional leaves, linked from notes.md
```
Spec frontmatter carries `status: planned|in-progress|done`, which is what
tells parallel changes apart. Archive only on request: move `changes/<id>/`
to `changes/_archive/`, commit `.ai`.

${cli_note}## Project requirements

${gen_begin}
${generated_body}
${gen_end}
