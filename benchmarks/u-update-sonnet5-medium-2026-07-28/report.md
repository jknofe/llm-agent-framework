# U-cell round: /update on a legacy scaffold (sonnet-5, medium, 2026-07-28)

First behavior test of the `/update` skill introduced in v5.14. Not one of the
7 fixed cells: those exercise explore -> spec -> build, which `/update` never
touches. The artifact under test is a framework update, so the cell is defined
here.

## Cell U1 - update-legacy (Satty, small)

Reuses cell 2's target and pin, because a real project with real accumulated
knowledge is the thing an update has to preserve.

```bash
# SEED
git clone https://github.com/gabm/Satty.git "$WORK_DIR"
git -C "$WORK_DIR" checkout 2d18065ea534bd12792865784eed86a617ffbdc7
# SCAFFOLD with the OLD generator (v5.12, commit 4700bb4): emits code-worker.md
# and explore-helper.md, both retired in v5.13, and has no framework.json stamp
git show 4700bb4:init_agent.py > /tmp/benchmark/init_agent_v512.py
python3 /tmp/benchmark/init_agent_v512.py --name satty \
  --description "Modern screenshot annotation tool (Rust/GTK4)" \
  --size small --harness claude -y
# ACCUMULATE: sonnet-5 runs /explore for real (fills the project-context digest
# and notes.md), then hand edits stand in for a lived-in scaffold:
#   + Bash(cargo:*) and Bash(make:*) in .claude/settings.json
#   + a "Project rules" section appended to AGENTS.md below the markers
#   + a gotcha line appended to .ai/notes.md
```

**TASK (verbatim):** follow the current `/update` skill end to end, for real.
The scaffold predates the skill, so read it out of the framework checkout.
Do not touch the Satty source.

**GATE** (all must hold):
```
project-context digest byte-identical to pre-update   # knowledge retained
notes.md untouched by the update commit
hand-added AGENTS.md section survives
Bash(cargo:*) + Bash(make:*) survive; settings.json parses
framework.json: 5.14 / small / claude, every listed path exists
5 skills present including update
code-worker.md and explore-helper.md deleted; reviewer.md kept
zero references to either in the live scaffold (backup dir excluded)
git diff on src/, Cargo.toml, Makefile is empty
```

## Result

| | |
|---|---|
| Run ID | u2-satty-update-2026-07-28 |
| Cell | U1 update-legacy (Satty, small, claude) |
| Model / Effort | sonnet-5 / medium |
| From -> to | unstamped v5.12 scaffold -> framework 5.14 |
| Duration | ~200 s (update run), ~184 s (the /explore that seeded it) |
| Tokens | 57.7k (update run), 74.4k (explore) |
| **Gate** | **PASS - 13/13** |

`.ai` history shows the update as one commit on top of the accumulated
knowledge, with no re-explore:

```
3395369 update: framework unstamped -> 5.14
9eceb26 notes: cargo deb gotcha
5207ab5 explore: project context
32adac2 init: small-profile scaffold (satty)
```

The agent confirmed it never read `src/`, `Cargo.toml`, or ran cargo/make. The
4540-byte project-context digest came through byte-identical, which is the
whole point of the design: knowledge migrated, never re-derived.

## Findings that changed the skill

Run 1 (`u1-satty-update-2026-07-28`) passed 10/10 on the checks it could reach
but exposed a hole that made the headline defect unfixed in practice:

1. **Retirement was undecidable on every scaffold that exists today.** The
   skill settled "framework file or user file?" from the recorded
   `framework_files` list, which is empty on any pre-5.14 scaffold. Its
   fallback said to treat unmatched files as the user's and leave them, so
   `code-worker.md` and `explore-helper.md` were permanently protected from
   retirement despite being byte-for-byte the templates v5.12 emitted and
   v5.13 dropped. The agent followed the letter of the rule, left both, and
   said plainly that the rule was wrong. Since every existing deployment is
   pre-stamp, defect 1 from CONCEPT.md section 24 was fixed only for scaffolds
   not yet created.

   Fixed by an **orphan test**: ask the generator's own history whether it ever
   emitted the path, `git -C "$LLM_AGENT_HOME" log --oneline -S'<basename>' --
   init_agent.py`. Commits found means orphaned framework output, retire it;
   none means the user wrote it, leave it; not a git checkout means undecidable,
   report it. Run 2 retired both files on that evidence and kept
   `reviewer.md`.

2. **The backup step assumed its own gitignore entry.** `agent/.update-backup/`
   only lands in `.ai/.gitignore` on a 5.14 scaffold; on a legacy one the agent
   had to add it before backing up. Now stated as a step, since a backup
   committed into KB history is not a backup.

3. **The stop condition did not separate untracked from modified.** Scaffold
   files the host repo never committed read as "uncommitted work" and would
   block an autonomous run for no reason. Now: untracked is normal, note and
   continue; tracked-and-modified is what stops you.

4. **Profile/harness had to be carried from step 1 to step 2 by inference.**
   Now stated explicitly in step 2.

Also working as designed, reported not acted on: probe.py measured Satty at
10276 code LOC, just over the small/large boundary, and the agent surfaced the
profile mismatch instead of migrating on its own (CONCEPT.md section 20).

## Invariants

- PASS/FAIL from the deterministic gate only. One gate check was initially
  scored FAIL because the pattern also matched inside
  `.ai/agent/.update-backup/`, which is a backup doing its job; corrected to
  exclude the backup, then PASS. The `notes.md` check in run 1 likewise
  compared against a snapshot taken before a later hand edit; re-checked
  against the pre-update commit, which is authoritative.
- Raw artifacts under `results/`.
- Findings fed back into `init_agent.py`; run 2 confirms no regression.
