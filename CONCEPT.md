# Project-Aware LLM Agent Framework — Concept

State: 2026-06-11, v3. Language policy: all agent docs in telegraphic English
(no filler, symbols over words, identifiers verbatim). Rationale: English =
best-trained model language + denser tokenization than German; telegraphic
style ≈ 20-30% fewer tokens at equal information.

## 1. Knowledge Base

### Layout

```
.ai/knowledgebase/
├── manifest.yaml            # machine-readable index (source of truth)
├── INDEX.md                 # generated human view, read-only
├── architecture/
│   ├── overview.md          # hot
│   └── module-<name>.md
├── conventions/
│   ├── code-style.md        # hot
│   ├── testing.md
│   └── git-workflow.md
├── domain/
│   ├── glossary.md          # hot
│   └── <context>.md
├── infra/
│   ├── build.md
│   └── ci-cd.md
├── decisions/               # ADRs, append-only
│   └── NNNN-<slug>.md
└── tasks/
    ├── <ticket-id>/
    │   ├── ticket.md        # original + Q&A answers
    │   ├── plan.md          # task index: order, deps, routing, status
    │   ├── NN-<slug>.md     # one file per task, self-contained
    │   └── kb-delta.yaml    # accumulated KB patches
    └── _archive/            # finished tickets, invisible to agent
```

### Node format

```yaml
---
id: architecture/module-payment
summary: Payment processing, Stripe adapter, idempotency handling
tags: [payment, stripe, api]
covers: ["src/payment/**"]
tier: hot|cold
updated: 2026-06-11
related: [domain/billing]
---
```

Rules: node cap ~1500 tokens, larger → split + cross-link. Single source of
truth, never duplicate. `summary` + `covers` enable load decisions without
content loads.

### manifest.yaml over prose index

Flat node list (id, path, summary, tags, covers, tier, updated) + budgets.
Agent parses, not reads → deterministic matching. INDEX.md = generated human
view.

### Navigation protocol (every turn)

1. Parse manifest.yaml (always)
2. Hot tier: embedded in CLAUDE.md generated section (see §6), never loaded
   separately
3. Two-stage retrieval: (a) `covers` globs + tag match, exact; (b) on miss
   only, keyword score over summaries. No embedding index below ~200 nodes
4. Budget: ≤4 cold nodes / ≤6000 tokens per task; `related` ≤1 hop, only on
   explicit miss
5. Session cache of loaded node ids, never reload
6. Mark used vs unused nodes (telemetry)
7. Never load `tasks/_archive/`

## 2. Phases

### Phase 1: Initialization
- Sampling, no full scan: per module entry points, public API, tests
- Bottom-up: module nodes → overview → regenerate manifest/INDEX
- Q&A for non-derivable knowledge (domain terms, unwritten rules)
- Store commit SHA + file hashes → re-init = diff only
- Coverage report: unread areas (lazy init in Phase 4)

### Phase 2: Planning (high-reasoning model)
- Ticket scaffold: `init_agent.py new-ticket <id>`
- Interactive Q&A until acceptance criteria unambiguous; answers → ticket.md
- One file per task `NN-<slug>.md`: goal, criteria, affected files, pre-bound
  KB node ids **with content hashes**, expected signatures/interfaces, test
  skeletons, complexity tag (low/med/high)
- plan.md = thin index (order, deps, routing, status)
- Pre-binding = central token saver: implementation never searches

### Phase 3: Implementation (cost-efficient model)
- Loads only: plan.md + current task file + its nodes/files
- Node hash check; drift → re-plan affected task only
- Done = tests green + lint + `status: done` + patch in kb-delta.yaml
  (op: update/create/split, node, diff)
- Typed escalation:
  - missing-context → reload KB (1 hop) first, then model upgrade
  - ambiguity → ask user
  - test-fail ×2 → model upgrade, this task only
  Never improvise around blockers

### Phase 4: Operational
- No fixed workflow; protocol + budgets still apply
- Post-merge: diff changed paths vs `covers` globs → flag stale nodes

## 3. Model split: evaluation

Effective as **dynamic routing**, not rigid split.

- Pro: cost asymmetry = value asymmetry. Planning: few tokens, high
  reasoning leverage. Implementation: high volume, mechanical given good plan
- Risks: plan = single point of failure; cheap model degrades on surprises,
  cross-cutting refactors, debugging
- Mitigation: complexity tags route high tasks to strong model, typed
  escalation, strong model as review gate (diff review ≪ generation tokens)

## 4. Ticket lifecycle

- Status in frontmatter (`planned|in-progress|done|blocked`), never folder
  names → stable paths for pre-bound refs + hashes
- Ticket done: kb-delta applied → `init_agent.py archive <id>` moves to
  `tasks/_archive/`
- Archive invisible to agent; knowledge lives on in KB/ADRs
- archive command blocks on open tasks (--force overrides), warns on missing
  kb-delta.yaml

## 5. Living KB

- KB delta = mandatory final step of every implementation task, structured
  patch (kb-delta.yaml), not free text
- Declarative auto-apply: metadata/`covers` = auto, structural = review gate
- Staleness: CI compares `covers` globs vs commits since `updated`
- Compaction job: enforce node cap, merge fragments, prune dead nodes,
  narrow triggers of loaded-but-unused nodes (>50%)
- Token telemetry as feedback loop for budget tuning

## 6. CLAUDE.md as hot-tier transport (decision)

Hot-tier content written into CLAUDE.md as **generated section**, since
CLAUDE.md is loaded every session anyway:

```markdown
<!-- BEGIN GENERATED:project-context (source: hot-tier nodes) -->
<!-- END GENERATED:project-context -->
```

- Source stays KB (hot nodes); section = build artifact, regenerated by init,
  kb-delta apply on hot nodes, compaction
- Section budget ~1500 tokens, condensed: one-liner, stack, build/test
  commands, top conventions, module map 1 line/module, core glossary
- Protocol change: never load hot tier separately
- No manual duplication → staleness solved by regeneration, not discipline

Open / next step: `sync-claude` subcommand (hot nodes → section between
markers).

## 7. CLAUDE.md split: phase docs on demand (decision)

CLAUDE.md (incl. @imports) is loaded eagerly → split only pays if it changes
what gets loaded. Phases are mutually exclusive per session → on-demand.

- CLAUDE.md = core, cap 2000 tokens: KB protocol, budgets, ticket layout,
  default routing, generated project-context section, phase pointer table
- `.ai/agent/phases/{init,planning,implementation}.md`: loaded only at phase
  start. Operational = no doc, core protocol is default
- Escalation + KB maintenance rules live in implementation.md
- Mitigation "cheap model skips phase doc": plan.md frontmatter carries
  `read-first: .ai/agent/phases/implementation.md` → instruction comes from
  artifact it must load anyway
- Net: ~50-60% of agent instructions out of always-on context; active phase
  doc ~400-600 tokens on demand

## 8. Language + style policy (decision)

- All agent docs, KB nodes, tickets, plans: English. Best-trained model
  language, denser tokenization vs German, no mixed-language context
- Telegraphic style: drop articles/filler, symbols (→ = ≤ ×) over words,
  imperative fragments. ~20-30% token reduction, zero information discarded
- Exceptions kept verbatim: identifiers, paths, commands, code blocks,
  frontmatter keys. Ambiguity risk for cheap models mitigated by exact
  structure + numbered rules

## 9. Token efficiency stack (summary)

1. Manifest + frontmatter summaries → load decisions without loads
2. Node caps + dedup → bounded worst case
3. Plan pre-binds nodes/files with hashes → zero discovery in implementation
4. Single task files → only current task in context
5. Session node cache; hot tier via CLAUDE.md generated section
6. Slim core CLAUDE.md + on-demand phase docs
7. Incremental init via hashes, sampling over full scan
8. Model routing + typed escalation
9. Telegraphic English everywhere
10. Telemetry feedback loop for trigger/budget tuning
