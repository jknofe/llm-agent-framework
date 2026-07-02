# Benchmark Report: Sonnet 5 × medium/high (Understand-Anything, explore + plan only)

**Date:** 2026-07-02
**Runbook:** [../satty-deb-2026-07-01/runbook.md](../satty-deb-2026-07-01/runbook.md), adapted
(see *Deviations from the runbook* below).
**Target:** [Understand-Anything](https://github.com/Egonex-AI/Understand-Anything.git) —
an open-source codebase-understanding tool (TypeScript/pnpm monorepo, tree-sitter + LLM,
~39k LOC of TS/TSX). **Large** profile.
**Task (UA-1):** add Angular detection to `@understand-anything/core`'s framework registry —
a new `FrameworkConfig` plus its three-place registration and a registry test. Additive,
single-package, verifiable against `FrameworkConfigSchema` and the existing
`framework-registry.test.ts` pattern. This is the TS-ecosystem analog of the Satty
"add packaging" task (self-contained, one domain, a couple of files).
**Matrix:** claude-sonnet-5 × {medium, high} × large profile (2 cells).
**Framework state:** current `main` working tree (v5.6).
Raw per-cell results: [results/](results/).

## Deviations from the runbook

This run intentionally departs from the reference runbook on three axes; everything else
(cold-context agent per cell, autonomous Q&A→assumptions, phase-doc-first, review gate)
is unchanged.

1. **New target + task.** Understand-Anything instead of Satty; "add Angular framework
   config" instead of "add Debian packaging." The task was chosen for the same shape:
   additive, one package, schema/test-verifiable.
2. **Large profile** (the Satty small/large split; here both cells run large, since the
   target is ~39k LOC and the ticket→plan→implement pipeline is what large exercises).
3. **Scope truncated at PLAN.** Per the request, each cell ran `init → explore →
   add-ticket → plan (+ plan-review gate)` and then **stopped** — no implement, no build,
   no Docker. There is therefore no PASS/FAIL Docker column; correctness here means
   *"is the generated plan schema-valid, factually grounded, and implementable as written?"*,
   verified statically by the orchestrator against the real repo (see *Verification*).

## Results

| Run | Model | Effort | Duration | Sub-tokens | KB nodes filled | Plan task files | `.ai` commits |
|---|---|---|---|---|---|---|---|
| sonnet5-medium-large-ua | claude-sonnet-5 | medium | 806 s (~13.5 m) | ~110k | 4 (+3 left as stubs) | 1 | 7 (per-node explore commits) |
| sonnet5-high-large-ua | claude-sonnet-5 | high | 1287 s (~21.5 m) | ~161k | 8 (all) | 2 (+ `kb-delta.yaml`) | 4 (batched explore commit) |

Both cells: clean `.ai` audit trail (`init → explore → add-ticket → plan`), all writes
confined to `.ai/` (no target source modified), a schema-valid `angular.ts` block, and a
plan-review gate run via the documented general-purpose fallback (the named `reviewer`
subagent type is unreachable from inside a subagent — a known, documented limitation, hit
in both cells as expected).

## Verification (orchestrator, against the real repo)

Both plans were checked against ground truth in `packages/core/src/languages/`:

- **Schema.** `FrameworkConfigSchema` (zod): `id`/`displayName` `min(1)`, `languages`
  `array(string.min(1)).min(1)`, `detectionKeywords`/`manifestFiles` `min(1)`,
  `promptSnippetPath` `min(1)`, `entryPoints` optional array, `layerHints` optional
  `record(string,string)`. **Both** planned blocks satisfy every constraint.
- **The count trap.** `framework-registry.test.ts:109-111` hardcodes
  `"registers all 10 built-in framework configs"` / `toHaveLength(10)`. **Both** cells
  independently discovered this and folded the 10→11 bump into the plan as mandatory
  (it is CI-breaking otherwise — the `Test core` step). High cited the exact line.
- **Cross-language tests** (`:116-120`) use `.toBeGreaterThanOrEqual`, so both language
  choices below keep them green.

Both plans are implementable as written. Neither was implemented (scope).

## Plan divergence — the generated `angular.ts` (the core artifact)

| Field | medium | high |
|---|---|---|
| `languages` | `["typescript","javascript"]` — **follows the surrounding convention** (react/vue/nextjs/express all list both) | `["typescript"]` — **evidence-based departure**: "Angular CLI scaffolds `.ts`; no first-class JS Angular starter", stated as assumption #1 |
| `detectionKeywords` | `["@angular/core","@angular/cli"]` (2) | `["@angular/core","@angular/cli","@angular/common"]` (3) |
| `entryPoints` | `main.ts`, `app.module.ts`, `app.component.ts` | `main.ts`, `app.config.ts` (standalone, Angular 17+), `app.module.ts` — more version-current |
| `layerHints` | 6 keys (components/services/guards/pipes/directives/modules) | 7 keys (+ `interceptors`) |
| Keyword-collision check | not explicit | explicit, both directions, vs. all 10 existing frameworks |

Neither `languages` choice is wrong: high's is more *accurate* to Angular reality; medium's
is more *consistent* with the file's neighbours. The interesting part is that high **noticed
the convention and chose to break it with a recorded justification**, whereas medium
followed the convention without flagging the tension — the same "assumption quality is the
model/effort axis" signal the Satty runs found, reproduced here on a judgment call rather
than a policy detail.

## Explore divergence (large-profile KB)

- **medium** filled 4 nodes (`architecture/overview`, `infra/build`, `conventions/code-style`,
  `domain/glossary`) and left `testing`/`git-workflow`/`ci-cd` as scaffolded stubs —
  explicitly scoped out as unneeded for UA-1. Committed one node per commit.
- **high** filled all 8 (added `infra/ci-cd`, `conventions/testing`, `conventions/git-workflow`)
  and produced a denser project-context (React 19/Vite/Tailwind v4 dashboard stack, subpath
  export rules, the "no `model:` in agent frontmatter" gotcha lifted from the repo's own
  CLAUDE.md). Batched explore into one commit.

Both surfaced the **two load-bearing non-obvious findings** a shallow read would miss, and
both let them reshape the plan:
1. `promptSnippetPath` / `layerHints` are **declarative-only today** — no consumer in
   `packages/core/src`; the `.md` snippet is resolved by `skills/understand/SKILL.md`
   relative to *its own* directory, skipped silently if absent.
2. the hardcoded `toHaveLength(10)` count assertion.

## Plan-phase & review-gate divergence

- **medium** produced **1** task file and relied on its **review gate to recover rigor**:
  the fresh-context reviewer found a *real* gap — acceptance criterion 5 (per-language
  lookup) had no dedicated test — and medium added a `getForLanguage("typescript"/"javascript")`
  test (consistent with its dual-language choice) plus assumption #9.
- **high** produced **2** task files (mandatory core config + an *optional* `02` for the
  `.md` prompt snippet, split out precisely because explore proved it's non-blocking) and a
  `kb-delta.yaml`. Its review gate found **only a prose off-by-one** ("9 other frameworks"
  vs. 10 listed) — no correctness gap, because high had already front-loaded the
  getForLanguage reasoning (and, given its TS-only choice, correctly decided no JS assertion
  was warranted).

So the effort tier moved *where the rigor lived*: at medium the review gate did the catching;
at high the planning phase itself was thorough enough that the gate only polished prose.

## Cross-run conclusions (consistent with the Satty runs)

- **Effort remains the dominant axis, and it shows up as thoroughness, not correctness.**
  Both cells produced a schema-valid, implementable plan on the first pass. High spent ~1.6×
  the time and ~1.5× the tokens to get: full KB coverage, a second (optional) task,
  an explicit collision check, and a more version-current config — none of which medium got
  *wrong*, it just didn't reach for them.
- **Assumption quality is the clearest model/effort gain** — reproduced from the Satty runs,
  here on a genuine judgment call (`languages`), where high knowingly departed from local
  convention with a cited rationale.
- **The review gate's rigor tracks effort.** Medium's gate caught a real untested-criterion
  gap; high's plan left the gate almost nothing to do. The gate earns its cost at medium
  more than at high on this task.
- **Framework mechanics held on a new stack and a new profile.** `probe.py`'s inventory
  correctly pointed both agents at `packages/core/src/languages/`; the phase-doc-first
  workflow scoped explore and plan cleanly; the `reviewer`-subagent-unreachable fallback
  fired and worked in both cells, exactly as documented.

## Verdict

2/2 produced schema-valid, factually-grounded, implementable plans with a clean `.ai`
trail — with no source touched, as scoped. High delivered the more complete package
(full KB, optional snippet task, collision proof, more current defaults) and a more
defensible `languages` decision; medium reached an equally correct core artifact faster
and leaned on its review gate to close its one real gap. The effort tier is again the
dominant quality axis, and it manifests as breadth-of-consideration and assumption quality
rather than as first-pass correctness — the same shape the Satty runs reported, now
confirmed on a TypeScript target, the large profile, and an explore+plan-only scope.
