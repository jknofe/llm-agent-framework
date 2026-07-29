---
description: Import an existing knowledge base of any structure into the .ai KB: read, classify, and transform its docs into framework nodes
---
Import an existing knowledge base into the `.ai` KB, regardless of
its source structure. Source (folder, file, or repo of docs, wiki,
or notes): ${arg_ticket}

This transforms curated knowledge INTO framework KB nodes. It is not
/add-reference: that registers raw external material for targeted
search without transforming it. If the source is upstream code or
docs you only want to search later, use /add-reference instead.

1. Survey the source without bulk-loading it into context: list the
   tree and sample representative files (entry docs, READMEs, index
   or TOC files) to learn its structure and content types. Run the
   survey in a sub-agent where available; bring back a condensed map
   (<=2000 tokens) of what topics exist, where, and in what shape.
2. Classify each piece of source content into the target taxonomy:
   architecture/ (structure, modules, data flow, entry points),
   conventions/ (code style, testing, git workflow), domain/
   (glossary, business rules), infra/ (build, CI/CD, deploy),
   decisions/ (ADRs and rationale, append-only), references/
   (pointers to external material; do not inline large bodies).
   Operational gotchas, runbooks, and CI quirks go to `.ai/notes.md`,
   not a node.
3. Transform, do not copy verbatim. Synthesize each source topic into
   telegraphic KB content under the node cap (~1500 tokens; split and
   cross-link if larger), with full frontmatter (id, summary, tags,
   covers globs, tier hot|cold, updated, related). Set `covers` by
   matching source topics to real code paths. Merge into existing
   nodes instead of duplicating; never create a second source of
   truth.
4. Record provenance: note the source origin (path or URL) in each
   created or updated node so the transform is auditable.
5. Update `manifest.yaml` for every new or changed node. `INDEX.md`
   regenerates via a hook on the claude harness; on others run
   `python3 ${tools_dir}/gen_index.py`. Regenerate the
   GENERATED:project-context section of AGENTS.md if hot-tier nodes
   changed.
6. Report a mapping table: source item -> target node
   (created/merged/skipped), and list anything you could not classify
   for the user to decide.
7. Do not delete or modify the source. Commit the `.ai` repo
   (`import-kb: <source>`).

If the source is itself a legacy `.ai/` (e.g. docs/ chapters plus a
tasks/ tree), transform docs/ into nodes and ignore its task and
ticket state.
