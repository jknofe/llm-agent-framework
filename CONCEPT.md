# Project-Aware LLM Agent Framework — Concept

State: 2026-06-11, v4 (research-informed revision, changes listed in §10).
Language policy: two registers (§8): plain imperative English for normative
docs, telegraphic English for KB content. English = best-trained model
language + denser tokenization than German.

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
├── references/              # external references: 1 node per source
│   └── <name>.md            # origin, fetched, pinned, usage notes
└── tasks/
    ├── <ticket-id>/
    │   ├── ticket.md        # original + Q&A answers
    │   ├── plan.md          # task index: order, deps, routing, status
    │   ├── NN-<slug>.md     # one file per task, self-contained
    │   └── kb-delta.yaml    # accumulated KB patches
    └── _archive/            # finished tickets, invisible to agent

.ai/external/                # raw external material (clones, doc dumps);
└── <name>/                  # search territory, never load territory;
                             # excluded from .ai git (re-fetchable)
```

### External references

Two layers: raw copy in `.ai/external/<name>/` (clone/copy via
`add-reference`), curated node `references/<name>.md` in KB (origin, fetched
date, pinned version, consult-for notes). Agent loads node only; raw copy =
targeted search, sub-agent where available, never bulk-load. Staleness
visible via `fetched`/`pinned` frontmatter.

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
4. Budget (soft): target ≤4 cold nodes / ≤6000 tokens per task; `related`
   ≤1 hop. Overrun allowed: state reason in one line, proceed, log for
   telemetry. Recall before precision: never skip needed context to satisfy
   budget
5. Session cache of loaded node ids; invalidate cache on context compaction
   (summarized content ≠ loaded content)
6. Mark used vs unused nodes (telemetry)
7. Never load `tasks/_archive/`
8. Session hygiene: clear bulky tool results after extracting what matters;
   run exploration in sub-agent contexts where harness supports it (§2)

## 2. Phases

### Phase 1: Initialization
- Sampling, no full scan: per module entry points, public API, tests
- Exploration in isolated sub-agent contexts where harness supports it; each
  returns condensed summary ≤2000 tokens to main context. Keeps raw file
  dumps out of the synthesizing context
- Bottom-up: module nodes → overview → regenerate manifest/INDEX
- Q&A for non-derivable knowledge (domain terms, unwritten rules)
- Store commit SHA + file hashes → re-init = diff only
- Coverage report: unread areas (lazy init in Phase 4)

### Phase 2: Planning (high-reasoning model)
- Ticket scaffold: `init_agent.py new-ticket <id>`
- Interactive Q&A until acceptance criteria unambiguous; answers → ticket.md
- One file per task `NN-<slug>.md`: goal, criteria, affected files, pre-bound
  KB node ids + content hashes (**warm start**), expected
  signatures/interfaces, test skeletons, complexity tag (low/med/high)
- plan.md = thin index (order, deps, routing, status)
- Pre-binding = warm start, not contract: implementation starts from bound
  nodes/files; bounded extra discovery allowed (≤5 targeted searches) before
  `missing-context` escalation. Rationale: agentic search is cheap and
  improving; baking the planner's context guess into a hard contract trades
  brittleness for tokens
- Plan-review gate before Phase 3: planning model self-reviews plan vs
  acceptance criteria (review ≪ generation tokens), then user sign-off on
  plan.md. Weak plan poisons every downstream task

### Phase 3: Implementation (cost-efficient model)
- Loads only: plan.md + current task file + its nodes/files; bounded extra
  discovery ≤5 targeted searches
- Node hash check, diff-aware: drift → diff current node vs bound hash.
  Delta does not touch task's interfaces/criteria → proceed on fresh content.
  Delta touches them → re-plan affected task only. Never silent-proceed on
  stale context, never full re-plan on cosmetic drift
- Done = tests green + lint + `status: done` + patch in kb-delta.yaml
  (op: update/create/split, node, diff)
- Typed escalation:
  - missing-context → bounded discovery + reload KB (1 hop, sub-agent where
    available) first, then model upgrade
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
  escalation, plan-review gate (§2) + strong model as diff-review gate
  (review ≪ generation tokens)
- Known gap: complexity often surfaces during execution, not planning;
  reactive escalation (test-fail ×2) burns two attempts first. Outcome
  telemetry (§5) tunes tags + escalation thresholds over time

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
- Ownership: automation flags, human decides. Named KB owner + fixed review
  cadence (monthly lint: obsolete rationale, dead nodes, drifted `covers`).
  Neglected KB = confident wrong context, worse than no KB
- Telemetry, two layers:
  - cost: tokens loaded/used per task, unused-node rate
  - outcomes: task success rate, escalation counts by type, re-plan rate,
    hash-drift rate, budget-overrun rate
  Outcome data tunes routing thresholds, budgets, node triggers; token data
  alone cannot show whether the model split works

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

Portability: where a harness reads `AGENTS.md` (vendor-neutral standard)
instead of CLAUDE.md, generate the same content there; source stays KB.

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
- Harness alignment: phase docs = hand-rolled skills. Where harness supports
  the Agent Skills standard, package each phase as `SKILL.md` (frontmatter
  name + description ~30-50 tokens at startup, body loaded on trigger) →
  progressive disclosure enforced by harness, not by model obedience.
  `read-first` pointer stays as fallback for skill-less harnesses
- Net: ~50-60% of agent instructions out of always-on context; active phase
  doc ~400-600 tokens on demand

## 8. Language + style policy (decision, revised v4)

- All agent docs, KB nodes, tickets, plans: English. Best-trained model
  language, denser tokenization vs German, no mixed-language context
- Two registers:
  - **Normative text** (KB protocol, phase docs, escalation rules,
    acceptance criteria): plain imperative English, complete sentences.
    Compression research validates terse *content*, not terse *instructions*;
    the cost-efficient executor is exactly the model class most likely to
    misread ambiguous fragments. ~500 tokens saved per doc < cost of one
    misread rule
  - **KB content** (nodes, summaries, tickets, glossaries): telegraphic.
    Drop articles/filler, symbols (→ = ≤ ×) over words. ~20-30% token
    reduction, zero information discarded
- Exceptions kept verbatim everywhere: identifiers, paths, commands, code
  blocks, frontmatter keys
- Validation path: A/B same ticket in both styles, compare escalation +
  re-plan rates

## 9. Token efficiency stack (summary)

1. Manifest + frontmatter summaries → load decisions without loads
2. Node caps + dedup → bounded worst case
3. Plan pre-binds nodes/files with hashes → warm start, near-zero discovery
4. Single task files → only current task in context
5. Session node cache (compaction-aware); hot tier via CLAUDE.md section
6. Slim core CLAUDE.md + on-demand phase docs (Agent Skills where supported)
7. Incremental init via hashes, sampling + sub-agent isolation over full scan
8. Model routing + typed escalation + plan-review gate
9. Two-register language: plain instructions, telegraphic content
10. Session hygiene: tool-result clearing, soft budgets, declared overruns
11. Two-layer telemetry (tokens + outcomes) for trigger/budget/routing tuning

## 10. v4 revision notes (2026-06-11)

Research-informed pass (Anthropic context engineering + Agent Skills, KB-for-
coding-agents literature, plan-then-execute studies). Changes vs v3:

1. Pre-binding demoted: contract → warm start; bounded discovery (≤5
   searches); diff-aware hash-drift handling instead of re-plan-on-any-drift
2. Budgets hard → soft: declared overruns, recall before precision
3. Sub-agent isolation for exploration, ≤2000-token summaries back
4. Session hygiene: tool-result clearing, node-cache invalidation on
   compaction
5. Language policy split into two registers (plain normative / telegraphic
   content)
6. Agent Skills packaging for phase docs; AGENTS.md portability
7. Plan-review gate before implementation
8. Telemetry extended with outcome layer; KB ownership + review cadence

Unchanged: KB layout, manifest navigation, hot/cold tiers, hot tier via
CLAUDE.md generated section, kb-delta, staleness CI, ticket lifecycle +
archive.
