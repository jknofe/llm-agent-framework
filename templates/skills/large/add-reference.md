---
description: Register external material (repo, docs) under .ai/external/ with a references KB node
---
Register an external reference. Name and origin (git URL or local
path): ${arg_ticket}

1. Fetch the material into `.ai/external/<name>/`:
   git URL or local git repo: `git clone --depth 1 <origin>`;
   plain local folder: copy it.
2. Ensure `.ai/.gitignore` contains `external/`.
3. Create `.ai/knowledgebase/references/<name>.md` with frontmatter:
   `id: references/<name>`, one-line `summary`,
   `tags: [external, reference]`, `covers: []`, `tier: cold`,
   `updated`, `origin`, `fetched: <today>`,
   `pinned: <commit sha or n/a>`, `related: []`.
   Body: local copy path, what the material answers, entry points.
4. Append the node to `manifest.yaml`. `INDEX.md` regenerates via a
   hook on the claude harness; on others run
   `python3 ${tools_dir}/gen_index.py`.
5. Commit the `.ai` repo (`add-reference: <name>`).

Reminder: search raw copies with targeted queries; never bulk-load.
