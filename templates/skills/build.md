---
description: Implement a change's spec: work the task checklist, review the diff, finish
---
Implement a planned change. Id: ${arg_ticket}

1. Load `.ai/changes/<id>/spec.md`; set `status: in-progress`. Read
   `.ai/notes.md` and, if the change spans areas you do not know, the
   `.ai/notes/map.md` leaf. Write `.ai/.current` (gitignored) with the
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
   Once `notes.md` passes ~1-2 screens, move topic clusters (largest
   first) into `.ai/notes/<topic>.md`, each leaving a one-line linked
   pointer (`- [topic](notes/<topic>.md) - hook`), until the hub is
   back under ~1 screen; do not split while notes stay short. Then a
   bounded drift check, not a re-explore: re-run `python3
   ${tools_dir}/probe.py` and compare its build/test/lint commands
   against the `GENERATED:project-context` section of `AGENTS.md`,
   and its module map against `.ai/notes/map.md` if that leaf exists.
   Update only for a changed command or a new, removed, or renamed
   module; a bare LOC delta is not actionable. Keep the AGENTS.md
   section under ~300 tokens. Last, confirm every leaf under
   `.ai/notes/` is linked from `notes.md` and every pointer resolves.
6. Set `status: done`, delete `.ai/.current`, and commit `.ai`
   (`build: <id>`).

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same task,
stop and rethink the approach rather than make a third blind attempt.
