---
description: Implement a change's spec: work the task checklist, review the diff, finish
---
Implement a planned change. Id: ${arg_ticket}

1. Load `.ai/changes/<id>/spec.md`; set `status: in-progress`. Read
   `.ai/notes.md`, and any leaf under `.ai/notes/` the change touches.
   Write `.ai/.current` (gitignored, one per working tree) with the
   change id, the spec path, and the date, so the work can be resumed;
   keep its modified-files list current as you go. If the session is
   compacted, that file is the backup of exactly what to preserve.
2. Work the task checklist in order. Explore the real code with
   read/search tools as needed; do not load the whole tree.
3. Keep tests and lint green.
4. Review gate, sized to the change: before declaring the change
   done, check the full diff against the acceptance criteria.
   - One task in the checklist and a diff under roughly one screen:
     do the check inline against the criteria. No sub-agent.
   - Otherwise: have it reviewed in a fresh context. Run the
     `reviewer` sub-agent where the harness supports sub-agents. If
     it cannot be spawned (e.g. you are yourself a sub-agent) and no
     human is available, spawn a fresh general-purpose sub-agent
     given only the diff and the criteria; failing that, do a
     clean-context self-review and note that the `reviewer`
     sub-agent was unavailable.
   Either way, if the diff touches build, test, or CI wiring, also
   cross-check captured constraints: for each build, test, or CI
   gotcha in `.ai/notes.md`, confirm the diff honors it, not just
   that the acceptance criteria read as met. Fix gaps that affect
   correctness or the stated criteria; ignore style-only findings.
   Sizing down the gate is allowed; skipping it silently is not.
5. Record. Append any durable decision or gotcha to `.ai/notes.md`.
   Record a failing test as pre-existing only after it fails on a
   clean checkout of the base commit and you have read the test: a
   test that fails before your change because the same bug you are
   fixing also breaks it belongs in this change, not in the notes.
   Later sessions act on what is written here.
   Write only what the repository cannot state itself; a summary of
   code you just read is not durable knowledge.
   Once `notes.md` passes ~1-2 screens, move topic clusters (largest
   first) into `.ai/notes/<topic>.md`, each leaving a one-line linked
   pointer (`- [topic](notes/<topic>.md) - hook`), until the hub is
   back under ~1 screen; do not split while notes stay short. If this
   change altered a build, test, or lint command, update that line in
   the `GENERATED:project-context` section of `AGENTS.md` and keep the
   section under ~300 tokens. Last, confirm every leaf under
   `.ai/notes/` is linked from `notes.md` and every pointer resolves.
6. Set `status: done`, delete `.ai/.current`, and commit `.ai`
   (`build: <id>`).

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same task,
stop and rethink the approach rather than make a third blind attempt.
