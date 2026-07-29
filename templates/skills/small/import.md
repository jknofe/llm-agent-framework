---
description: Migrate an existing .ai/ folder (older version or other layout) into the small profile: project-context, notes.md, and in-flight changes
---
Migrate an existing `.ai/` directory into the current small-profile
structure. Source `.ai/` (an older version of this framework, or a
differently-shaped agent folder): ${arg_ticket}

This converts a whole prior `.ai/` working directory into the small
profile. The small-profile targets are the GENERATED:project-context
section of AGENTS.md, `.ai/notes.md`, and `.ai/changes/<id>/spec.md`
for in-flight changes; there is no KB node store. It is not
/import-kb: that transforms arbitrary curated knowledge (a docs/wiki
dump) and ignores lifecycle state, whereas /import also carries
ticket/change and notes state across. If the source is a docs/wiki
dump rather than a `.ai/`-style working folder, use /import-kb. It
is also not /update: that moves a scaffold this framework already
wrote (one carrying `.ai/agent/framework.json`) to the current
version in place. Use /update when the folder is a stamped scaffold
of an earlier version, /import when it is unstamped or foreign. Run
this after scaffolding, against a copy of the old folder (e.g. move
the pre-existing `.ai/` aside to `.ai.old/` before init, then
`/import .ai.old`).

1. Survey without bulk-loading: list the source tree; sample its
   entry/index files and any manifest, notes, `changes/`, `tickets/`,
   `knowledgebase/` (sub-agent where available; bring back a
   condensed map). Note whether the source was large (knowledgebase/
   + manifest) or small.
2. Distill knowledge, do not copy. Fold stable, high-value facts
   (purpose, tech stack, build/test/lint commands, top conventions,
   module map, glossary) into the project-context section of
   AGENTS.md (cap ~1500 tokens); if the source was a large-profile
   KB, distill its hot-tier nodes down, do not reproduce the node
   store. Route operational gotchas, runbooks, decisions, and domain
   terms to `.ai/notes.md` (append, telegraphic; use the notes hub if
   it grows).
3. Migrate lifecycle state: unfinished tickets or changes ->
   `.ai/changes/<id>/spec.md` (goal, acceptance criteria, task
   checklist, status preserved); finished ones ->
   `.ai/changes/_archive/`. A large body worth only searching later
   -> clone or copy into `.ai/external/<name>/` and note it in
   `.ai/notes.md` instead of inlining it.
4. Regenerate, do not copy: refresh project-context from the migrated
   facts, not the old AGENTS.md text. Never overwrite
   `.ai/agent/framework.json` with the source's copy: init already
   stamped this scaffold at the current version, and that stamp is
   what /update reads later. Report a short mapping (source
   -> project-context / notes.md / changes / external / skipped). Do
   not delete the source. Commit `.ai` (`import: <source>`).
