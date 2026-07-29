# Agent: ${project_name}

Small-project agent (concept v5, small profile). Token efficiency is a hard
requirement: keep this file dense and scannable. At this scale the source code
is the knowledge base, so explore it on demand with your read/search tools
(just-in-time) instead of maintaining a separate knowledge store. Workflow
entry points are ${entry_note}. Write normative instructions in plain imperative
English; write notes telegraphic. Keep identifiers, paths, and commands
verbatim.

## Right-sizing
A change you can describe in one sentence that touches one or two files needs
no spec: make it, update `.ai/notes.md` if a decision or gotcha emerged, and
commit `.ai`. Use `/spec` then `/build` for everything larger.

${goal_note}## Protocol
1. Explore the codebase with native read/search tools (Read, Grep, Glob), not
   by loading everything. The source is the knowledge base. Check the Project
   Context section below first: if it still holds only the seed one-liner (or
   the raw `<!-- Populated by /explore -->` marker) with no module map or
   build/test/lint commands, `/explore` was never run. Run it before non-trivial
   work: a stale or missing digest costs more discovery tokens over the
   session than the one-time `/explore` pass.
2. Durable knowledge (decisions, gotchas, domain terms, unwritten rules,
   operational runbooks, pointers to related repos/paths this project depends
   on, e.g. a sibling repo's venv used for tests, or prior-art to mirror) goes
   in `.ai/notes.md` (append, telegraphic). Read it at the start of a task.
   Architecture/module-map knowledge belongs in the Project Context section
   instead (`/explore`'s output). Never duplicate it here. `notes.md` may grow
   into a hub: once it passes ~1-2 screens, move topic clusters (largest first)
   into `.ai/notes/<topic>.md`, each leaving a one-line linked pointer
   (`- [topic](notes/<topic>.md) - hook`) behind, until the hub is back under
   ~1 screen. Then read the hub first and open only the leaves a task needs;
   keep the pointer list in sync (add on split, remove on delete). Do not split
   while notes stay short - one file is cheaper to read whole than an index
   plus a leaf.
3. Non-trivial work: `/spec <id>` writes `.ai/changes/<id>/spec.md` (goal,
   acceptance criteria, task checklist); `/build <id>` implements it.
4. Before declaring a change done, have the full diff reviewed in a fresh
   context against the acceptance criteria: the `reviewer` sub-agent where
   available; in an autonomous run, a fresh general-purpose sub-agent or, if
   none is reachable, a recorded clean-context self-review. The review also
   confirms the diff honors every build/CI gotcha recorded in `.ai/notes.md`,
   not just the acceptance criteria. Fix correctness gaps; ignore style-only
   findings.
5. Tests and lint must pass. Done = checks green and review clean.
6. After changing files under `.ai/`, commit them in its own repo:
   `git -C .ai add -A && git -C .ai commit -m "<short summary>"`. Never commit
   `.ai` content to the host project repo.${hook_note}
7. Task cursor: `.ai/.current` (gitignored working state) records the active
   change id, the spec file path, the modified-files list, and the date. Read
   it at session start and offer to resume; update it when you start or finish
   a change; delete it when the change is done. It is the durable resume
   pointer across sessions, independent of compaction.
8. When compacting the session, preserve: the current change id, the spec file
   path, the list of modified files, and the build/test commands
   (`.ai/.current` is the on-disk backup of exactly this).

## Workflows
| Command | What it does |
|---|---|
| `/explore` | Sample the code; fill the Project Context below and `.ai/notes.md`. |
| `/spec <id> <title>` | Write `.ai/changes/<id>/spec.md` for a non-trivial change. |
| `/build <id>` | Implement the spec's tasks, review the diff, finish. |
| `/tidy-up [scope]` | Hygiene sweep that may not change behavior: dead code, obsolete files, comments, em dashes. |
| `/update` | Move this scaffold to the current framework version, keeping what the project knows. |

## Changes layout
```
.ai/changes/<id>/spec.md   # goal, acceptance criteria, task checklist, notes
.ai/changes/_archive/      # finished changes; never load
.ai/notes.md               # running memory hub: decisions, gotchas, domain terms
.ai/notes/<topic>.md       # optional leaves, linked from notes.md once it grows
```
Status lives in the spec frontmatter (`planned|in-progress|done`), never in
folder names. Archive only when the user asks: verify `status: done`, move
`changes/<id>/` to `changes/_archive/`, commit `.ai`.

${cli_note}## Project Context

${gen_begin_small}
${generated_body}
${gen_end}
