---
description: Import an existing knowledge base of any structure into the small profile: distill it into the AGENTS.md project context and notes.md
---
Import an existing knowledge base into the small-profile `.ai`,
regardless of source structure. Source (folder, file, or repo):
${arg_ticket}

At this scale there is no KB node store; the targets are the
GENERATED:project-context section of AGENTS.md and `.ai/notes.md`.

1. Survey the source without bulk-loading it: list the tree and
   sample entry/index files (sub-agent where available; bring back a
   condensed map).
2. Distill, do not copy. Fold stable, high-value facts (purpose, tech
   stack, build/test/lint commands, top conventions, module map,
   glossary) into the project-context section of AGENTS.md
   (cap ~1500 tokens). Put operational gotchas, runbooks, decisions,
   and domain terms into `.ai/notes.md` (append, telegraphic).
3. If a body of material is large and only worth searching later (an
   upstream repo or doc dump), clone or copy it into
   `.ai/external/<name>/` and note it in `.ai/notes.md` instead of
   inlining it.
4. Report a short mapping: source -> project-context / notes.md /
   external / skipped. Do not delete the source. Commit `.ai`
   (`import-kb: <source>`).
