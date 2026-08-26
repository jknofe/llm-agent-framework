# Agent: ${project_name}

Project-aware agent (concept v5). KB = `.ai/knowledgebase/`. Token efficiency
is a hard requirement; this file stays under 2000 tokens. Phase instructions
live in `${phases_dir}/` and are loaded only when the phase runs
(${entry_note}). Write normative instructions in plain
imperative English; write KB content telegraphic. Keep identifiers, paths,
and commands verbatim.

## Phases

| Phase | Read first (mandatory, before any other step) |
|---|---|
| 1 Initialization | `${phases_dir}/init.md` |
| 2 Planning | `${phases_dir}/planning.md` |
| 3 Implementation | `${phases_dir}/implementation.md` |
| 4 Operational | none. Protocol below = default behavior |

Maintenance is not a phase. `/update` moves this scaffold to the current
framework version, merging the framework files and migrating the KB in place;
it never re-runs Phase 1. `/tidy-up [scope]` sweeps the host code for dead
code, obsolete files, overlong comments, and em dashes, and may not change
behavior; anything that would is a ticket.

Right-sizing: a change you can describe in one sentence and that touches a
single file needs no ticket. Do it directly, update the affected KB nodes,
and commit `.ai`. Use the ticket pipeline for everything larger, but for a
change confined to one self-contained area (e.g. a packaging descriptor or a
self-contained CLI subcommand), take
planning.md's trivial path: one task file, no Q&A rounds, and both review
gates sized down to an inline check against the criteria. Do not pay ceremony
that exceeds the task.
${goal_note}
## KB Protocol

1. Parse `.ai/knowledgebase/manifest.yaml` first. Never load all nodes.
2. Hot-tier content is embedded in the Project Context section below. Never
   load `tier: hot` nodes separately.
3. Match the task against `covers` globs and `tags` first (stage 1, exact).
   Only on a miss, keyword-score the manifest summaries (stage 2).
4. Budgets are soft targets: aim for at most 4 cold nodes / 6000 tokens per
   task, and follow `related` links at most 1 hop. If you must exceed a
   budget, state the reason in one line and proceed. Recall beats precision:
   never skip context you need just to stay under budget.
5. Never load `tasks/_archive/`.
6. Run exploration and review in sub-agent contexts when the harness
   supports them. Keep raw file dumps out of the main context.
7. Invariants: single source of truth, never duplicate. Split a node over
   ~1500 tokens and cross-link the parts.
8. `INDEX.md` is generated. To change it, edit `manifest.yaml` and run
   `python3 ${tools_dir}/gen_index.py`. Never edit `INDEX.md` directly.${rules_note}
9. External references: nodes under `references/` describe material in
   `.ai/external/` (other repos, docs, example code). Load the node first,
   then search the raw copy with targeted queries (in a sub-agent when
   available). Never bulk-load raw external material into context. If you
   find material in `.ai/external/` without a `references/` node, create
   the node (see the /add-reference skill for the format).
10. Persist `.ai` changes: after changing files under `.ai/`, commit them in
    its own repo with a short message, e.g.
    `git -C .ai add -A && git -C .ai commit -m "plan: JIRA-1234"`.
    Never commit `.ai` content to the host project repo.${hook_note}
11. Running memory: `.ai/notes.md` holds operational gotchas, runbooks
    (validation loops, CI quirks, merge-order rules), and unwritten rules too
    volatile for a curated node. Read it at session start; append
    telegraphically as you learn. Promote anything durable and structural into
    a KB node via `kb-delta.yaml`; keep `notes.md` as the volatile layer.
12. Task cursor: `.ai/.current` (gitignored working state) records the active
    ticket id, the current task file, the modified-files list, and the date.
    Read it at session start and offer to resume; update it when you start or
    finish a task; delete it when the ticket is done. It is the durable resume
    pointer across sessions, independent of compaction.
13. When compacting the session, always preserve: the current ticket id, the
    current task file path, the list of modified files, and the build/test
    commands (`.ai/.current` is the on-disk backup of exactly this).

## Ticket Layout

```
.ai/tickets/      # inbox: <ID>-<slug>.md (e.g. JIRA1234-do-this-and-that.md),
                  # added via /add-ticket or dropped in by the user
.ai/knowledgebase/tasks/<ticket-id>/
  ticket.md       # original ticket + recorded Q&A answers
  plan.md         # task index; frontmatter: read-first pointer, kb-commit
  NN-<slug>.md    # one file per task, self-contained
  kb-delta.yaml   # accumulated KB patches
.ai/knowledgebase/tasks/_archive/   # finished tickets; never load
```

Status in frontmatter (`planned|in-progress|done|blocked`), never in folder
names. `/plan <id>` turns an inbox ticket into `.ai/knowledgebase/tasks/<id>/`
(and promotes its `status` from `new` to `planned`).

Archive only when the user asks for it, then: verify every task file in
`.ai/knowledgebase/tasks/<id>/` has `status: done` (if not, list the open ones
and ask); verify `kb-delta.yaml` was applied to the KB; move it to
`.ai/knowledgebase/tasks/_archive/<id>/`; commit the `.ai` repo (`archive: <id>`).

${cli_note}## Project Context

${gen_begin}
${generated_body}
${gen_end}
