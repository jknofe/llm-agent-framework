# Phase 3: Implementation

Read this before executing any task.

## Load discipline
Load only: `plan.md`, the single current task file, its pre-bound KB nodes,
and the listed files. You may run at most 5 targeted searches beyond that.
Never load the whole ticket folder.

## Task cursor
At the start of a task, write `.ai/.current` (gitignored) with the active
ticket id, this task file, the modified-files list, and the date; refresh the
modified-files list as you edit. On task completion, point it at the next task;
when the ticket is done, delete it. A fresh session reads `.ai/.current` first
to resume exactly where the last one stopped.

## Drift check (diff-aware)
`plan.md` frontmatter records `kb-commit`, the `.ai` commit the plan was
built against. Before starting a task, check each pre-bound node for drift:
`git -C .ai diff <kb-commit> -- knowledgebase/<node path>`.
- Empty diff: proceed.
- Non-empty: read the diff. If it does not touch the task's interfaces or
  acceptance criteria, proceed on the fresh content. If it does, stop and
  re-plan the affected task only.
Never proceed silently on stale context. Never trigger a full re-plan for
cosmetic drift.

## Definition of done (per task)
- Tests pass and lint is clean
- Task frontmatter is `status: done`
- A KB patch is appended to `kb-delta.yaml`:
  `op: update|create|split`, `node: <id>`, `diff: <content>`

## Ticket review gate
After the last task is done, check the combined change against the acceptance
criteria in `ticket.md` and `plan.md` before declaring the ticket done. Size
the gate to the ticket:
- A ticket that took planning.md's trivial path (one task file, diff under
  roughly one screen): check it inline against the criteria, no sub-agent.
- Everything else: review it in a fresh context. Run the `reviewer` sub-agent
  on the full diff. If the harness cannot spawn it (e.g. you are yourself a
  sub-agent) and no human is available, spawn a fresh general-purpose
  sub-agent given only the diff and the criteria; if no fresh context is
  reachable at all, do a clean-context self-review against those criteria and
  record that the `reviewer` sub-agent was unavailable.

Fix gaps that affect correctness or the stated requirements; ignore
style-only findings. Where the diff touches build, CI, or packaging, the gate
also cross-checks captured constraints: for every gotcha recorded in
`.ai/notes.md` or the bound KB nodes, confirm the diff honors it. A change
that ignores a known build side effect or feature flag is a correctness gap
even when the acceptance criteria read as met. Record the outcome in
`plan.md` (`reviewed: <date>`). Sizing the gate down is a judgment call you
may make; silently skipping it is not.

## Parallel dispatch (optional)
Tasks marked `parallel: ok` in their frontmatter may be worked by concurrent
sessions, one task file per session. Constraints:
- Each session gets only its self-contained task file plus this doc; never
  share working context between parallel sessions.
- `.ai` stays single-writer: only the coordinating session updates `plan.md`
  status, `kb-delta.yaml`, `.ai/.current`, and makes `.ai` commits. Parallel
  workers report their result and proposed KB patch back instead of writing.
- Git worktrees of the host repo do not contain the gitignored `.ai/`; run
  parallel sessions in the same checkout (parallel-ok tasks touch disjoint
  files by definition) or copy `.ai/` into the worktree.
- The ticket review gate stays serial: one fresh-context review of the
  combined diff after the last task, never per worker.

## Escalation (typed; never improvise around a blocker)
- `missing-context`: use your bounded discovery first, then reload KB (1 hop,
  in a sub-agent when available). Still blocked: ask the user.
- `ambiguity`: ask the user.
- `test-fail` twice on the same task: stop. Have a fresh context (the
  `reviewer` sub-agent) critique the approach, or re-plan the task. Never
  make a third blind attempt.

## KB maintenance
- `kb-delta.yaml` auto-apply covers metadata and `covers` changes only.
  Structural changes go through the review gate.
- After hot-tier node updates, regenerate `GENERATED:project-context` in
  AGENTS.md. Before declaring the ticket done, run the project-context
  refresh so the always-loaded digest cannot silently drift: re-run
  `python3 ${tools_dir}/probe.py` and compare its build/test/lint commands and
  module map against that section. Refresh only for a changed command or a
  new/removed/renamed module; a bare LOC delta on an existing module is not
  actionable, leave it. This is a bounded diff check, not a re-explore.
- After `manifest.yaml` changes, `INDEX.md` regenerates automatically (a
  PostToolUse hook runs `gen_index.py`); run it by hand only on a non-claude
  harness. Never edit `INDEX.md` directly.
${rules_bullet}- ADRs (`decisions/`) are append-only. Supersede via link, never edit.
- Prune test (for every standing rule or instruction you maintain): if the
  agent already behaves correctly without it, delete it. Always-on
  instruction bloat is why real rules get ignored.
- Append operational gotchas and runbooks (validation loops, CI quirks,
  merge-order rules) to `.ai/notes.md` as you hit them; promote durable
  structural knowledge into a node via `kb-delta.yaml`. `notes.md` is the
  volatile layer, curated nodes are the source of truth.
- Staleness: `check_stale.py` lists nodes whose `covers` globs match host-repo
  commits newer than the node. A SessionStart hook runs it automatically; its
  output at session start flags nodes to refresh. Run
  `python3 ${tools_dir}/check_stale.py` by hand after a merge or on a non-claude
  harness.
