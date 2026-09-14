---
description: Import an existing knowledge base of any structure: requirements into AGENTS.md, the map into .ai/notes/map.md, the rest into notes.md
---
Import an existing knowledge base into `.ai`, regardless of source
structure. Source (folder, file, or repo): ${arg_ticket}

There is no KB node store; the targets are the GENERATED:project-context
section of AGENTS.md (requirements only), `.ai/notes/map.md` (module
map, stack, glossary) and `.ai/notes.md` (everything else).

1. Survey the source without bulk-loading it: list the tree and
   sample entry/index files (sub-agent where available; bring back a
   condensed map).
2. Distill, do not copy. Build/test/lint commands, required or
   forbidden tools, and project rules go into the project-context
   section of AGENTS.md (cap ~300 tokens). Purpose, stack, module map
   and glossary go into `.ai/notes/map.md`, linked from `.ai/notes.md`.
   Operational gotchas, runbooks, decisions, and domain terms go into
   `.ai/notes.md` (append, telegraphic). If the source repository
   already documents its architecture, point at that document instead
   of restating it.
3. If a body of material is large and only worth searching later (an
   upstream repo or doc dump), clone or copy it into
   `.ai/external/<name>/` and note it in `.ai/notes.md` instead of
   inlining it.
4. Report a short mapping: source -> project-context / map.md /
   notes.md / external / skipped. Do not delete the source. Commit `.ai`
   (`import-kb: <source>`).
