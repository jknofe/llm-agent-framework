---
description: Migrate an existing .ai/ folder (older framework version or other layout) into the current structure: knowledge and lifecycle state
---
Migrate an existing `.ai/` directory into the current large-profile
structure. Source `.ai/` (an older version of this framework, or a
differently-shaped agent folder): ${arg_ticket}

This converts a whole prior `.ai/` working directory - both the
knowledge AND the lifecycle state - into the current layout. It is
not /import-kb: that transforms arbitrary curated knowledge (a
docs/wiki dump) into KB nodes and deliberately ignores task and
ticket state. /import additionally carries the ticket, task, plan,
decision, and notes state across. If the source is a docs/wiki dump
rather than a `.ai/`-style working folder, use /import-kb instead.
It is also not /update: that moves a scaffold this framework already
wrote (one carrying `.ai/agent/framework.json`) to the current
version in place. Use /update when the folder is a stamped scaffold
of an earlier version, /import when it is unstamped or foreign.
Run this after scaffolding, against a copy of the old folder: move
the pre-existing `.ai/` aside (e.g. to `.ai.old/`) before init, then
`/import .ai.old`.

1. Survey without bulk-loading. List the source tree; sample its
   entry points (`manifest.yaml`, `INDEX.md`, `AGENTS.md`,
   `tickets/`, `knowledgebase/`, `changes/`, notes). Identify the
   layout and roughly which framework version it is (large markers:
   `knowledgebase/` + `manifest.yaml`; small markers: `changes/` +
   `notes.md`, no manifest; foreign: neither). Run the survey in a
   sub-agent where available; bring back a condensed map (<=2000
   tokens) of what exists and where.
2. Migrate the knowledge. For source content already in framework
   node shape, upgrade it in place: remap each node into the six
   categories (architecture/, conventions/, domain/, infra/,
   decisions/, references/) and rewrite its frontmatter to the
   current schema (id, summary, tags, covers globs, tier hot|cold,
   updated, related), re-matching `covers` to real code paths. For
   content not already node-shaped, apply the /import-kb
   read->classify->transform protocol (synthesize telegraphic nodes
   under the ~1500-token cap, dedup by merging, never a second source
   of truth). Operational gotchas and runbooks route to
   `.ai/notes.md`, not a node.
3. Migrate the lifecycle state (what /import-kb drops):
   - Inbox tickets -> `.ai/tickets/<ID>-<slug>.md`, frontmatter
     preserved.
   - Planned or in-progress tickets ->
     `.ai/knowledgebase/tasks/<id>/` (ticket.md, plan.md,
     NN-<slug>.md task files, kb-delta.yaml), preserving each task's
     status (planned|in-progress|done|blocked) in frontmatter, not
     folder names. Finished tickets ->
     `.ai/knowledgebase/tasks/_archive/`.
   - Decisions/ADRs -> `decisions/` nodes, append-only, keep the
     rationale.
   - External references -> `references/` nodes; if the source held
     raw material under its own `external/`, copy it into
     `.ai/external/<name>/` and ensure `.ai/.gitignore` lists
     `external/`.
   - `notes.md` / notes hub -> `.ai/notes.md` (+ leaves),
     telegraphic.
4. Regenerate, do not copy, the derived artifacts: append every
   migrated node to `manifest.yaml` (INDEX.md regenerates via the
   claude hook; on other harnesses run
   `python3 ${tools_dir}/gen_index.py`), and regenerate the
   GENERATED:project-context section of AGENTS.md from the migrated
   hot-tier nodes rather than importing the old AGENTS.md text.
   Never carry the source's INDEX.md or generated section over
   verbatim, and never overwrite `.ai/agent/framework.json` with the
   source's copy: init already stamped this scaffold at the current
   version, and that stamp is what /update reads later.
5. Record provenance: note the source origin in each migrated node so
   the migration is auditable.
6. Report a mapping table: source item -> target
   (migrated/merged/skipped), and list anything you could not map for
   the user to decide. Do not delete or modify the source. Commit the
   `.ai` repo (`import: <source>`).

Profile mismatch: if the source was a small-profile `.ai`
(project-context + notes, no node store), promote its distilled facts
into KB nodes here. Map the source's content onto this profile's
targets; do not recreate the source's shape.
