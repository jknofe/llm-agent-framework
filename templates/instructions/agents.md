# Agent: ${project_name}

Requirements only: the commands this project is checked with, the rules
the code cannot tell you, and the workflow entry points, ${entry_note}.
For structure, read the source with your read/search tools. Normative text
in plain imperative English, notes telegraphic; identifiers, paths, and
commands verbatim.

## Right-sizing
Do the task directly: read what you need, change it, run the project's full
test and lint commands, append to `.ai/notes.md` if a decision or gotcha
emerged, commit `.ai`. A spec and a review gate are opt-in: the user asks for
them with `/spec <id>` and `/build <id>`, for a change they want written down
and reviewed before it is called done. Do not start one on your own.

${goal_note}## Protocol
1. Read `.ai/notes.md` at the start of a task. Durable knowledge (decisions,
   gotchas, unwritten rules, runbooks, pointers to sibling repos) goes there,
   appended, telegraphic. If it lists leaves under `.ai/notes/`, open only
   the ones the task needs; `.ai/notes/map.md`, when present, is the module
   map from `/explore`.
2. Tests and lint must pass, the whole suite, not only the test a task
   names. Done = checks green.
3. When the user runs `/spec <id>`, write `.ai/changes/<id>/spec.md`; when
   they run `/build <id>`, implement it and review the diff against its
   criteria. Both are user-invoked steps, never a default.
4. After changing files under `.ai/`, commit them in its own repo:
   `git -C .ai add -A && git -C .ai commit -m "<short summary>"`. Never commit
   `.ai` content to the host project repo.${hook_note}
5. `.ai/.current` (gitignored) is the resume pointer: active change id, spec
   path, modified files. Read it at session start and offer to resume.

## Workflows
| Command | What it does |
|---|---|
| `/explore` | Record the build/test/lint commands and project rules below; map the code into `.ai/notes/map.md`. |
| `/spec <id> <title>` | Opt-in: write `.ai/changes/<id>/spec.md` for a change the user wants specified. |
| `/build <id>` | Opt-in: implement that spec's tasks, review the diff, finish. |
| `/tidy-up [scope]` | Hygiene sweep that may not change behavior. |
| `/framework-update` | Move this scaffold to the current framework version. |

## Changes layout
```
.ai/changes/<id>/spec.md   # goal, acceptance criteria, task checklist, notes
.ai/changes/_archive/      # finished changes; never load
.ai/notes.md               # running memory hub: decisions, gotchas, domain terms
.ai/notes/<topic>.md       # optional leaves, linked from notes.md
```
Status lives in the spec frontmatter (`planned|in-progress|done`). Archive
only when the user asks: verify `status: done`, move `changes/<id>/` to
`changes/_archive/`, commit `.ai`.

${cli_note}## Project requirements

${gen_begin}
${generated_body}
${gen_end}
