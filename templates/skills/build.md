---
description: Implement a change's spec: work the task checklist, review the diff, finish
---
Implement a planned change. Id: ${arg_ticket}

1. Load `.ai/changes/<id>/spec.md`; set `status: in-progress`. Read
   `.ai/notes.md`. Write `.ai/.current` (gitignored) with the change
   id, the spec path, and the date, so the work can be resumed.
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
5. Append any durable decision or gotcha to `.ai/notes.md`. If
   `notes.md` has grown past ~1-2 screens, move topic clusters
   (largest first) into `.ai/notes/<topic>.md`, each leaving a
   linked one-line pointer (`- [topic](notes/<topic>.md) - hook`),
   until the hub is back under ~1 screen, so later sessions read the
   hub first and open only the leaves they need; do not split while
   notes stay short. Then run the
   project-context refresh so the always-loaded digest cannot
   silently drift: re-run `python3
   ${tools_dir}/probe.py` and compare its build/test/lint commands
   and module map against the `GENERATED:project-context` section
   of `AGENTS.md`. Update that section only for a changed command or
   a new/removed/renamed module; a bare LOC delta on an existing
   module is not actionable, leave it. Keep it under ~1500 tokens.
   This is a bounded diff check, not a re-explore. One exception on
   the LOC rule: if probe's `Code LOC` line exceeds ~10k, tell the
   user this project has outgrown the small profile and propose
   re-initializing as large (hand-filled content is preserved);
   propose only, never migrate on your own. Last, if a
   `.ai/notes/` hub exists, confirm every leaf is linked from
   `notes.md` and every pointer resolves (no orphaned or dangling
   leaves).
6. Set `status: done`, delete `.ai/.current`, and commit `.ai`
   (`build: <id>`).

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same task,
stop and rethink the approach rather than make a third blind attempt.
