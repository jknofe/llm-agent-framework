# Project-Aware LLM Agent Framework — Concept

State: 2026-08-26, v5.20 (review gates sized to the change: right-sizing now
reaches the gates, not just the pipeline entrance. A right-sized small-profile
change gets no gate at all, the large trivial path sizes both gates down to an
inline criteria check, and the reviewer brief scales depth to the artifact
with the packaging/toolchain sweep conditioned on the diff touching build
config. Sizing down is allowed, silent skipping is not).
v5.19 (copilot invocation documented correctly: prompt
files are a VS Code feature invoked as `/name` slash commands, and Copilot
CLI does not read `.github/prompts/` at all, so it gets the kickoff
sentences instead. The generated AGENTS.md section said prompt files were
VS Code only without ever saying how to run them there, and
`--bootstrap-update` told copilot users to run `/update` regardless of
surface. Docs only, no mechanism change).
v5.18 (`--bootstrap-update`: deliver the `/update` skill
into a scaffold built before it existed, and nothing else, so pre-5.14
projects can be updated by the agent instead of by a blind re-init. The stamp
it writes records `framework_version: null` on purpose. Also fixes the orphan
test, whose `-- init_agent.py` path filter went stale in 5.17 and would have
made every file added after that version unretirable. §28). v5.17 (generator
restructured: content the generator emits
moved out of string literals into `templates/` as files of their own kind
(emitted Python as `.py`, prose as `.md`, data as data), logic split into an
`agentgen/` package, `init_agent.py` reduced to the CLI. Slots use
`string.Template` because emitted content is full of literal braces. The two
axes keep branching in code, with conditional prose as fragment files, so no
document is duplicated per variant. Verified by byte-identity across all four
variants: the emitted scaffold is unchanged from v5.16. §27). v5.16 (/tidy-up:
a bounded hygiene sweep over the host code
in four passes (dead code removed with evidence, obsolete files proposed but
never deleted, overlong comments compressed to 1-2 lines without losing the
knowledge in them, em dashes rewritten out of prose), gated on a green
test/lint baseline captured up front and forbidden from changing behavior;
both profiles, both harnesses. The generator's own templates were swept for
the em-dash rule they already stated. §26). v5.15 (/import: migrate a whole
existing `.ai/` folder
(older framework version or foreign agent layout) into the current structure,
carrying both the knowledge and the lifecycle state (tickets, tasks, plans,
decisions, notes; small profile: in-flight changes) that /import-kb drops;
both profiles, both harnesses. Distinct from /update, which upgrades a
scaffold this framework already stamped; /import handles unstamped or foreign
folders. §25). v5.14 (agent-driven framework update: `init_agent.py`'s
`-u/--update` is removed and replaced by an `/update` skill in both profiles
and both harnesses. Scaffolds now carry a version stamp
(`.ai/agent/framework.json`: framework version, profile, harness, and the
list of framework files that version emitted); the CLI keeps two flags that
only serve the skill, `--detect` and `--emit-reference DIR`. Updating is a
merge, and merges need judgment a stdlib scaffolder does not have. §24).
v5.13 (worker sub-agents removed: the `code-worker` and
`explore-helper` definitions, their dispatch guidance in the phase docs and
the small-profile skills, and the runbook's W arm are gone. Two reasons: the
dispatch instructions were harness-neutral text while the agent definitions
were claude-only, so copilot scaffolds told the agent to dispatch to
sub-agents that do not exist; and the one W-arm measurement showed the
delegation claim failing (+35% total tokens, +43% cost at an equal gate).
§23 rewritten as the rejected-design record). v5.12 (worker sub-agents on a
mid-tier model: optional scaffolded `code-worker` and `explore-helper` agent
definitions pinning `model: sonnet` in frontmatter; removed in v5.13).
v5.11 (/goal as a documented autonomous-dispatch mode:
AGENTS.md now names /goal explicitly in both profiles, pointed at the same
done-bar /build (small) or /implement (large) already defines rather than a
new one, paired with the existing stall/escalation rule; claude-harness only,
§22). v5.10 (explore-freshness guard: small-profile Protocol item 1
now tells the agent to check whether the Project Context digest is still an
unpopulated stub and run /explore first if so, instead of proceeding on a
stale/wrong one-liner; notes.md stub explicitly sanctions cross-repo/path
pointers as an existing genre, while restating that architecture/module-map
content stays out of notes.md, §21). v5.9 (automatic profile selection:
init-agent counts source
LOC and applies the ~10k boundary to pick small vs large when --size is omitted
or 'auto'; explicit --size still wins,
§20). v5.8 (small-profile notes hub: .ai/notes.md may become a
linked index with .ai/notes/<topic>.md leaves once it grows past ~1-2 screens,
guidance-only, §19). v5.7 (project-context freshness: end-of-change refresh of
the AGENTS.md generated digest via probe.py, LOC-only drift excluded; ecosystem-
neutral correctness-criteria examples; §18). v5.6 (harness-mechanism pass after
a best-practice review: skills locked to manual invocation, path-scoped rules
generated from conventions nodes, parallel-ok task marking, /goal as middle
verification tier, prune test in KB lint, §17). v5.5 (more determinism offloaded from the
model to scripts/
hooks: probe.py repo inventory, auto-regenerate INDEX on manifest write,
check_stale at session start, §16). v5.4 (/import-kb: transform an existing
knowledge base of any structure into .ai, §15). v5.3: durable task cursor +
running-memory notes.md in
both profiles, backported from the legacy agents (§14). v5.2: size profiles, a
stripped-down small profile for codebases ≤10k LOC (§13). v5.1: model choice
fully delegated to user (§3); v5: standards + deterministic enforcement (§12).
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
    │   ├── plan.md          # task index: order, deps, status, kb-commit
    │   ├── NN-<slug>.md     # one file per task, self-contained
    │   └── kb-delta.yaml    # accumulated KB patches
    └── _archive/            # finished tickets, invisible to agent

.ai/tickets/                 # inbox: <ID>-<slug>.md, via /add-ticket or
                             # dropped in by user; /plan consumes into tasks/

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
2. Hot tier: embedded in AGENTS.md generated section (see §6), never loaded
   separately
3. Two-stage retrieval: (a) `covers` globs + tag match, exact; (b) on miss
   only, keyword score over summaries. No embedding index below ~200 nodes
4. Budget (soft): target ≤4 cold nodes / ≤6000 tokens per task; `related`
   ≤1 hop. Overrun allowed: state reason in one line, proceed. Recall before
   precision: never skip needed context to satisfy budget
5. Never load `tasks/_archive/`
6. Exploration + review in sub-agent contexts where harness supports it (§2)
7. INDEX.md = generated by `gen_index.py` from manifest, never edited;
   PreToolUse hook blocks direct writes (claude harness)
8. Compaction: instruct harness to preserve current ticket id, task file
   path, modified-files list, build/test commands. v4 items dropped as not
   model-actionable in any current harness: session node cache, used/unused
   marking, tool-result clearing (§12)

## 2. Phases

### Phase 1: Initialization
- Deterministic inventory first: `probe.py` (host SHA, language mix, detected
  build/test/lint commands, module map + LOC, dep manifests, entry points) →
  seed mechanical project-context fields free, sample by its map (§16)
- Sampling, no full scan: per module entry points, public API, tests
- Exploration in isolated sub-agent contexts where harness supports it; each
  returns condensed summary ≤2000 tokens to main context. Keeps raw file
  dumps out of the synthesizing context
- Bottom-up: module nodes → overview → update manifest; INDEX auto-regenerates
  (PostToolUse hook runs `gen_index.py` on manifest write, §16)
- Q&A for non-derivable knowledge (domain terms, unwritten rules)
- Once build/test/lint commands known: offer project-specific Stop hook
  (lint/tests on turn end) → "done = checks pass" deterministic (claude)
- Store host-repo commit SHA → re-init = diff only
- Coverage report: unread areas (lazy init in Phase 4)

### Phase 2: Planning
- Ticket source: `.ai/tickets/` inbox (via /add-ticket or user-dropped md
  file); agent creates `tasks/<id>/` from it, deletes inbox file
- Interactive Q&A until acceptance criteria unambiguous; answers → ticket.md
- One file per task `NN-<slug>.md`: goal, criteria, affected files, pre-bound
  KB node ids (**warm start**), expected signatures/interfaces, test
  skeletons
- plan.md = thin index (order, deps, status) + `kb-commit` frontmatter: .ai
  commit SHA the plan was built against. Drift baseline; replaces v4
  per-node content hashes (git diff = deterministic, model-computed hashes
  were not)
- Pre-binding = warm start, not contract: implementation starts from bound
  nodes/files; bounded extra discovery allowed (≤5 targeted searches) before
  `missing-context` escalation. Rationale: agentic search is cheap and
  improving; baking the planner's context guess into a hard contract trades
  brittleness for tokens
- Trivial path: ticket fits one sentence / 1-2 files → skip Q&A, single task
  file, sign-off = one line, and both review gates size down to an inline
  criteria check (§29). Ceremony must not exceed the task (SDD field
  reports: planning overhead > savings on small tasks)
- Plan-review gate before Phase 3: adversarial review in fresh context
  (reviewer sub-agent; fallback: user review) vs acceptance criteria, then
  user sign-off on plan.md. v4 self-review dropped: producing context grades
  its own work. Weak plan poisons every downstream task

### Phase 3: Implementation
- Loads only: plan.md + current task file + its nodes/files; bounded extra
  discovery ≤5 targeted searches
- Drift check, diff-aware: `git -C .ai diff <kb-commit> -- <node path>` per
  pre-bound node. Empty → proceed. Delta not touching task's
  interfaces/criteria → proceed on fresh content. Touching them → re-plan
  affected task only. Never silent-proceed on stale context, never full
  re-plan on cosmetic drift
- Done = tests green + lint + `status: done` + patch in kb-delta.yaml
  (op: update/create/split, node, diff)
- Ticket review gate: after last task, review of full diff vs acceptance
  criteria, sized to the ticket (§29). Trivial path → inline check, no
  sub-agent; otherwise fresh-context review (reviewer sub-agent). Fix
  correctness gaps, ignore style-only findings; record `reviewed: <date>` in
  plan.md
- Typed escalation:
  - missing-context → bounded discovery + reload KB (1 hop, sub-agent where
    available), then ask user
  - ambiguity → ask user
  - test-fail ×2 → stop; fresh-context critique of approach or re-plan the
    task; never a third blind attempt
  Never improvise around blockers

### Phase 4: Operational
- No fixed workflow; protocol + budgets still apply
- Post-merge + session start: `check_stale.py` flags nodes whose `covers`
  globs match commits since `updated`

## 3. Model choice (revised v5.1)

Model choice belongs to the user, via harness controls (`/model`,
`opusplan`, sub-agent `model:` frontmatter). The framework is
model-agnostic: no routing machinery, no model instructions in generated
docs.

- v4 per-task complexity routing dropped in v5: harnesses route per
  sub-agent/session, not per task file; routing machinery cost > savings at
  this scale; outcome data to tune it never existed
- v5 "strong main loop" default guidance dropped in v5.1: restates or
  fights a user decision the harness already owns; always-on tokens, zero
  behavior change
- Kept as property, not instruction: self-contained task files +
  fresh-context review gates are what make cheap-execution modes (e.g.
  opusplan: plan on strong model, implement on cheap one) viable. Stated in
  README, not in agent docs. Direction stays asymmetric: never plan on the
  weak model
- v5.12 instantiated that property once with two scaffolded worker
  definitions pinning `model: sonnet`; v5.13 removed them (§23). The rule
  stands as before: routing is the user's, via harness controls, and the
  framework ships no tier pin of its own

## 4. Ticket lifecycle

- Status in frontmatter (`planned|in-progress|done|blocked`), never folder
  names → stable paths for pre-bound refs + kb-commit diffs
- Intake: ticket md lands in `.ai/tickets/` inbox (/add-ticket or by hand);
  /plan converts to `tasks/<id>/`
- Ticket done: kb-delta applied → user prompts agent to archive; agent
  verifies all tasks `done` + kb-delta applied, moves to `tasks/_archive/`,
  commits .ai (no CLI command; rules in instructions file)
- Archive invisible to agent; knowledge lives on in KB/ADRs

## 5. Living KB

- KB delta = mandatory final step of every implementation task, structured
  patch (kb-delta.yaml), not free text
- Declarative auto-apply: metadata/`covers` = auto, structural = review gate
- Staleness: `check_stale.py` compares `covers` globs vs host commits since
  `updated` (exit 1 on findings → CI-wirable); run post-merge + operational
  session start
- Compaction job: enforce node cap, merge fragments, prune dead nodes
- Ownership: automation flags, human decides. Named KB owner + fixed review
  cadence (monthly lint: obsolete rationale, dead nodes, drifted `covers`,
  and the prune test — any rule the agent already follows unprompted gets
  deleted; always-on instruction bloat is why real rules get ignored).
  Neglected KB = confident wrong context, worse than no KB
- Telemetry: cut in v5. v4 specified two layers (token cost + outcomes)
  with no collection mechanism; spec without mechanism = dead weight.
  Re-add together with collection hooks when needed; outcome data stays the
  precondition for any future routing automation (§3)

## 6. AGENTS.md as hot-tier transport (decision, revised v5)

Canonical instructions file = AGENTS.md (vendor-neutral standard, read
natively by Copilot and most current harnesses). Claude harness gets a
one-line CLAUDE.md pointer (`@AGENTS.md` import); copilot-instructions.md
dropped. Hot-tier content written into AGENTS.md as **generated section**,
since it is loaded every session anyway:

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
- Re-init recovers an existing generated section (also from legacy CLAUDE.md
  scaffolds) instead of reverting it to the stub

Regeneration of the section is an agent duty (Phase 1 + after hot-node
kb-delta), not a CLI feature: the CLI only scaffolds.

## 7. AGENTS.md split: phase docs on demand + skills (decision, revised v5)

AGENTS.md (incl. imports) is loaded eagerly → split only pays if it changes
what gets loaded. Phases are mutually exclusive per session → on-demand.

- AGENTS.md = core, cap 2000 tokens: KB protocol, budgets, ticket layout,
  right-sizing rule, generated project-context section, phase pointer table
- `.ai/agent/phases/{init,planning,implementation}.md`: single source of
  truth, loaded only at phase start. Operational = no doc, core protocol is
  default
- Escalation + KB maintenance rules live in implementation.md
- Entry points = Agent Skills (implemented v5): each workflow packaged as
  `.claude/skills/<name>/SKILL.md` (open SKILL.md standard; frontmatter
  name + description ~30-50 tokens at startup, body loaded on trigger) →
  progressive disclosure enforced by harness, not by model obedience.
  Skill bodies stay thin pointers to the phase docs. Copilot harness: same
  bodies as `.github/prompts/*.prompt.md` (VS Code)
- Mitigation "implementing session skips phase doc": plan.md frontmatter
  carries `read-first: .ai/agent/phases/implementation.md` → instruction
  comes from artifact it must load anyway; also covers skill-less harnesses
  (Copilot CLI kickoff lines)
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
  re-plan rates (a two-register A/B spec was drafted for v5.6 but never run; a
  spec'd-but-never-run validation is the same dead weight telemetry was culled
  for)

## 9. Token efficiency stack (summary)

1. Manifest + frontmatter summaries → load decisions without loads
2. Node caps + dedup → bounded worst case
3. Plan pre-binds nodes/files + `kb-commit` baseline → warm start,
   near-zero discovery, deterministic drift check
4. Single task files → only current task in context
5. Hot tier via AGENTS.md generated section
6. Slim core AGENTS.md + on-demand phase docs (Agent Skills / prompt files)
7. Incremental init via commit SHA, sampling + sub-agent isolation over
   full scan
8. Typed escalation + fresh-context review gates (plan + ticket diff)
9. Two-register language: plain instructions, telegraphic content
10. Soft budgets with declared overruns; right-sizing: no ticket ceremony
    below ticket scale
11. Deterministic tools + hooks over protocol prose (probe inventory,
    gen_index, check_stale; PreToolUse/PostToolUse/SessionStart/Stop hooks)

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

## 11. Tooling update (2026-06-12)

CLI reduced to a single interactive scaffold command (`init-agent`, no
subcommands, no parameters; prompts: name, description, harness
claude/copilot, overwrite-confirm replaces --force). Lifecycle ops moved
from CLI to agent:

- ticket intake: `.ai/tickets/` inbox (`<ID>-<slug>.md`), filled via
  /add-ticket or by hand; /plan consumes inbox → `tasks/<id>/`
- references: /add-reference (clone/copy → `.ai/external/`, node + index
  updates by agent) or material placed by hand, node created on discovery
- archive: user prompts agent; rules in instructions file, no command
- .ai commits: agent duty (protocol rule), CLI commits only at init;
  `git -C .ai` pre-allowed in the permission list

Rationale: every lifecycle op is agent-executable instruction-following;
keeping it in the CLI duplicated logic the agent must know anyway and
forced parameter ceremony on the user. Slash commands /explore, /add-ticket,
/plan, /implement, /add-reference, /import-kb (§15); harness copilot gets the
same as .github/prompts/*.prompt.md.

## 12. v5 revision notes (2026-06-12)

Implementation pass: open standards + deterministic enforcement over
protocol prose. Changes vs v4:

1. AGENTS.md = canonical instructions file; CLAUDE.md = `@AGENTS.md`
   pointer (claude harness); copilot-instructions.md dropped (Copilot reads
   AGENTS.md natively)
2. Slash commands → Agent Skills (`.claude/skills/<name>/SKILL.md`, open
   standard); copilot keeps VS Code prompt files; phase docs remain single
   source of truth in `.ai/agent/phases/`
3. Enforcement via hooks (claude): PreToolUse blocks direct INDEX.md edits;
   Stop blocks turn end on dirty `.ai` repo; Phase 1 offers a
   project-specific lint/test Stop hook once commands are known
4. Review gates adversarial: `reviewer` sub-agent (fresh context, read-only
   tools) replaces v4 self-review at the plan gate; new ticket diff-review
   gate at the end of Phase 3
5. Drift detection: per-node content hashes → plan.md `kb-commit` +
   `git -C .ai diff` (deterministic, pre-allowed command)
6. Deterministic KB tools in `.ai/agent/tools/`: gen_index.py (INDEX.md
   from manifest), check_stale.py (covers globs vs commits since `updated`,
   CI-wirable exit code)
7. Model routing dropped entirely (§3): v5 cut complexity-tag routing,
   v5.1 (same day) cut the remaining "strong main loop" guidance and the
   AGENTS.md Model Use section. Model choice = user's, via harness controls;
   framework model-agnostic
8. Telemetry spec cut (§5): no mechanism existed, spec without mechanism is
   dead weight
9. Right-sizing: trivial path in Phase 2; one-sentence single-file changes
   need no ticket at all
10. Always-on protocol pruned: non-model-actionable v4 items removed
    (session node cache, used/unused marking, tool-result clearing);
    compaction-preserve instruction added
11. init never overwrites hand-filled KB content (nodes, manifest, INDEX);
    existing generated project-context section recovered on re-init, also
    from legacy CLAUDE.md scaffolds
12. Decision (owner, 2026-06-12): `.ai` stays a private nested repo, no
    remote, no host-repo sharing. Team-shared KB rejected

Unchanged: KB layout, manifest navigation, hot/cold tiers, kb-delta,
staleness model, ticket lifecycle + archive, two-register language policy.

## 13. Small-project profile (2026-06-24, v5.2)

`init-agent` now prompts for a size profile. **large** (default) is the full
framework above. **small** targets codebases up to ~10k LOC, where there is no
context scarcity to manage: the whole source is cheap to read on demand. The
profile is a strict subset — same private nested `.ai` repo, same AGENTS.md
transport, same review-gate idea — with the large-codebase machinery removed.

Design rule: keep what pays even when the code is small; drop everything whose
only job is rationing context or tracking drift in a large KB. Rationale:
current best practice favors just-in-time retrieval (keep lightweight
identifiers, read the real source via tools) over a pre-loaded knowledge store,
and "do the simplest thing that works"; at ≤10k LOC the agent re-reads the
source faster than it can maintain a synced index, so the index's upkeep cost
(drift, staleness, commits, regeneration) exceeds its value.

### Kept
- AGENTS.md as canonical, always-on instructions (host repo) + CLAUDE.md
  pointer; build/test/lint commands are the highest-ROI content.
- Generated `project-context` section in AGENTS.md as the only knowledge store
  (arch summary, module map, glossary, commands), filled by `/explore`.
- Private nested `.ai/.git` repo + the `ai_repo_clean` Stop hook (owner
  decision, 2026-06-24: same privacy model as large).
- `reviewer` sub-agent as a single final-diff review gate before done.
- Read-only permission allow list; right-sizing rule + trivial path;
  two-register language; dual skill/prompt rendering from one spec list.

### Simplified
- KB (manifest, INDEX, hot/cold nodes, two-stage retrieval, per-task budgets,
  `related` hops) → the AGENTS.md generated section, plus ad-hoc
  `.ai/<topic>.md` only if a project genuinely needs it.
- Ticket pipeline (inbox → ticket.md → plan.md → NN-task.md → kb-delta.yaml,
  two gates) → a single `.ai/changes/<id>/spec.md` (goal + acceptance criteria
  + task checklist) and one gate.
- Four phases + on-demand phase docs + skills-as-pointers → three
  self-contained skills (`/explore`, `/spec`, `/build`); instructions inlined,
  still loaded on trigger by the harness (progressive disclosure kept,
  indirection dropped).
- Living KB + ADRs (`decisions/`) → one append-only `.ai/notes.md` (structured
  note-taking).
- Five skills → three.

### Dropped (solving a non-problem at this scale)
- manifest.yaml, INDEX.md, hot/cold tiers, two-stage retrieval, per-task
  token/node budgets, `related`-hop limits.
- Drift detection (`kb-commit` + per-node `git diff`), staleness scanning
  (`check_stale.py`), `gen_index.py`, the `protect_generated` hook (no
  generated INDEX to protect).
- `kb-delta.yaml` structured patches; the plan-review gate (keep only the final
  review); the `add-ticket` and `add-reference` skills (external material:
  clone into `.ai/external/` ad hoc and note it in `notes.md`).

### Trade-offs
- Retained ceremony: the `.ai` commit discipline + Stop hook is the one piece of
  large-profile operational tax kept, by owner decision.
- One gate not two: a poor task decomposition can slip past planning; mitigated
  by small task counts and the final diff review. Plan-review is the upgrade
  path.
- Graduation is not automatic: crossing ~10-15k LOC means re-running init as
  large (hand-filled content is preserved) and hand-migrating `notes.md`/specs
  into KB nodes; the artifact shapes differ. No auto-migrator. The crossing is
  at least *flagged* since the §18.1 refresh: probe.py prints a code-only LOC
  total, and small `/build` proposes the re-init once it passes ~10k (proposal
  only, migration stays a deliberate user decision).

### Unchanged across profiles
Private `.ai` repo model, AGENTS.md generated-section transport, the
fresh-context review idea, two-register language, the right-sizing rule, and
the single-interactive-scaffold CLI (now with one extra size prompt).

## 14. Backport from legacy agents (2026-06-26, v5.3)

Comparison against an earlier family of Copilot-style project agents (the
direct conceptual ancestor: same private nested `.ai` repo, same
ticket→task→implement pipeline) surfaced two things they did better, both now
backported. Everything else they had — context rationing, drift/staleness,
review gates, sub-agent isolation, single-source instructions — this framework
already does better or equivalently, so only these two were taken.

### 14.1 Durable task cursor (`.ai/.current`)

Problem: resume across *new sessions*. v4 dropped an explicit session cursor as
"not model-actionable", but that judgment was about an in-memory node cache, not
a file. The legacy agents kept a dead-simple on-disk pointer (`.ai/tasks/.current`
= JIRA id + task id) that survived session boundaries with zero machinery. The
framework's only resume mechanism was a *compaction-preserve instruction* — a
hint to the harness, lost on a cold start.

Decision: a `.ai/.current` cursor file in both profiles, recording the active
ticket/change id, the current task/spec file, the modified-files list, and the
date. Read at session start (offer to resume); updated on task start/finish;
deleted when the work item is done.

- **Gitignored, not tracked.** It is per-checkout working state, not shared
  knowledge: resuming always happens in the same working copy, so on-disk
  persistence is enough, and tracking it would churn KB history and force a
  commit on every cursor update. Added to `.ai/.gitignore` next to `external/`.
- **Does not fight the Stop hook.** `ai_repo_clean` runs `git -C .ai status
  --porcelain`; an ignored file never appears, so the hook stays quiet.
- It is the on-disk backup of exactly what the compaction-preserve item asks
  the harness to keep; the two are complementary, not redundant.

### 14.2 Running memory for runbooks/gotchas (`.ai/notes.md`, large profile)

Problem: the highest-value knowledge the mature legacy agents carried was
*procedural/operational* — validation loops, CI failure modes (e.g. stale
`workflow_dispatch` keys → HTTP 422), merge-order rules. The large profile's
node taxonomy (architecture/conventions/domain/infra/decisions/references) has
no natural home for this volatile, list-shaped knowledge; it would either bloat
a curated node or be lost.

Decision: give the large profile the same `.ai/notes.md` the small profile
already had, rather than invent a new typed node category (the smaller change,
and the graduation path already assumes `notes.md` exists). It is the **volatile
layer**: read at session start, appended telegraphically as gotchas surface;
anything durable and structural is **promoted into a curated node via
kb-delta.yaml**. Curated nodes remain the single source of truth; `notes.md` is
scratch/operational memory beside them. The stub text now names runbooks and CI
quirks explicitly so the genre is obvious in both profiles.

### Unchanged
KB layout and protocol, manifest navigation, hot/cold tiers, kb-delta, drift
and staleness model, ticket lifecycle + archive, review gates, two-register
language, size profiles, single-interactive-scaffold CLI.

## 15. Knowledge-base import (2026-06-26, v5.4)

`/import-kb <source>` ingests an *existing* knowledge base of arbitrary
structure — a docs/wiki folder, a Confluence/Markdown export, a README-heavy
repo, or a legacy `.ai/` (e.g. the ancestor agents' `docs/` chapters) — and
transforms it into the framework's own shape. The transform is the model's job,
not a parser's: the input has no fixed schema to match ("regardless of
structure"), so a deterministic importer cannot exist. The skill encodes a
read → classify → transform protocol; the model supplies the understanding.

### Why a skill, not a tool
The input layout is unknown by definition, which is exactly what an LLM is for:
read heterogeneous material, infer what each piece *is*, map it onto the target
taxonomy. A script could only handle one known layout. The deterministic parts
the skill reuses are the ones the framework already owns: `gen_index.py` for
INDEX, the manifest format, the node frontmatter schema.

### Protocol (both profiles)
1. **Survey, don't bulk-load.** List the source tree, sample entry/index/README
   files, run the survey in a sub-agent where available, return a condensed map.
   The source may be huge; it never enters the synthesizing context wholesale.
2. **Classify** each piece of content into the target shape.
3. **Transform, don't copy.** Synthesize into telegraphic content, dedup against
   existing knowledge (merge, never a second source of truth), record provenance
   (source path/URL) so the import is auditable.
4. **Wire up + commit.** Regenerate the dependent artifacts, commit `.ai`, report
   a source→target mapping and list the unclassifiable remainder for the user.

### Profile differences
- **Large**: targets are KB nodes under the six categories; operational
  gotchas/runbooks route to `notes.md` (§14). Output is full nodes with
  frontmatter and `covers` globs matched to real code paths; `manifest.yaml` +
  `INDEX.md` + the project-context section are regenerated.
- **Small**: no node store; the skill distills stable facts into the AGENTS.md
  project-context section and routes the rest to `notes.md`. Large bodies worth
  only searching are cloned into `.ai/external/` and noted, not inlined. The
  small profile now carries four skills (`/explore`, `/spec`, `/build`,
  `/import-kb`).

### Boundary vs /add-reference
`/import-kb` *absorbs and transforms* curated knowledge into the KB (the source
can then be retired). `/add-reference` *keeps raw external material* under
`.ai/external/` as search territory and registers only a thin pointer node, no
transformation. Code or upstream docs you only want to search later go through
add-reference; a prior team's documentation you want to *become* your KB goes
through import-kb. The skill body states this distinction so the agent chooses
correctly.

## 16. More determinism offloaded to scripts/hooks (2026-07-01, v5.5)

Continues §12.6's "deterministic tools + hooks over protocol prose". Three
mechanical jobs that were LLM-driven (or standing prose instructions the model
had to remember) become scripts/hooks. Motive: save tokens on the most
expensive work and make the outcome reproducible. `ai_repo_clean` stays
unchanged — content commits keep model-written, meaningful messages (owner
decision; auto-templated messages rejected).

1. `probe.py` (`.ai/agent/tools/`, both profiles): read-only, stdlib-only repo
   inventory. Uses `git ls-files` (gitignore-aware, deterministic; `os.walk`
   fallback). Prints compact, stable-sorted Markdown to stdout: host commit
   SHA, language mix, detected build/test/lint commands (package.json scripts,
   Cargo/Go/Python/Ruby manifests, Makefile targets, ROS 2/colcon via
   package.xml, vcstool .repos, Snapcraft, Debian packaging via
   debian/control, Docker/Compose, GitHub Actions workflow list), module map
   with files + LOC, dependency manifests, entry-point candidates. First step of Phase 1
   (large) and `/explore` (small): the mechanical `project-context` fields are
   seeded from it, not re-derived by the model, and its map drives sampling.
   Biggest single lever — the initialization phase is the costliest.
2. Auto-INDEX (PostToolUse hook `regen_index.py`, large only): runs
   `gen_index.py` whenever `manifest.yaml` is written, always exit 0
   (non-blocking; the write already succeeded). Replaces the standing prose
   rule "after a manifest change, run gen_index". `protect_generated` (blocks
   hand-edits of INDEX.md) stays. On non-claude harnesses (no hook) the phase
   docs still tell the agent to run `gen_index.py`.
3. check_stale at session start (SessionStart hook, large only): runs the
   existing `check_stale.py` with `|| true` (neutralizes its CI exit code);
   its stdout enters the session as context. Replaces the prose "run it at the
   start of operational sessions". Manual run kept for after a merge / non-
   claude harnesses.

Not in scope (future iterations, tracked): `apply_delta.py` (declarative
metadata/covers auto-apply), `drift.py` (bundle the per-node drift diffs),
archive + ADR-number helpers. Node content, classification, planning, and the
review gates stay with the model — that is genuine judgment, not mechanism.

## 17. Harness-mechanism pass (2026-07-02, v5.6)

Web-research review of the concept against mid-2026 best practice (Anthropic
context engineering, Claude Code best-practices docs, AGENTS.md/AAIF status,
SDD field reports) confirmed the foundations and surfaced newer harness
features the framework predated. Theme continues §16: replace protocol prose
with harness mechanism as harnesses grow them. Copilot support is unchanged
throughout — every claude-specific mechanism is additive, with the manifest
protocol as the fallback on other harnesses.

1. **Skills locked to manual invocation.** Every scaffolded skill is a
   user-sequenced pipeline step with side effects (KB writes, code changes,
   `.ai` commits); `disable-model-invocation: true` prevents the model from
   auto-triggering them mid-conversation (e.g. starting /plan on sight of a
   ticket). `argument-hint` added for discoverability. Copilot prompt files
   have no such field and are unchanged.
2. **Path-scoped rules as generated artifacts (claude, large).** Cold
   `conventions/*` nodes with non-empty `covers` render to
   `.claude/rules/<id>.md` with `paths:` frontmatter via `gen_rules.py`:
   the harness now injects the convention deterministically when matching
   files are touched, instead of the model remembering the manifest lookup.
   Same pattern as the AGENTS.md generated section: node = source of truth,
   rule = build artifact (marker line, stale-file cleanup). The
   regen hook fires on conventions-node and manifest writes;
   `protect_generated` blocks edits to marked rule files (hand-written
   rules stay editable). Hot nodes excluded (already in the AGENTS.md
   section — no duplication); nodes without `covers` stay manifest-loaded.
3. **Parallel-ok task marking.** `/plan` sets `parallel: ok` on tasks with
   no `depends` and no overlapping affected files; plan.md's table gains a
   Parallel column. implementation.md defines the dispatch constraints:
   one self-contained task file per session, `.ai` single-writer (only the
   coordinating session commits), worktree caveat (gitignored `.ai/` is not
   carried over), review gate stays serial on the combined diff. Zero
   machinery — the self-contained task files already made this safe; the
   protocol now says so. Harness-neutral.
4. **/goal as middle verification tier (claude).** The Phase-1 verification
   offer now names the session-scoped `/goal` condition as the lighter
   alternative to the scaffolded lint/test Stop hook. Both profiles.
5. **Prune test in KB lint.** Monthly lint + implementation.md gain the
   canonical deletion criterion for standing instructions: if the agent
   already behaves correctly without a rule, delete it (§5).
6. **README corrections.** The `ai_repo_clean` "never lost" claim softened
   (Claude Code overrides a Stop hook after repeated consecutive blocks;
   protocol rule = backstop); auto permission mode noted as the
   low-maintenance interactive alternative to the scaffolded allowlist.
7. **Two-register A/B made runnable.** §8's validation path was given a
   benchmark spec instead of a standing intention (later removed unrun when the
   benchmarks were consolidated to a single fixed runbook).

Rejected in this pass: subdirectory-CLAUDE.md pointers for module nodes
(weaker duplicate of item 2), embedding retrieval (still wrong below ~200
nodes), auto-migrating the allowlist to auto mode (allowlist stays default:
deterministic, works headless).

Unchanged: KB layout, manifest navigation, hot/cold tiers, kb-delta, drift
and staleness model, ticket lifecycle + archive, review gates, two-register
language, size profiles, model-agnosticism, single-interactive-scaffold CLI.

## 18. Project-context freshness + ecosystem-neutral criteria (2026-07-02, v5.7)

Two small refinements after v5.6, both surfaced and then validated by benchmark
runs (the multi-eco set and the sonnet5-medium regression cell). No new
machinery; both harden existing behavior.

1. **End-of-change project-context refresh.** The always-loaded AGENTS.md
   `GENERATED:project-context` digest had no regenerator outside `/explore` and
   re-init: INDEX.md and path-scoped rules auto-regenerate via hooks (§16.2,
   §17.2), but the digest could silently drift once implementation changed a
   build command or the module map. Fix: a bounded step at the end of small
   `/build` and large implementation.md — re-run `probe.py`, compare its
   build/test/lint commands and module map against the digest, and refresh the
   section only for a changed command or a new/removed/renamed module. A bare
   LOC delta on an existing module is explicitly **not** actionable (that
   exclusion came from the sonnet5-medium run, where a +26-line file tripped a
   false rewrite). Deliberately a model-run step, not a hook: `probe.py` output
   is the mechanical input, but deciding whether the curated human-readable
   digest needs an edit is judgment. Validated: fired and caught a real
   new-`make deb`-target drift in the sonnet5-medium-small-v2 cell, and fired
   5/5 in the multi-eco round while correctly staying quiet on LOC-only drift.
   One graduation exception rides this step (2026-07-04): probe.py prints a
   code-only `Code LOC` total, and if it exceeds ~10k in a small-profile
   project, `/build` proposes re-initializing as large (§13). Threshold-based,
   no stored snapshot needed; proposal only, never an automatic migration.
2. **Ecosystem-neutral correctness criteria.** The `/spec` skill and large
   task-file format ask for acceptance criteria that name the relevant
   linter/policy check (§12, ecosystem correctness). The example list named
   only `lintian` and `clippy` — the two ecosystems benchmarked at the time
   (Debian packaging, Rust) — biasing agents on other stacks toward
   benchmark-flavored criteria. Diversified to `eslint, mypy/ruff, clippy,
   shellcheck, lintian, schema validators` with "for the ecosystem you touch"
   framing. Found by a static overfitting audit; confirmed by the multi-eco
   run, where agents named their repos' own gates unprompted (pytest, mypy,
   flake8, shellcheck) with no lintian/clippy reflex.

The multi-eco round (Python/Shell/C++-ROS × bugfix/feature/refactor) found no
framework defects; the harness-side fixes it did surface (container image,
brief premise, parallel-orchestration) were benchmark-harness details, not
framework changes.

## 19. Small-profile notes hub (2026-07-03, v5.8)

The small profile stored durable knowledge in a single flat `.ai/notes.md` plus
the curated project-context digest. Flat is right while notes are small (the
whole file is cheap to read whole), but on a long-lived small project the log
grows and every session re-reads all of it. Fix: `notes.md` may become a
hub-and-spoke — a linked index whose detail lives in `.ai/notes/<topic>.md`
leaves, so a session reads the compact hub and opens only the leaves a task
needs. This is the large profile's manifest→node retrieval principle done with
plain markdown links and none of its machinery (no manifest, no generated
INDEX, no hot/cold tiers, no budgets, no kb-delta). Same shape as this repo's
own auto-memory (`MEMORY.md` index + one-file-per-fact leaves).

Design choices:
- **Progressive, threshold-triggered.** Start flat; once `notes.md` passes ~1-2
  screens, move topic clusters (largest first) into leaves until the hub is back
  under ~1 screen. Never split while notes stay short — the index-plus-leaf read
  is strictly more expensive than one small file. (The "largest cluster only,
  once" wording of the first draft under-split a mature project — hub stayed
  over threshold, ~14% read reduction; corrected to split-until-under-threshold
  after the A/B below.)
- **Guidance only, no tooling.** Lives in the AGENTS.md protocol, the notes.md
  stub, `/explore` (read hub first), and `/build` step 5 (split + keep links in
  sync). The link-integrity check (every leaf linked, every pointer resolves)
  rides the existing end-of-build project-context refresh — no new hook.
- **No staleness guard, by design.** Small dropped `check_stale.py`; the hub is
  the volatile notes layer (not curated architecture) and the source is read
  JIT, so a stale leaf is low-cost. A project that needs `covers`-addressable,
  staleness-guarded memory has outgrown small — re-init as large (carries the
  digest over).

Validated by a controlled A/B (sonnet-5 medium, same repo + task, notes size the
only variable): a seeded 84-line notes.md split correctly (hub + leaf, links in
sync); a fresh 43-line notes.md correctly stayed flat. Both code gates green.

## 20. Automatic profile selection (2026-07-03, v5.9)

`init-agent` now picks the size profile from the codebase itself instead of
defaulting to large. When `--size` is omitted (or given as `auto`), it counts
lines of code across the host repo's source files and applies the §13 boundary:
`<=10k LOC` -> small, above -> large.

- **LOC estimate (`estimate_loc`).** Reuses probe.py's file-discovery model:
  `git ls-files` when the target is a git repo (deterministic, gitignore-aware
  so lockfiles/vendored trees don't count), else an `os.walk` fallback that
  skips `.git`, `.ai`, and common vendor/build dirs. Counts only code
  extensions (`CODE_EXTS`) — docs, data, and markup (`.md`, `.json`, `.yaml`,
  `.toml`, `.html`, `.css`) are excluded so the number reflects code the agent
  must reason about, not prose or generated files. Threshold is the single
  constant `SIZE_LOC_THRESHOLD = 10000`, matching §13's ~10k boundary.
- **Interaction.** `--size auto` (explicit) selects silently. `--size
  large|small` still forces that profile — an explicit flag always wins. With
  no flag and a TTY, the auto pick becomes the *default* of the existing size
  prompt, so the estimate is shown and the user can veto it; with no flag and
  no TTY (scripted), the auto pick is used directly. Graduation between
  profiles stays a deliberate re-init, per §13, never a side effect of an
  update; v5.14 moved updating out of the CLI entirely and `/update` reports a
  profile mismatch rather than acting on it (§24).

Validated on real and synthetic repos: ha-core (2.29M LOC) -> large,
network-status (30 LOC) -> small; a synthetic 12.6k-LOC git project scaffolds
large and a 90-LOC one scaffolds small, with explicit-override, non-git
fallback, and the (since removed) `--update --size auto` edge cases all
correct. Scaffold path only
(no explore run).

## 21. Explore-freshness guard + notes.md pointer clarification (2026-07-06, v5.10)

Investigated a proposal: could the small profile's `.ai/notes.md` carry more
steering — pointers to sub-repos/folders, or an architecture overview — so a
fresh session finds the right code faster instead of re-deriving structure by
search. Surveyed four real deployments of this framework
(`ha-value-crossing`, `ha-weatherstage`, `navigation2`, and this repo itself)
rather than reasoning in the abstract.

Findings:
- The mechanism the proposal wants **already exists** and, when used, works
  well: the small profile's `GENERATED:project-context` section in AGENTS.md
  (module map, tech stack, glossary — filled by `/explore`) and the large
  profile's `architecture/*` KB nodes. `ha-value-crossing`'s digest has a
  precise per-file module map; `navigation2`'s KB has a real module-oriented
  architecture split. Adding a second architecture home inside `notes.md`
  would duplicate this and violate the standing single-source-of-truth
  invariant (§13's design rule) — this is the collision the proposal itself
  anticipated. **Rejected.**
- "Pointers to other repos/folders" already happens, unprompted, inside
  `notes.md` — `ha-weatherstage`'s notes point at
  `ha-value-crossing`'s `.venv-ha` for running its HA-aware tests. This fits
  the stub's existing "operational runbooks" genre; it was just never named
  as an explicit example, making it a discoverability gap rather than a
  missing capability.
- The real gap: the project-context digest has **no freshness guard**. This
  repo's own `AGENTS.md` is the live counterexample — its digest still reads
  the scaffold-time placeholder ("CLI tool and Python library for
  manipulating SQLite databases", left over from a §20 test run) while
  `.ai/notes.md` has 60+ lines of real, current decisions. `/explore` was
  simply never invoked here, and nothing short-circuits non-trivial work on
  a repo whose always-loaded digest is still a stub or wrong. A fresh session
  reading this file cold gets actively misled about the project's purpose —
  the opposite of the token efficiency the digest exists to buy.

Decision: two guidance-only edits (no new tooling, matching the §19
precedent), both in the shared stub renderers:
1. Small-profile Protocol item 1 (`render_agents_md_small`) now tells the
   agent to check the Project Context section first and run `/explore` before
   non-trivial work if it is still just the seed one-liner or the raw
   `Populated by /explore` marker with no module map/commands.
2. The `notes.md` stub (`render_notes_stub`, shared by both profiles) now
   names "pointers to related repos/paths this project depends on" as an
   explicit example of what belongs there, and restates in the same breath
   that architecture/module-map content stays in the Project Context section
   — sanctioning the observed-useful pattern without opening the door to
   duplicating the digest.

Rejected alternatives: seeding the digest from `probe.py`'s mechanical output
at scaffold time (would help, but the framework deliberately keeps `probe.py`
output out of the committed scaffold — see `--debug-probe`'s `PROBE.md`,
explicitly "not part of the scaffold" — so this would be a separate, larger
design change, not a minor steering fix); a dedicated `references/`-style
node for small (already covered by `.ai/external/` + a `notes.md` line per
§13's dropped list; small deliberately has no node machinery).

## 22. /goal as a documented autonomous-dispatch mode (2026-07-08, v5.11)

2026's "loop engineering" trend (self-prompting agents that run turn after
turn until a stated condition holds — Claude Code's native `/goal`/`/loop`,
the community Ralph Wiggum technique) was checked against this concept.
Comparison found the two are answering different questions rather than
competing: right-sizing decides *how much ceremony a task needs*; `/goal`
decides *whether a human supervises turn-by-turn or the agent runs
unsupervised toward an already-stated finish line*. Nothing in the concept
previously said anything about the second question beyond one throwaway
line (§17 item 4: "/goal ... the lighter alternative to the scaffolded
lint/test Stop hook").

Key finding driving the design: `/goal`'s own condition text is not
automatically the spec's (or plan's) acceptance criteria — it is exactly
and only the string the user types after `/goal`, checked each turn by a
separate, fast model. `/build` and `/implement` already have a rigorous
definition of done baked into the skill (acceptance criteria checked off,
gate green, reviewer clean); if the `/goal` condition restates that
loosely ("build spec-01") instead of pointing at the artifact directly, the
condition-checker's bar and the skill's own bar can silently drift apart —
the checker might call it done a step early (e.g., before the reviewer
runs) because nothing in the condition said that step was required.

Decision: document `/goal` as a **supervision mode layered on the existing
paths, not a third size tier and not a new definition of done**. Added to
both profiles' `AGENTS.md`, `claude`-harness only (`/goal` has no Copilot
equivalent), right after Right-sizing:
- A decision rule for when it applies: the finish line must be
  machine-checkable (tests, lint, a named gate script), and no mid-flight
  judgment call is expected — a `/goal` loop cannot ask the user a
  question, so it is the wrong tool the moment ambiguity is likely.
- A fixed condition-phrasing convention that points at the artifact
  already defining done instead of restating it: `.ai/changes/<id>/spec.md`
  (small) or `.ai/knowledgebase/tasks/<id>/plan.md` (large), plus the gate
  and the reviewer's sign-off.
- A paired stall clause, reusing the existing typed-escalation wording
  verbatim (test-fail-twice → stop, never a third blind attempt) rather
  than inventing a new guardrail — this was the one gap the loop-engineering
  comparison actually surfaced: the concept had no generic iteration/budget
  ceiling in prose, only that one specific escalation trigger.

Hardened after a doc-check against the official /goal and /loop references
(2026-07-08, same version):
- The goal evaluator reads only the transcript — it never runs commands or
  reads files — so the scaffolded condition examples now require the agent
  to *show* the checked-off criteria and the gate's exit status in output,
  not merely reach them; a condition that only names a file leaves the
  evaluator guessing.
- A turn-cap clause ("or stop after N turns") now rides both condition
  examples — the docs' own bounding mechanism, closing the budget-ceiling
  gap noted above with zero new machinery.
- Because scaffolded skills are `disable-model-invocation: true` (§17.1),
  a /goal loop cannot load `/build`/`/implement` itself: the documented
  ordering is invoke the skill first, then set the goal, so the procedure
  is already in context for every loop turn. For the same reason,
  `/loop <interval> /build <id>` delivers the skill as plain text instead
  of executing it (v2.1.196 scheduled-fire semantics) — the framework does
  not use /loop, recorded here so nobody debugs it as a defect later.

Usage pattern this surfaced: `/goal` is a **second way to drive the
framework, running alongside human-supervised spec-then-build rather than
replacing it**. Turn-by-turn supervision (write a spec, watch `/build`
implement it, review the diff) stays the default for one-off or
judgment-heavy work. `/goal`'s complement is a backlog of several
already-scoped, independently checkable tasks (a ticket queue, a handful of
specs already written) worked through in one continuous session without a
human re-approving between them. Within that session, discovery already
surfaced for the first task (the project-context digest, `notes.md`, files
already read) carries forward in-context for free through later tasks — no
rediscovery — as long as the window doesn't fill. The two risks that erase
that saving are exactly why `notes.md` is worth writing to mid-loop, not
only at `/explore` time: compaction (detail lost to summarization once the
window fills) and context rot (earlier detail degrading before any hard
compaction event). `notes.md` is the loop's insurance against both — cheap
to write, and the reason the framework's persistence layer and `/goal`'s
unsupervised dispatch reinforce each other rather than being unrelated
features.

Rejected: treating `/goal` as a new top-level path alongside trivial and
ticket-driven work (first draft of this idea) — cleaner to model it as
orthogonal to sizing, since the same spec or plan is used either way and
nothing about the artifact format changes. Also rejected: adopting
heartbeats/crons/hooks (the other loop-engineering patterns) as core
mechanisms — they answer "run on a schedule/event with nobody watching,"
a use case this concept is not built for (every unit of work starts from a
human-filed ticket or invocation by design); worth a deliberate look only
if scheduled maintenance-style agents become an actual separately-scoped
goal, not a reason to retrofit the pipeline now.

## 23. Worker sub-agents on a mid-tier model (2026-07-17, v5.12; removed 2026-07-28, v5.13)

v5.12 scaffolded two optional agent definitions (claude harness only, both
profiles), each pinning `model: sonnet` in frontmatter: `code-worker`
implemented one fully specified change item dispatched by the main agent,
`explore-helper` was the read-only collector for the exploration fan-out.
Planning, specs, review gates, and digest/KB curation stayed on the strong
tier, and the dispatcher re-verified every gate.

v5.13 removes both definitions and every dispatch instruction that named
them (phase 1 explore bullet, phase 3 "Worker dispatch" section,
small-profile /explore and /build skills, the runbook's W arm). Two reasons:

1. Harness leakage. The agent definitions were claude-only, but the dispatch
   guidance lived in harness-neutral text (phase docs, `command_specs_small`).
   Copilot scaffolds therefore instructed the agent to dispatch to
   `code-worker` and `explore-helper`, which do not exist there. Any revival
   has to gate the prose on `harness == "claude"`, not only the file writes.
2. The measurement came back negative. The W arm ran once
   (`benchmarks/w4-sonnet5-medium-2026-07-17/`, sonnet-5 x medium, cell-4
   py-feature, worker pinned to the same tier as MODEL). Both twins passed
   the gate; the worker twin cost +35% total tokens, +40% output, +43%
   estimated cost, with only wall-clock active time slightly lower. §13's
   scale threshold applies to delegation as well: brief construction, worker
   cold context, report-back, and re-verification exceeded the discovery
   noise kept out of the orchestrator.

What survives the removal:
- §3 stands unchanged and now has no exception: routing is the user's, via
  harness controls; the framework pins no tier anywhere.
- The generic guidance the workers were attached to stays, phrased without
  named agents: run the exploration fan-out in sub-agent contexts, cap each
  return at ~2000 tokens, and never let a sub-agent write the digest, notes,
  or KB (digest errors compound across every later warm start).
- The asymmetry rule from the 2026-07-04 round is unaffected: low-tier
  self-reported PASS is not a gate result, so gates are re-verified by
  whoever owns them.

Conditions for a revival, if one is ever attempted: harness-gated prose, a
worker tier actually cheaper than MODEL (the measured pair used the same
tier, so a price gap remains untested), and a repo large enough that
discovery noise dominates dispatch ceremony. The recorded W round stays in
`benchmarks/` as the evidence; the runbook arm that produced it is retired.

## 24. Agent-driven framework update (2026-07-28, v5.14)

`init_agent.py -u/--update` regenerated every framework-owned file and froze
every hand-filled one (`write` vs `write_owned`). Measured against a real
scaffold, that binary ownership model loses in three ways:

1. **Retired files survive forever.** `-u` only writes; it never deletes. A
   project scaffolded on v5.12 keeps `.claude/agents/code-worker.md` after an
   update to v5.13, which withdrew it. Confirmed on a test scaffold: the file
   was still there after `-u`, and nothing in the report mentioned it.
2. **User edits to framework files are silently reverted.** A permission entry
   added to `.claude/settings.json` was gone after `-u`, unreported. The same
   holds for rules appended to AGENTS.md outside the generated markers.
3. **The shape of hand-filled content can never change.** `write_owned`
   refuses to touch a file whose content differs from the stub, which is
   correct for content and wrong for structure: a new frontmatter key, a new
   manifest field, or a renamed directory never reaches an existing project.
   The KB is preserved and silently frozen at the schema it was born with.

Two smaller ones: nothing recorded which framework version built a scaffold,
so an update could only overwrite unconditionally; and the pre-update snapshot
covered `.ai` only, while AGENTS.md, CLAUDE.md and the harness directory live
in the host repo and were overwritten with no rescue copy.

What did work and is kept: `extract_generated` carries the
`GENERATED:project-context` section across a regeneration in both profiles
(verified for small and large), and `write_owned` protects KB node bodies.

**Decision.** An update is a three-way merge (project state, previous
framework, current framework) plus a schema migration. Both are judgment
calls, so the agent owns them and the CLI provides only what is deterministic:

- **Version stamp.** `.ai/agent/framework.json` records `framework_version`,
  `profile`, `harness`, `project`, `generated`, and `framework_files` (every
  framework path that version emitted, collected by `write()` itself so the
  list cannot drift from the writes). `recorded framework_files` minus
  `reference framework_files` is exactly the retire set, so defect 1 becomes
  a set difference rather than a guess.
- **`--emit-reference DIR`.** Renders a pristine scaffold of the current
  framework into an empty dir with no git init, no gitignore edits, no commit,
  no host-project side effects. This is the comparison target; a real project
  is never compared against a re-run over itself.
- **`--detect`.** Prints the stamp as JSON, falling back to inspecting the
  tree for scaffolds that predate the stamp (version `null`, empty file list,
  so the skill knows nothing can be retired deterministically).
- **`/update` skill**, both profiles, both harnesses. Preflight (read the
  stamp, commit `.ai`, copy the host-repo framework files to the gitignored
  `.ai/agent/.update-backup/`, refuse to proceed silently over uncommitted
  work) -> render the reference -> classify every path as added / identical /
  framework-changed / user-edited / retired and act per class, merging the
  user-edited ones and deleting the retired ones together with the
  instructions that still named them -> migrate hand-filled content into the
  new shape in place -> verify every referenced tool runs -> rewrite the stamp
  and report one row per file. `dry-run` stops after classification.

The governing rule, stated in the skill itself: the knowledge is the
expensive artifact and the framework files are cheap, so `/update` never
re-runs `/explore` and never regenerates hand-filled content from a stub. If
a new field cannot be derived from what the project already records, it is
left empty and reported, not invented and not researched from the codebase.

Harness gating is explicit per §23's lesson: the merge cases, the backup
paths, and the verification steps name `.claude/settings.json` and hooks only
on claude, and `.github/prompts/` only on copilot. The skill body is built by
one `render_update_body(size, harness, arg)` so both axes stay in one place.

Not in scope: profile switching. Graduating small -> large stays a deliberate
re-init per §20; `/update` detects a codebase that has outgrown its profile
and says so in the report instead of migrating on its own.

**Measured** (`benchmarks/u-update-sonnet5-medium-2026-07-28/`, sonnet-5 x
medium): a v5.12 Satty scaffold with a real `/explore` digest, real notes, and
hand edits, updated to 5.14 by an agent following only the skill. Gate 13/13:
the 4540-byte project-context digest came through byte-identical, notes and the
hand-added AGENTS.md section survived, the two user-added permissions survived,
both retired worker definitions were deleted with no dangling references, and
the agent never read the codebase. Two runs were needed. The first exposed the
design's one real hole: retirement rested on the recorded `framework_files`
list, which is empty on every scaffold that exists today, and the fallback rule
said to treat unmatched files as the user's. Defect 1 was therefore fixed only
for scaffolds not yet created. The fix is an **orphan test** that asks the
generator's own history instead of the stamp:

    git -C "$LLM_AGENT_HOME" log --oneline -S'<basename>' -- init_agent.py

Commits found means the framework emitted the file and a later version dropped
it, so retire it; none means the user wrote it, so leave it; no git checkout
means undecidable, so report it. This makes retirement work on legacy scaffolds
without a stamp, which is the only case that matters in the field. Three smaller
instruction fixes came from the same runs: ensure `.ai/.gitignore` covers the
backup path before writing it (legacy scaffolds lack the entry), separate
untracked from tracked-and-modified in the stop condition (an
uncommitted-scaffold host repo is normal, not a reason to block), and carry
profile/harness explicitly from preflight into the reference render.

## 25. Migrating an existing .ai/ folder (2026-07-29, v5.15)

`/import <source>` migrates a whole prior `.ai/` working directory - an older
version of this framework, or a differently-shaped agent folder - into the
current structure. It runs after scaffolding, against a copy of the old folder
(move the pre-existing `.ai/` aside to `.ai.old/` before init, then
`/import .ai.old`), because init writes a fresh `.ai/` and a foreign layout has
no owned files for `write_owned` to preserve.

### Why it is separate from /import-kb (§15)
`/import-kb` transforms *arbitrary curated knowledge* (a docs/wiki dump, a
README-heavy repo) into KB nodes and deliberately ignores task and ticket state
(§15 last paragraph: "transform docs/ into nodes and ignore its task and ticket
state"). That is the wrong operation for a prior `.ai/` you want to keep working
in: you would lose the inbox, the planned/in-progress tasks, the decisions, and
the running notes. `/import` is the migration counterpart - it carries the
*lifecycle state* across as well, and upgrades already-framework-shaped nodes in
place (re-categorize, rewrite frontmatter to the current schema, re-match
`covers`) rather than re-synthesizing them from scratch. For the knowledge that
is not already node-shaped it reuses the /import-kb read->classify->transform
protocol, so the two skills share machinery without duplicating intent. The
four-way boundary the skill bodies state so the agent chooses correctly:
`/add-reference` keeps raw material for search; `/import-kb` transforms curated
knowledge into nodes; `/import` migrates a whole `.ai/` working directory,
knowledge and state; `/update` (§24) upgrades a scaffold this framework already
wrote.

### Why it is separate from /update (§24)
Both move a prior `.ai/` to the current shape, but they start from different
material. `/update` operates on a scaffold this framework wrote, identified by
its `.ai/agent/framework.json` stamp: the file list is known, so the work is a
file-by-file merge plus retirement of what the framework dropped. `/import`
starts from a folder with no stamp - an older pre-stamp version, or a foreign
agent layout - where nothing about the source can be assumed, so the work is
classification before migration. The decision rule the skill bodies carry:
stamped scaffold -> `/update`, unstamped or foreign -> `/import`. Because
`/import` runs after a fresh init, the current scaffold's stamp is already
correct; `/import` must never overwrite it with the source's copy, or the next
`/update` would diff against the wrong version.

### Why a skill, not a tool
Same reasoning as §15: the source layout is unknown by definition (any prior
version, or a foreign framework), so no deterministic parser can exist. The
model reads heterogeneous input, infers what each piece *is* (a node, a ticket,
a plan, a decision, a note), and maps it onto the current shape. The
deterministic parts it reuses are the ones the framework already owns:
`gen_index.py`, the manifest format, the node frontmatter schema, the ticket and
changes layouts.

### Protocol
Survey (sub-agent, condensed map, detect large|small|foreign layout) ->
migrate knowledge (upgrade node-shaped content in place; classify+transform the
rest) -> migrate lifecycle state (tickets -> inbox; planned/in-progress ->
tasks/<id>/ with status preserved in frontmatter; finished -> _archive/;
decisions -> decisions/ nodes; external -> references/ + `.ai/external/`; notes
-> notes.md) -> regenerate the derived artifacts (manifest, INDEX,
project-context) from the migrated content rather than copying the source's
generated files, leaving `.ai/agent/framework.json` as init stamped it ->
report a source->target mapping, list the unmappable remainder, preserve the
source, commit `.ai` (`import: <source>`).

### Profile differences
- **Large**: full migration into KB nodes plus the ticket/task pipeline;
  `manifest.yaml` + `INDEX.md` + the project-context section are regenerated.
- **Small**: no node store; distill the source's stable facts into the AGENTS.md
  project-context section, route the rest to `notes.md`, and carry in-flight
  work into `.ai/changes/<id>/spec.md` (finished ones to `_archive/`). A
  large-profile source's hot-tier nodes are distilled down, not reproduced.

### Profile mismatch
The source's profile and the current scaffold's profile need not match; `/import`
maps the source's content onto the *current* profile's targets rather than
recreating the source's shape (a small source's project-context becomes nodes in
a large scaffold; a large source's node store is distilled into project-context +
notes in a small scaffold). The small profile now carries seven skills
(`/explore`, `/spec`, `/build`, `/import-kb`, `/import`, `/tidy-up`,
`/update`).

## 26. Hygiene sweeps as a skill (2026-07-29, v5.16)

`/tidy-up [scope]` sweeps the host code for four kinds of rot: dead code,
obsolete files, overlong comments, and em dashes in prose. It is maintenance,
not a phase and not a ticket, so it sits beside `/update` rather than inside
the pipeline.

### The constraint that shapes it
A tidy-up may not change behavior. That single rule is what makes the skill
safe to hand an agent, and it is enforced structurally rather than by asking
nicely: step 0 captures a green build/test/lint baseline and refuses to start
without one, step 5 re-runs the same commands and compares. Without the
up-front baseline the agent cannot distinguish a break it caused from one it
inherited, which is the failure mode that makes automated cleanup dangerous.
Anything that would change behavior is out of scope by definition and becomes
a change spec instead.

### Why the four passes carry different authority
Removing dead code and rewriting prose is reversible and locally verifiable,
so the agent does it. Deleting a file is neither: the evidence that a file is
unused is always circumstantial (nothing references it *that a search found*),
and the cost of being wrong is unbounded. So pass 2 only proposes, with a
table of path, reason, blast radius, and confidence. This asymmetry is the
design, not caution for its own sake: the passes are ordered by how cheaply a
mistake can be detected and undone.

### Dead code needs evidence, and a library has none
The pass states where a plain search goes blind (reflection, plugin
registries, dependency injection, serialized field names, conditional
compilation, generated bindings, packaging entry points) because an agent that
greps for a symbol and finds nothing will otherwise conclude it is dead. The
sharper rule: in a library, an exported symbol is not dead because this repo
does not call it. Removing it is an API break, so the public surface counts as
used. Ecosystem tools that report unused code are treated as a candidate list
to verify, never as authority.

### Comments: a line count that cannot destroy knowledge
Shortening comments to 1-2 lines is trivially satisfiable by deleting them,
which is the wrong outcome. The pass therefore separates narrative that
restates the code (compress or delete) from information the code cannot carry:
why, invariants, workarounds, citations. That content is compressed if it
fits and relocated with a pointer if it does not. Licence headers, SPDX tags,
generated-file banners, and published API documentation are exempt from the
count entirely.

### Em dashes: a register rule the framework owed itself
§8 has required plain punctuation in generated artifacts since v1. The
generator was violating it: nine em dashes in `init_agent.py` templates
reached ten files across the four scaffold variants. Those were rewritten by
clause (parenthetical to commas, break to colon or full stop) rather than
swapped character for character, which is the same instruction the pass gives.
Fixtures, golden files, vendored sources, licence texts, and data files are
excluded, because there the character is the data and editing it is a
behavior change.

### Profile and harness differences
- **Large**: removals can invalidate KB nodes whose `covers` globs matched a
  deleted path; those nodes and their `manifest.yaml` entries are updated and
  `INDEX.md` regenerated.
- **Small**: the module map in the project-context digest is updated only if a
  module disappeared, and durable findings append to `notes.md`.
- **claude**: the survey fan-out runs in sub-agents that return evidence
  rather than file dumps, and the `reviewer` sub-agent takes the diff.
- **copilot**: search-based survey and a clean-context self-review, noted as
  such in the report.

Like every other skill, it commits `.ai` and leaves host-repo changes staged
for the user. The framework does not commit the host project repo.

## 27. Generator structure: content as files (2026-07-29, v5.17)

The generator was one 3093-line Python file in which two thirds of the lines
were not code. Measured by AST: 792 lines of skill body prose, 554 lines of
Python programs written as string literals, 312 lines of AGENTS.md text, 272
of phase docs, 151 of static config. About 600 lines were actual logic. This
section records why that was split and on what principle, because the shape
is easy to undo by accident.

### The principle
Content that the generator emits lives under `templates/` as a file of its
own kind: emitted Python as `.py`, emitted markdown as `.md`, emitted data as
a data file. Code decides *which* content applies and *what* fills its slots.
Prose does not live in string literals, and logic does not live in templates.

### What that buys
The 554 lines of embedded programs were the sharpest case. `probe.py` was 236
lines of Python that no linter, type checker, or test could see, because to
every tool it was one long string. Writing a `{` in it required remembering to
write `{{`. As a file it is just Python. The same move turned
`_MANIFEST_PARSER`, a code fragment that was spliced into three tools by hand,
into one file included in three places.

It also made a test layer possible for the first time. `tests/check_templates.py`
asserts properties that could not previously be asked: no template is orphaned,
every slot a template declares is filled by its caller, no rendered artifact
still contains a `${...}`, every rendered tool parses as Python, the rendered
settings parse as JSON, and no template carries an em dash (section 8, which
the generator had been violating in nine places).

### Slot syntax: why not str.format
Emitted content is full of literal braces: JSON, dict literals, f-strings
inside the generated tools. `str.format` would demand every one of them be
doubled, and a missed escape is a silent corruption rather than an error.
`string.Template.safe_substitute` ignores braces entirely, and it leaves
unknown `$NAME` alone, so the three harness variables that must reach the
output verbatim (`$ARGUMENTS`, `$LLM_AGENT_HOME`, `$CLAUDE_PROJECT_DIR`) need
no escaping either. The cost of `safe_substitute` is that a mistyped slot
fails silently, which is exactly what the slot check in the test layer exists
to catch. Slot names stay lowercase so they cannot collide with the
passthrough variables.

### The two axes stay in code
Profile and harness branch at 28 points, and the branches are sentence-level
rather than document-level: a clause that appears only on the claude harness,
a bullet only in the large profile. The tempting move is four copies of
AGENTS.md, one per variant. That is rejected: duplicated documents are how the
axes drift, which is the failure the "handle both or state why" rule in the
dev guide already exists to prevent. Instead the conditional prose is a
fragment file under `fragments/<harness>/` or `fragments/<profile>/`, and the
`if` that selects it stays in Python. Templates hold prose; they do not hold
conditionals, and no template language was introduced.

### Distribution was never the constraint
"Single stdlib file" read like a distribution requirement. It was not one.
`install.sh` git-clones the whole repo and the shell function runs
`$LLM_AGENT_HOME/init_agent.py` after a pull, so a sibling package and
template tree travel with it automatically. There is no `curl | python`, no
pip, no zipapp path. Python puts the script's own directory on `sys.path`, so
the imports resolve regardless of the working directory the user runs
`init-agent` from. If a single-file artifact is ever wanted, `zipapp` is
stdlib and can bundle the tree without changing the source layout.

### The refactor was verified, not reviewed
Restructuring 2081 lines of content by hand invites silent corruption, so the
move was gated on byte-identity: render all four size and harness variants
before and after, diff the trees, and require an empty diff. That harness
caught two real defects during the work that reading the diff would not have.
The first was an extraction script that neutralized `if __name__ ==
"__main__"` by rewriting the text, which also rewrote the nested guards inside
the templates. The second was `/update`'s description, which differs by
profile and had been collapsed to one string. Both surfaced as a failing diff
within seconds. No behavior changed in this revision: the emitted scaffold is
identical to v5.16 in all four variants, and the version bump records the
source layout, not the output.

## 28. Bootstrapping /update into a pre-5.14 scaffold (2026-07-29, v5.18)

§24 put updating in the agent's hands: an update is a merge, and merges need
judgment a scaffolder does not have. That leaves a gap at the bottom. A
scaffold built before v5.14 has no `/update` skill to run, so the agent has no
way in, and the obvious workaround is wrong.

### Why re-running init is not the workaround
Init overwrites framework files whole, which is all a scaffolder can do. On an
existing scaffold that was measured, not assumed:

- project rules appended below the framework text in AGENTS.md: gone
- a permission the user added to `.claude/settings.json`: gone
- files the framework retired two versions ago: still there, because `write()`
  has no concept of deletion
- re-running without `--harness` on a copilot scaffold: a `.claude/` tree
  appears next to the `.github/prompts/` one, and the stamp then names the
  wrong harness

Only the `GENERATED:project-context` section is rescued, because
`extract_generated` looks for it specifically. Everything else a user put in a
framework-owned file is lost silently.

### What the bootstrap does instead
`init_agent.py --bootstrap-update` writes exactly two things: the `/update`
skill (or its prompt-file equivalent) and a stamp. Nothing else is touched, so
there is nothing for it to destroy. Profile and harness come from
`detect_scaffold`, never from a flag, which removes the drift failure above by
construction. It refuses on a directory with no scaffold, and on one already
stamped with a version, where `/update` is the right tool and already present.

This is safe for a reason specific to skills: skill files are entirely
framework-owned. Unlike AGENTS.md, which carries a generated section plus
whatever the user appended, and unlike `settings.json`, which carries user
permissions, a skill file has no user-edited region at all. Overwriting one
cannot lose anything. That property is what makes the narrow fix possible, and
it is worth preserving: do not add a user-editable region to a skill file.

### The stamp must not claim a version
The stamp records `framework_version: null` and an empty file list. Stamping
the current version instead would be actively harmful, and in the obvious way:
`/update`'s preflight reads the recorded version, sees it match the reference,
and concludes the project is current, while the project still holds the old
AGENTS.md and phase docs. The empty file list matters for the same reason.
Retirement is "in the recorded list, absent from the reference", so a current
list makes that set empty and nothing is ever retired. Null is the honest
value and is the case the preflight already handles: profile, harness, and
project name are recorded so the agent need not re-detect them, and the
version stays unknown so retirement falls to the orphan test, deliberately.

### The orphan test had gone stale
With an empty file list the orphan test is the only thing that can retire
anything, and v5.17 had broken it without anyone noticing. It asks the
generator's history whether a path was ever emitted:

    git -C "$LLM_AGENT_HOME" log --oneline -S'<basename>' -- init_agent.py

That path filter was right while `init_agent.py` was the whole product. After
the restructure the write calls live in `agentgen/` and the content under
`templates/`, so a file introduced after 5.17 leaves no trace in
`init_agent.py`. The test would report "no commits", conclude the user wrote
the file, and leave it forever. The filter now covers all three paths. The
failure was latent rather than live, because every path that exists today was
named in `init_agent.py` back when it was added, and it would have started
biting on the first file retired after 5.17.

### What this deliberately does not do
No three-way merge, no deterministic classification plan, no second update
implementation in Python. The bootstrap is a delivery mechanism and stops
there. Making `/update` itself smarter, by rendering the reference for the
version a project was built at so "did the user edit this file" becomes a hash
comparison rather than a judgment call, is a real improvement and is measured
in the notes for a later revision. It is not needed for the mechanism to work,
and it is better designed after watching `/update` run against real legacy
scaffolds than before.

## 29. Review gates sized to the change (2026-08-26, v5.20)

Owner report from daily use: reviews fire too often and run too deep, and
small changes feel like they pay a gate built for large ones. Reading the
templates confirms it. Right-sizing existed only at the *entrance* to the
pipeline (does this need a ticket / a spec?) and never at the *gate*. Once
inside, review cost was constant.

### Three separate defects

**The small profile reviewed changes it had just exempted from planning.**
Right-sizing says a one-sentence, 1-2 file change needs no spec: make it,
note it, commit. The always-on protocol then said "before declaring a change
done, have the full diff reviewed in a fresh context against the acceptance
criteria" with no scope qualifier. A right-sized change has neither a spec nor
acceptance criteria, so the rule demanded a `reviewer` sub-agent for a diff
whose whole content fits in a sentence. The two rules sat eleven lines apart
in the same always-loaded document. This is the main driver of the "too often"
report: it hits the most common daily change, the small one.

**The large profile's trivial path shrank one gate of two.** Phase 2 shrinks
the plan-review gate to a one-line sign-off for a trivial ticket, and
AGENTS.md advertised the path as "one task file, one review gate". Phase 3's
ticket review gate carried no trivial clause and closed with "Never silently
skip the gate", so a trivial ticket still paid a full sub-agent diff review.
The two phase docs disagreed and the entry document described a third
behavior. Both gates now size down together on the trivial path.

**Review depth did not scale.** The `reviewer` brief ran one fixed checklist
regardless of the artifact, including toolchain-version and
registry-availability reasoning for build config even when the diff touched no
build config, and both gates cross-checked every gotcha in `notes.md`
unconditionally. The packaging reasoning is now conditioned on the diff
actually touching build/CI/packaging (which is what it was written for, per
§18), as is the gotcha sweep, and the brief opens by telling the reviewer to
match depth to the artifact and that report length is not evidence of rigor.

### The rule
Sizing a gate down is a judgment call the agent may make; skipping one
silently is not. Every gate keeps a floor, an inline check against the
acceptance criteria, so "small" buys a cheaper instrument rather than no
instrument. The fresh-context requirement is what gets spent, and it is spent
where a producing context is actually likely to grade its own work wrong: a
multi-task diff, or one with blast radius beyond the files it names.

### What this does not change
The gates themselves stay. §12's finding stands, a producing context grades
its own work generously, and fresh-context review is also what makes
cheap-execution modes safe (§9, §23). The change is proportionality, not
removal, and it does not touch the plan-review gate for non-trivial tickets:
a weak plan still poisons every downstream task, and that is the gate with the
highest leverage per token in the whole framework.
