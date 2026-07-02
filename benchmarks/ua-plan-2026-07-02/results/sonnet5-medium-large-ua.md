# Benchmark Results: sonnet5-medium-large-ua

## Configuration
| Field | Value |
|---|---|
| Run ID | sonnet5-medium-large-ua |
| Profile | large |
| Model | claude-sonnet-5 |
| Effort | medium |
| Task | UA-1 add Angular framework detection |
| Scope | explore + plan only (no implement/build) |
| Start | 2026-07-02T14:00:27 |
| End | 2026-07-02T14:13:53 |
| Duration | 806s (~13m 26s) |

## KB nodes produced (list + one-line each)
- `architecture/overview.md` (hot) — Monorepo layout (`understand-anything-plugin/` holds all source: core/dashboard/src/skills/agents; `homepage/` is unrelated), tree-sitter+LLM hybrid, 5+2 agent pipeline, data flow, entry points. Records host commit SHA for incremental re-init.
- `infra/build.md` (cold) — pnpm workspace (3 packages), root scripts (`build`=`pnpm -r build`, `test`=`vitest run` which **excludes** `packages/core`), core's separate `--filter` build/test commands, tsconfig, tree-sitter/dashboard-subpath gotchas.
- `conventions/code-style.md` (hot) — ESLint flat-config rules (unused-vars `^_` exemption, no-explicit-any off in tests), TS strict/ESM `.js`-extension-from-`.ts` convention, and the framework/language config-object pattern (file-per-id, `satisfies FrameworkConfig`, three-place registration) with a worked example.
- `domain/glossary.md` (hot) — 9 terms: knowledge graph, `FrameworkConfig`/`LanguageConfig`, the two registries, `detectionKeywords`, `layerHints`, `promptSnippetPath`, `importMap`, guided tour.
- `.ai/notes.md` — monorepo-layout gotcha (core excluded from root vitest), the registry pattern's "three places to update" rule, the `promptSnippetPath` cross-directory gotcha (resolves against `skills/understand/frameworks/`, not the core package), test-count-bump gotcha.

`conventions/testing.md`, `conventions/git-workflow.md`, `infra/ci-cd.md` were left as scaffolded placeholders (out of medium-effort scope; not needed for UA-1).

## AGENTS.md project-context (full generated section)
```
**Understand Anything** — Claude Code (+ multi-platform) plugin. A
multi-agent pipeline + tree-sitter analyzes a target codebase, builds a
knowledge graph (`.understand-anything/knowledge-graph.json` in the
*analyzed* project), and serves it via an interactive React dashboard.
Tree-sitter (WASM, `web-tree-sitter`) does deterministic structural
extraction (imports/exports/defs); LLM agents add semantic summaries,
tags, layers, domain mapping, tours. Host commit at last explore:
`54754a6f97051d1d76c8758353d8ea41afe502a6`.

**Tech stack**: TypeScript (strict, ESM, `target: ES2022`), pnpm workspace
monorepo, zod schemas, vitest, ESLint 9 flat config
(`typescript-eslint` recommended), React + React Flow + Zustand + Tailwind
v4 (dashboard).

**Layout**: source lives under `understand-anything-plugin/` (not repo
root). Packages: `packages/core` (`@understand-anything/core` — analysis
engine: types/schema, tree-sitter plugin+parsers, language/framework
registries, graph builder, search, staleness/fingerprinting; subpath
exports `.`/`./search`/`./types`/`./schema`/`./languages` to keep the
dashboard Node-free), `packages/dashboard` (React UI), `src/` (skill TS
source), `skills/` (skill defs incl. per-framework prompt snippets at
`skills/understand/frameworks/<id>.md`), `agents/` (pipeline agent defs).
`homepage/` (Astro) is a separate, unrelated workspace package.

**Build/test/lint**:
- `pnpm install`; `pnpm build` = `pnpm -r build` (each package's own
  `tsc`); `pnpm lint` = `eslint .`.
- `pnpm test` = `vitest run` at root — **excludes**
  `packages/core/**`. Core has its OWN `vitest.config.ts`; test it via
  `pnpm --filter @understand-anything/core test` (build:
  `pnpm --filter @understand-anything/core build`).
- `pnpm dev:dashboard` — dashboard dev server.

**Top conventions**:
- Language/framework config-object pattern (see
  `conventions/code-style`): one file per id under
  `packages/core/src/languages/frameworks/`, `export const
  <id>Config = {...} satisfies FrameworkConfig`, registered in
  `frameworks/index.ts` (import + `builtinFrameworkConfigs` array +
  named re-export) and validated by zod at `registry.register()`.
  `detectionKeywords` match case-insensitively as raw-text substrings of
  `manifestFiles` content (no parsing).
- Import specifiers use explicit `.js` extensions even from `.ts` files
  (ESM/bundler convention).
- `no-unused-vars` errors except `^_`-prefixed; `no-explicit-any` is off
  in test files.
- Vitest `describe/it/expect`; registry tests import configs directly
  from their source module, not just the barrel.

**Glossary** (full: `domain/glossary`): knowledge graph, `FrameworkConfig`
/ `LanguageConfig`, `FrameworkRegistry` / `LanguageRegistry`,
`detectionKeywords`, `layerHints`, `promptSnippetPath`, `importMap`,
guided tour.

**Module map**: see `architecture/overview` (cold: full data-flow +
entry-point list).
```

## Ticket (full content)
See `.ai/tickets/UA-1-add-angular-framework-detection.md` at creation time
(moved into `tasks/UA-1/ticket.md` by the plan phase — full final content
reproduced under "Plan produced" below since the inbox copy was deleted per
the plan skill's workflow).

## Plan produced (full content)

### `.ai/knowledgebase/tasks/UA-1/ticket.md`
```markdown
---
id: UA-1
title: Add Angular framework detection to core
status: planned
created: 2026-07-02
---

Add a `FrameworkConfig` for Angular to `@understand-anything/core` so that
Angular projects are detected the way React/Vue/Next.js already are.
Angular is a TypeScript/JavaScript framework detected via `package.json`
dependencies (`@angular/core`). Follow the existing framework-config
pattern (see `packages/core/src/languages/frameworks/react.ts`,
`vue.ts`).

## Q&A (Planning)

No human available (autonomous run). Resolved from code evidence in
`packages/core/src/languages/frameworks/*.ts`,
`packages/core/src/languages/types.ts` (`FrameworkConfigSchema`), and
`packages/core/src/__tests__/framework-registry.test.ts`. Recorded as
numbered assumptions:

1. **`id` / `displayName`**: `id: "angular"`, `displayName: "Angular"` —
   matches the lowercase-id / proper-name convention used by every
   existing config (`react`/`React`, `vue`/`Vue`, `gin`/`Gin`).
2. **`languages`**: `["typescript", "javascript"]` — Angular apps are
   almost universally TypeScript, but the registry keys frameworks by
   language id and other TS/JS frameworks (react, vue, nextjs, express)
   all list both; Angular CLI does support a (legacy/uncommon)
   JavaScript mode, so including both avoids a false negative rather
   than a false positive.
3. **`detectionKeywords`**: `["@angular/core", "@angular/cli"]` —
   `@angular/core` is present in `dependencies` of every Angular
   application (the framework's runtime package) and is the strongest,
   least ambiguous signal (unlike a bare `"angular"` keyword, which
   would also match legacy AngularJS 1.x (`angular` npm package) and
   many unrelated `angular-*` utility packages). `@angular/cli` is
   included as a secondary keyword to also catch workspace/tooling-only
   manifests. Detection matching is a raw case-insensitive substring
   check (`FrameworkRegistry.detectFrameworks`), so no JSON parsing or
   dependency-field targeting is needed — consistent with how
   `reactConfig` uses `"react"`/`"react-dom"`/`"@types/react"`.
4. **`manifestFiles`**: `["package.json"]` — same manifest as every
   other JS/TS framework config (react, vue, nextjs, express); Angular's
   `angular.json` is a build/workspace config, not a dependency
   manifest, and is not used as a `manifestFiles` entry anywhere in the
   existing pattern.
5. **`promptSnippetPath`**: `"./frameworks/angular.md"` — path-string
   convention only (`./frameworks/<id>.md`, resolved against
   `understand-anything-plugin/skills/understand/frameworks/` at
   runtime). `FrameworkConfigSchema` only requires a non-empty string;
   it does not validate file existence, and the registry/unit tests
   never read the file. Creating the actual
   `skills/understand/frameworks/angular.md` prompt snippet is **out of
   scope** for this ticket (the ticket's affected files are core-only);
   flagged here so a maintainer can follow up before the config is used
   in a real `/understand` run.
6. **`entryPoints`**: `["src/main.ts", "src/app/app.module.ts", "src/app/app.component.ts"]`
   — `src/main.ts` is Angular CLI's universal bootstrap file; `app.module.ts`
   is the root NgModule for classic (module-based) Angular apps;
   `app.component.ts` is the root component, present in both classic and
   modern standalone-component apps. (Angular >=17's standalone
   `app.config.ts` bootstrap style was considered but omitted to keep the
   list at the same length as the other configs' 3-4 entries; a
   maintainer may want to add it later.)
7. **`layerHints`**: `{ components: "ui", services: "service", guards:
   "middleware", pipes: "utility", directives: "ui", modules: "config" }`
   — mirrors Angular CLI's generated folder/artifact vocabulary
   (`ng generate component/service/guard/pipe/directive/module`), mapped
   to the same layer-id vocabulary already used by `reactConfig` /
   `nextjsConfig` / `vueConfig` (`ui`, `service`, `api`, `data`,
   `middleware`, `config`, `utility`).
8. **Test coverage**: add one `detectFrameworks` test asserting Angular
   is detected from a `package.json` containing `@angular/core` (mirrors
   the existing "detects React from package.json" test), and bump the
   `createDefault()` "registers all N built-in framework configs" count
   from 10 to 11 in the same test file, since `angularConfig` is added
   to `builtinFrameworkConfigs`.
9. **(post plan-review addition)** Added a third, dedicated test
   asserting `getForLanguage("typescript")` / `getForLanguage("javascript")`
   both include `id === "angular"` — the plan-review sub-agent flagged
   that the original two tests never actually exercised this
   (acceptance criterion 5 would have been unverified otherwise; the
   existing cross-language tests only ever check `react`'s id).
```

### `.ai/knowledgebase/tasks/UA-1/plan.md`
```markdown
---
ticket: UA-1
status: planned
read-first: .ai/agent/phases/implementation.md
kb-commit: bbc7bd52b078430f7cb1202a39a64506ab4f6e10
updated: 2026-07-02
---

# Plan: UA-1 — Add Angular framework detection to core

Trivial-ish, single-task ticket confined to one package
(`@understand-anything/core`), following an existing, well-established
pattern (9 other framework configs already present). One task file
covers the whole ticket.

| # | Task file | Depends on | Parallel | Status |
|---|---|---|---|---|
| 01 | `01-angular-framework-config.md` | — | no | planned |

Read `ticket.md` for the full description and the numbered autonomous
assumptions (Q&A) this plan was built against.
```

### `.ai/knowledgebase/tasks/UA-1/01-angular-framework-config.md`
```markdown
---
status: planned
depends: []
parallel: no
---

# Task 01: Add Angular FrameworkConfig to core

## Goal
Register Angular as a detectable framework in `@understand-anything/core`,
following the existing per-framework config-object pattern (see
`conventions/code-style` node, "Config-object pattern" section), so
Angular projects are detected via `FrameworkRegistry.detectFrameworks()`
the same way React/Vue/Next.js already are.

## Pre-bound KB nodes
- `architecture/overview` — module map / where `packages/core` lives.
- `conventions/code-style` — the config-object pattern (file-per-id,
  `satisfies FrameworkConfig`, three-place registration, detection
  semantics) this task must follow exactly.

## Acceptance criteria
1. `pnpm --filter @understand-anything/core build` (`tsc`) succeeds with
   no new type errors — the new file must satisfy `FrameworkConfig`
   (validated by `FrameworkConfigSchema` at `registry.register()` /
   `FrameworkRegistry.createDefault()`).
2. `pnpm --filter @understand-anything/core test` (vitest) passes,
   including the new/updated tests below.
3. `pnpm lint` (root ESLint) reports no new violations in the touched
   files.
4. `angularConfig` is exported from
   `packages/core/src/languages/frameworks/index.ts`, is present in the
   `builtinFrameworkConfigs` array, and is therefore returned by
   `FrameworkRegistry.createDefault().getAllFrameworks()`.
5. `FrameworkRegistry.createDefault().getForLanguage("typescript")` and
   `.getForLanguage("javascript")` both include an entry with
   `id === "angular"`.
6. `FrameworkRegistry.createDefault().detectFrameworks({ "package.json":
   '{"dependencies":{"@angular/core":"^17.0.0"}}' })` returns an array
   containing the Angular config (`id === "angular"`), matching the
   existing case-insensitive substring detection semantics — no new
   detection logic needed in `framework-registry.ts`.
7. The existing `createDefault` "registers all N built-in framework
   configs" test is updated to the new total (10 -> 11) and still
   passes.

## Affected files

### NEW: `understand-anything-plugin/packages/core/src/languages/frameworks/angular.ts`
Exact content to add (mirrors `react.ts` / `vue.ts` shape; see
`ticket.md` Q&A #1-7 for the rationale behind each field):

\`\`\`ts
import type { FrameworkConfig } from "../types.js";

export const angularConfig = {
  id: "angular",
  displayName: "Angular",
  languages: ["typescript", "javascript"],
  detectionKeywords: ["@angular/core", "@angular/cli"],
  manifestFiles: ["package.json"],
  promptSnippetPath: "./frameworks/angular.md",
  entryPoints: ["src/main.ts", "src/app/app.module.ts", "src/app/app.component.ts"],
  layerHints: {
    components: "ui",
    services: "service",
    guards: "middleware",
    pipes: "utility",
    directives: "ui",
    modules: "config",
  },
} satisfies FrameworkConfig;
\`\`\`

### EDIT: `understand-anything-plugin/packages/core/src/languages/frameworks/index.ts`
Add the import, array entry, and named re-export, keeping the existing
alphabetical-ish grouping style (append at the end, consistent with how
`ginConfig` was appended last):

\`\`\`ts
import type { FrameworkConfig } from "../types.js";

import { djangoConfig } from "./django.js";
import { fastapiConfig } from "./fastapi.js";
import { flaskConfig } from "./flask.js";
import { reactConfig } from "./react.js";
import { nextjsConfig } from "./nextjs.js";
import { expressConfig } from "./express.js";
import { vueConfig } from "./vue.js";
import { springConfig } from "./spring.js";
import { railsConfig } from "./rails.js";
import { ginConfig } from "./gin.js";
import { angularConfig } from "./angular.js";

export const builtinFrameworkConfigs: FrameworkConfig[] = [
  djangoConfig,
  fastapiConfig,
  flaskConfig,
  reactConfig,
  nextjsConfig,
  expressConfig,
  vueConfig,
  springConfig,
  railsConfig,
  ginConfig,
  angularConfig,
];

export {
  djangoConfig,
  fastapiConfig,
  flaskConfig,
  reactConfig,
  nextjsConfig,
  expressConfig,
  vueConfig,
  springConfig,
  railsConfig,
  ginConfig,
  angularConfig,
};
\`\`\`

### EDIT: `understand-anything-plugin/packages/core/src/__tests__/framework-registry.test.ts`
Two changes:

1. Import `angularConfig` alongside the existing `djangoConfig` /
   `reactConfig` imports:
   \`\`\`ts
   import { angularConfig } from "../languages/frameworks/angular.js";
   \`\`\`
2. Add a detection test next to "detects React from package.json"
   (inside the `describe("detectFrameworks", ...)` block):
   \`\`\`ts
   it("detects Angular from package.json", () => {
     const registry = new FrameworkRegistry();
     registry.register(angularConfig);
     const detected = registry.detectFrameworks({
       "package.json": '{"dependencies": {"@angular/core": "^17.0.0", "@angular/cli": "^17.0.0"}}',
     });
     expect(detected).toHaveLength(1);
     expect(detected[0].id).toBe("angular");
   });
   \`\`\`
3. Update the `createDefault` count assertion:
   \`\`\`ts
   it("registers all 11 built-in framework configs", () => {
     const registry = FrameworkRegistry.createDefault();
     expect(registry.getAllFrameworks()).toHaveLength(11);
   });
   \`\`\`
   (rename the `it` title from "10" to "11" and change the expected
   length from `10` to `11`).
4. Add a dedicated assertion for acceptance criterion 5 (language
   lookup), inside the `describe("createDefault", ...)` block, next to
   "includes frameworks for multiple languages" — the existing
   cross-language tests only ever check `react`'s id, so criterion 5
   needs its own test rather than riding on an existing one:
   \`\`\`ts
   it("includes Angular for both typescript and javascript", () => {
     const registry = FrameworkRegistry.createDefault();
     expect(registry.getForLanguage("typescript").some((f) => f.id === "angular")).toBe(true);
     expect(registry.getForLanguage("javascript").some((f) => f.id === "angular")).toBe(true);
   });
   \`\`\`

## Out of scope (do not do in this task)
- Creating `understand-anything-plugin/skills/understand/frameworks/angular.md`
  (the LLM prompt snippet referenced by `promptSnippetPath`). Not
  required for the schema, registry, or tests to pass (see ticket Q&A
  #5); left for a follow-up ticket since the LLM-facing prompt content
  is a different kind of authoring task than the structural config.
- Any change to `FrameworkRegistry` / `FrameworkConfigSchema` detection
  logic — Angular fits the existing manifest-keyword-substring mechanism
  without modification.

## Test skeleton (full updated relevant section for reference)
See "EDIT" block above for the exact test additions (3 total: a
`detectFrameworks` Angular test, the updated 10->11 count test, and a
dedicated `getForLanguage` Angular test covering acceptance criterion
5); no other test files need changes.

## Plan-review note
Reviewed by a fresh-context `general-purpose` sub-agent against this
task file, `ticket.md`, `plan.md`, and the real source
(`types.ts`, `react.ts`, `vue.ts`, `gin.ts`, `frameworks/index.ts`,
`framework-registry.test.ts`). Confirmed: the `angular.ts` config
satisfies `FrameworkConfigSchema`; the `frameworks/index.ts` edit
applies cleanly against the real current file; the test-file edit's
claimed current state ("registers all 10 built-in framework configs",
`toHaveLength(10)`) matches the real file exactly. One gap was found
and fixed: acceptance criterion 5 (per-language lookup) had no
dedicated test — added test item 4 above to close it.
```

## .ai commit history
```
fcab645 plan: UA-1
bbc7bd5 add-ticket: UA-1
1ae2fd0 explore: glossary, notes, manifest/index, AGENTS.md project-context
8ab41ae explore: conventions/code-style
4697066 explore: infra/build
a0da5c1 explore: architecture/overview
50d7b90 init: scaffold KB + phase docs (understand-anything)
```

## Plan-review outcome
Spawned a fresh-context `general-purpose` sub-agent (the `reviewer` agent
persona/checklist applied manually since the harness's dedicated
`reviewer` subagent type wasn't directly invokable by name here) with only
the three plan artifacts plus instructions to independently re-read the
real source files (`types.ts`, `react.ts`, `vue.ts`, `gin.ts`,
`frameworks/index.ts`, `framework-registry.test.ts`) to verify every
factual claim in the plan against ground truth, not just internal
consistency.

Findings: the proposed `angular.ts` correctly satisfies
`FrameworkConfigSchema`; the `frameworks/index.ts` edit is byte-for-byte
consistent with the real current file and appends cleanly; the test-file
edit's claimed "current state" (`"registers all 10 built-in framework
configs"`, `toHaveLength(10)`) matches the real file exactly, so the
10->11 bump is correct. One genuine gap: acceptance criterion 5
(`getForLanguage` must return Angular for both `typescript` and
`javascript`) had no dedicated test in the original plan — it would have
"passed" only because no test actually checked it. Fixed by adding a
4th test item to task 01 (`"includes Angular for both typescript and
javascript"`) and cross-referencing it in the ticket's Q&A as assumption
#9. Re-verified the fix closes the gap (the new test call structure
matches the registry's real `getForLanguage` signature and the existing
"cross-language" test's style). No other correctness, scope, or
self-containment issues were found.

## Observations
The large-profile framework held up well for a scoped, single-package
change: probe.py's module map correctly pointed at
`packages/core/src/languages/` as the highest-value area, and reading
5-6 real framework configs (react/vue/nextjs/gin/django) plus the schema
and test file was enough to derive an exact, schema-valid, convention-
matching `angular.ts` without guesswork. The one thing that needed real
investigation rather than pattern-matching was `promptSnippetPath`
resolution — it points outside the core package entirely (into
`skills/understand/frameworks/`), which isn't obvious from the core
package alone and would have produced an incomplete plan if skipped; this
is now recorded both in `.ai/notes.md` and as ticket assumption #5. The
plan-review gate caught one real, non-cosmetic gap (an untested
acceptance criterion) despite the plan otherwise being highly accurate
against ground truth, validating that an independent re-read of source
files (not just internal-consistency checking) is worth the sub-agent
call. The produced `angular.ts` block is complete and directly usable:
it mirrors `react.ts`'s shape field-for-field, all values are grounded in
either the real Angular CLI/ecosystem convention or an explicit numbered
assumption, and it passes the schema's structural constraints (non-empty
id/displayName, non-empty language/keyword/manifest arrays, optional
entryPoints/layerHints correctly typed).
