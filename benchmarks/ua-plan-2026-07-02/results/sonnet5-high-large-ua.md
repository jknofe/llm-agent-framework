# Benchmark Results: sonnet5-high-large-ua

## Configuration
| Field | Value |
|---|---|
| Run ID | sonnet5-high-large-ua |
| Profile | large |
| Model | claude-sonnet-5 |
| Effort | high |
| Task | UA-1 add Angular framework detection |
| Scope | explore + plan only (no implement/build) |
| Start | 2026-07-02T14:00:55 |
| End | 2026-07-02T14:22:22 |
| Duration | 1287s (~21m 27s) |

## KB nodes produced (list + one-line each)

- `.ai/knowledgebase/architecture/overview.md` (hot) — tree-sitter+LLM hybrid, multi-agent `/understand` pipeline, module map of core/dashboard/skill/skills/agents/tests/homepage, entry points.
- `.ai/knowledgebase/infra/build.md` (cold) — pnpm workspace layout, root scripts (`prepare`/`build`/`test`/`lint`/`dev:dashboard`), per-package build commands, local-plugin-cache testing gotcha, 5-file version-bump rule.
- `.ai/knowledgebase/infra/ci-cd.md` (cold) — `.github/workflows/ci.yml` step-by-step (install→lint→build core→build skill→test core→test root), concurrency cancel-in-progress, deploy-homepage workflow noted as unrelated.
- `.ai/knowledgebase/conventions/code-style.md` (hot) — TS strict, `.js` import-extension convention, `satisfies FrameworkConfig`/`LanguageConfig` pattern, zod-schema-enforced config validation, ESLint v9 flat-config rules.
- `.ai/knowledgebase/conventions/testing.md` (cold) — the two-vitest-config split (root excludes `packages/core/**`; core has its own isolated run), test layout, exact-count assertion gotcha for registry `createDefault()` tests.
- `.ai/knowledgebase/domain/glossary.md` (hot) — knowledge graph, Layer (two independent mechanisms), LanguageConfig/FrameworkConfig, `detectionKeywords` matching semantics, `promptSnippetPath`/`layerHints` non-consumption finding, intermediate files, incremental update.
- `.ai/knowledgebase/conventions/git-workflow.md` (cold) — branch naming, commit prefixes, PR checklist, CI merge gate.
- `.ai/notes.md` — monorepo layout corrections (no separate "analyzer" package), full registry-pattern writeup, the exact-count test trap, the `detectFrameworks` substring-match semantics, the `layerHints`/`promptSnippetPath` non-consumption evidence trail, tree-sitter/dashboard-import/agent-model gotchas from the repo's own CLAUDE.md, test-scoping gotcha.

## AGENTS.md project-context (full generated section)

```
**Understand Anything** — a Claude Code Plugin (also usable from Codex,
Cursor, Copilot, Gemini CLI, etc.) that runs a multi-agent pipeline
(tree-sitter static analysis + LLM semantic pass) to build a knowledge graph
of a target codebase and serve it via an interactive React dashboard.

**Tech stack**: TypeScript strict, pnpm workspaces monorepo (Node >=22, pnpm
>=10), ESM ("type": "module") everywhere, Zod v4 for structural config
validation, `web-tree-sitter` (WASM, not native bindings) for parsing,
Vitest for tests, ESLint v9 flat config for lint; dashboard: React 19 + Vite
+ TailwindCSS v4 + `@xyflow/react` + Zustand + Dagre/ELK + `graphology`.

**Build/test/lint**:
- `pnpm install` (runs `prepare` → builds core)
- `pnpm --filter @understand-anything/core build|test` — core's own isolated
  build/vitest run (own `vitest.config.ts`, **excluded** from root `pnpm test`)
- `pnpm --filter @understand-anything/skill build` — plugin skill pkg
- `pnpm test` (root `vitest.config.ts`) — `tests/**`, plugin `src/**`, dashboard `**`
- `pnpm --filter @understand-anything/dashboard build` — `tsc -b && vite build`
- `pnpm dev:dashboard` / `pnpm lint` (`eslint .`) / `pnpm build` (`pnpm -r build`)
- CI (`.github/workflows/ci.yml`, PRs + push to main): install → lint →
  build core → build skill → test core → test (root).

**Module map**:
- `understand-anything-plugin/packages/core/src/` — shared analysis engine:
  `types.ts`/`schema.ts` (graph types + zod schema/validate/sanitize),
  `analyzer/` (graph-builder, llm-analyzer, layer-detector, tour-generator,
  language-lesson — a subdir of core, not a separate package), `plugins/`
  (tree-sitter-plugin, extractors/, non-code parsers/, registry, discovery),
  `languages/` (LanguageRegistry + FrameworkRegistry, see cold node
  `architecture/overview`), `persistence/`, `search.ts`, `fingerprint.ts`,
  `staleness.ts`. Subpath exports: `.`, `./search`, `./types`, `./schema`,
  `./languages` (last 4 browser-safe; dashboard must only import these).
- `understand-anything-plugin/packages/dashboard/src/` — React 19 dashboard
  (`App.tsx`, `store.ts` Zustand, `components/`, `hooks/`, `contexts/`).
- `understand-anything-plugin/src/` — `/understand-chat`, `/understand-diff`,
  `/understand-explain`, `/understand-onboard` skill TS source.
- `understand-anything-plugin/skills/` — skill/command markdown defs;
  `skills/understand/frameworks/*.md` = per-framework prompt-addendum
  snippets read by `/understand` (`<framework-id-lowercase>.md` convention,
  missing file skipped silently — not resolved from the config object).
- `understand-anything-plugin/agents/` — 9 agent prompt files. No `model:`
  in frontmatter (platform portability, see notes.md #167).
- `tests/` (repo root) — relocated skill tests, root `vitest.config.ts`.
- `homepage/` — separate Astro site/workspace, unrelated to core.

**Conventions**: relative imports use explicit `.js` extensions on `.ts`
source (`import { X } from "./types.js"`); config literals use
`satisfies FrameworkConfig`/`satisfies LanguageConfig` (not `: Type`); all
structural config validated via Zod v4 in `types.ts`/`schema.ts`, enforced
by `Schema.parse()` in each registry's `register()`; tests in `__tests__/`
or `*.test.ts(x)` next to source; commit prefixes `feat:`/`fix:`/`docs:`/
`style:`/`refactor:`/`test:`/`chore:`.

**Glossary**: `LanguageConfig`/`FrameworkConfig` = zod-validated declarative
descriptors registered into `LanguageRegistry`/`FrameworkRegistry`.
`detectionKeywords` = case-insensitive substrings matched against raw
manifest file content. `layerHints` = per-directory layer metadata on every
builtin framework config, **not yet consumed** by any code in
`packages/core/src` (a separate generic directory-heuristic layer detector
exists instead). Registry `createDefault()` tests assert exact builtin
counts (10 frameworks, 41 languages) — adding a builtin bumps that literal.
```

## Ticket (full content)

`.ai/tickets/UA-1-add-angular-framework-detection.md` (as submitted, before /plan moved it into `tasks/UA-1/ticket.md`):

```
---
id: UA-1
title: Add Angular framework detection to core
status: new
created: 2026-07-02
---

Add a `FrameworkConfig` for Angular to `@understand-anything/core` so that
Angular projects are detected the way React/Vue/Next.js already are. Angular
is a TypeScript/JavaScript framework detected via `package.json`
dependencies (`@angular/core`). Follow the existing framework-config
pattern.
```

## Plan produced (full content)

### `.ai/knowledgebase/tasks/UA-1/ticket.md`

```
---
id: UA-1
title: Add Angular framework detection to core
status: planned
created: 2026-07-02
---

Add a `FrameworkConfig` for Angular to `@understand-anything/core` so that
Angular projects are detected the way React/Vue/Next.js already are. Angular
is a TypeScript/JavaScript framework detected via `package.json`
dependencies (`@angular/core`). Follow the existing framework-config
pattern.

## Q&A (Planning)

Autonomous run, no human available. Each open question below is resolved
from code evidence in `packages/core/src/languages/` (types.ts, the 10
existing `frameworks/*.ts` configs, `framework-registry.ts`, and
`__tests__/framework-registry.test.ts`) and recorded as a numbered
assumption. See `.ai/notes.md` ("Language/framework registry pattern") for
the underlying evidence trail.

1. **`languages` field**: Angular is TypeScript-only in practice (the
   Angular CLI scaffolds `.ts` by default; there is no first-class
   plain-JavaScript Angular starter comparable to React/Vue's JS mode).
   Assumption: `languages: ["typescript"]`, unlike React/Vue/Next.js/Express
   which list both `"typescript"` and `"javascript"`.

2. **`detectionKeywords`**: Angular projects always depend on
   `@angular/core` (the framework's runtime package); `@angular/cli` and
   `@angular/common` are near-universal companions in a generated
   `package.json`. Assumption: `["@angular/core", "@angular/cli",
   "@angular/common"]`, matching the 3-keyword shape used by `reactConfig`.
   Checked for collisions against all 10 other frameworks' keyword lists
   (`django`, `fastapi`, `flask`, `react`, `nextjs`, `express`, `vue`,
   `spring`, `rails`, `gin`) — no substring overlap in either direction.

3. **`manifestFiles`**: `["package.json"]`, same as every other JS/TS
   framework config (`react`, `nextjs`, `express`, `vue`).

4. **`promptSnippetPath`**: value `"./frameworks/angular.md"`, following the
   `./frameworks/<id>.md` convention used by all 10 existing configs. Per
   `notes.md`, this string is **not resolved from the config object by any
   code** — `skills/understand/SKILL.md` independently builds
   `./frameworks/<framework-id-lowercase>.md` relative to its own directory
   and skips silently if the file is missing, so the zod schema (`min(1)`
   string) is satisfied by the value alone and Angular detection works
   without the physical `.md` file existing. Assumption: create the actual
   snippet file anyway, as a **separate, lower-priority task (`02-`)**, for
   feature parity with the other 10 frameworks (all of which have a file
   under `skills/understand/frameworks/`) — it is not required for
   `framework-registry.test.ts` to pass and does not block task 01.

5. **`entryPoints`**: Assumption:
   `["src/main.ts", "src/app/app.config.ts", "src/app/app.module.ts"]` —
   covers both the modern standalone-bootstrap convention (`app.config.ts`,
   default since Angular 17) and the classic NgModule bootstrap
   (`app.module.ts`), mirroring how `nextjsConfig` lists multiple
   version-era entry-point candidates.

6. **`layerHints`**: the ticket did not specify a directory set; the plan
   directive (see task 01) asks for `components/services/modules/guards/
   pipes`, Angular's canonical CLI-generated directory names. Assumption:
   map `components → "ui"`, `directives → "ui"`, `services → "service"`,
   `modules → "config"` (an `@NgModule` declares/wires providers similarly
   to how `springConfig` maps `config → "config"` for DI wiring),
   `guards → "middleware"` (route guards gate navigation, the same role
   `express`/`gin`/`rails` assign to `middleware`), `pipes → "utility"`
   (data-transform functions, the same role `rails` assigns `helpers` and
   `fastapi` assigns `schemas`→`types`/`crud`→`service`), and
   `interceptors → "middleware"` (HTTP interceptors, same role as guards).
   Per `notes.md`, `layerHints` is currently declarative-only (no consumer
   in `packages/core/src`), so this choice affects no runtime behavior today
   — it only needs to be internally consistent with the vocabulary the other
   9 configs use (`ui`, `service`, `api`, `data`, `config`, `middleware`,
   `utility`, `types`), which it is.

7. **Builtin-count test literal**: adding an 11th `FrameworkConfig` makes
   `FrameworkRegistry.createDefault().getAllFrameworks()` return 11, not 10.
   `__tests__/framework-registry.test.ts` line ~111 currently asserts
   `.toHaveLength(10)` in a test titled "registers all 10 built-in framework
   configs". Assumption: this is in scope for UA-1 (task 01) even though the
   ticket body doesn't call it out explicitly — leaving it unfixed breaks
   `pnpm --filter @understand-anything/core test`, which is part of the CI
   gate (`.github/workflows/ci.yml` step "Test core"). Update the literal to
   `11` and the test title to match.

## Acceptance Criteria

- A new `FrameworkConfig` for Angular exists, registered as a builtin
  framework, discoverable via `FrameworkRegistry.createDefault().getById("angular")`.
- `FrameworkRegistry.createDefault().detectFrameworks({...})` detects
  Angular from a `package.json` containing an `@angular/core` dependency,
  the same way it detects React from `react`/`react-dom`.
- The new config parses successfully against `FrameworkConfigSchema`
  (zod) — validated implicitly by `FrameworkRegistry.register()` calling
  `.parse()`, and explicitly by the new test.
- `pnpm --filter @understand-anything/core test` passes, including the
  updated builtin-count assertion (11, not 10).
- `pnpm lint` passes (ESLint, `@typescript-eslint/no-unused-vars` etc.) on
  all touched files.
- No other framework's detection is affected (no keyword collisions
  introduced).
```

### `.ai/knowledgebase/tasks/UA-1/plan.md`

```
---
ticket: UA-1
status: planned
read-first: .ai/agent/phases/implementation.md
kb-commit: a381af24397dffddfe8116673c5e330a28bcb50d
updated: 2026-07-02
---

# Plan: UA-1 — Add Angular framework detection to core

Read `ticket.md` first (Q&A / assumptions), then the task files below.

| # | Task file | Depends on | Parallel | Status |
|---|---|---|---|---|
| 01 | `01-angular-framework-config.md` | — | ok | planned |
| 02 | `02-angular-prompt-snippet.md` (optional, lower priority) | — | ok | planned |

Task 01 is the ticket's core scope (framework detection: new config,
registration, tests — fixes the 10→11 builtin-count assertion along the
way). Task 02 is an optional feature-parity addition (the prompt-injection
`.md` snippet other frameworks have); it does not block 01 and is not
required for the ticket's acceptance criteria to pass.
```

### `.ai/knowledgebase/tasks/UA-1/01-angular-framework-config.md`

```
---
status: planned
depends: []
parallel: ok
---

# Task 01: Add Angular FrameworkConfig + registration + tests

## Goal

Add a builtin `FrameworkConfig` for Angular to `@understand-anything/core`,
registered exactly like the 10 existing frameworks (`django`, `fastapi`,
`flask`, `react`, `nextjs`, `express`, `vue`, `spring`, `rails`, `gin`), so
`FrameworkRegistry.createDefault()` can detect Angular projects from
`package.json` and look up the config by id `"angular"`.

## Pre-bound KB nodes

- `architecture/overview` (hot, embedded in AGENTS.md) — module map, core
  package layout.
- `conventions/code-style` (hot, embedded in AGENTS.md) — `.js` import
  extensions, `satisfies` pattern, zod validation.
- `conventions/testing` (cold) — two-vitest-config split; core tests run via
  `pnpm --filter @understand-anything/core test`, NOT covered by root
  `pnpm test`; exact-count assertions on `createDefault()` must be updated
  when a builtin is added.
- `.ai/notes.md` § "Language/framework registry pattern (relevant to UA-1)"
  — full evidence trail for the registry pattern, `detectFrameworks`
  matching semantics, and why `layerHints`/`promptSnippetPath` are
  currently declarative-only.
- `.ai/knowledgebase/tasks/UA-1/ticket.md` § Q&A — the 7 numbered
  assumptions this task implements.

## Affected files

1. **NEW** `understand-anything-plugin/packages/core/src/languages/frameworks/angular.ts`
2. **EDIT** `understand-anything-plugin/packages/core/src/languages/frameworks/index.ts`
   — import, add to `builtinFrameworkConfigs` array, add to the re-export
   block.
3. **EDIT** `understand-anything-plugin/packages/core/src/__tests__/framework-registry.test.ts`
   — import `angularConfig`, add an Angular detection test, and fix the
   builtin-count assertion (10 → 11).

No other files change. Do not touch `packages/core/src/languages/configs/`
(that directory is for *languages*, e.g. `typescript.ts`; Angular is a
*framework* on top of the existing `typescript` language config — no new
language config is needed or in scope).

## Exact new file: `frameworks/angular.ts`

```ts
import type { FrameworkConfig } from "../types.js";

export const angularConfig = {
  id: "angular",
  displayName: "Angular",
  languages: ["typescript"],
  detectionKeywords: ["@angular/core", "@angular/cli", "@angular/common"],
  manifestFiles: ["package.json"],
  promptSnippetPath: "./frameworks/angular.md",
  entryPoints: [
    "src/main.ts",
    "src/app/app.config.ts",
    "src/app/app.module.ts",
  ],
  layerHints: {
    components: "ui",
    directives: "ui",
    services: "service",
    modules: "config",
    guards: "middleware",
    pipes: "utility",
    interceptors: "middleware",
  },
} satisfies FrameworkConfig;
```

Validated against `FrameworkConfigSchema` (`languages/types.ts`):
`id`/`displayName` non-empty strings — ok; `languages` non-empty array of
non-empty strings — ok (`["typescript"]`); `detectionKeywords` non-empty
array of non-empty strings — ok (3 entries); `manifestFiles` non-empty array
— ok (`["package.json"]`); `promptSnippetPath` non-empty string — ok;
`entryPoints` optional string array — ok; `layerHints` optional
`Record<string,string>` — ok, all 7 values are plain strings.

**Detection-keyword collision check** (against all 9 other registered
frameworks' `detectionKeywords`, per `FrameworkRegistry.detectFrameworks`'s
case-insensitive substring match on the full manifest file content):
- `django`/`fastapi`/`flask`/`spring`/`rails`/`gin` — different manifest
  files entirely (`requirements.txt`/`pyproject.toml`/`Gemfile`/`go.mod`/
  `pom.xml`/`build.gradle*`), never scanned against `package.json` content.
- `react` (`"react"`, `"react-dom"`, `"@types/react"`), `vue` (`"vue"`,
  `"@vue/cli-service"`, `"nuxt"`, `"vite-plugin-vue"`), `nextjs`
  (`"\"next\":"`, `"@next/font"`, `"@next/image"`), `express`
  (`"\"express\":"`, `"express-validator"`, `"express-session"`) all also
  scan `package.json` — none of their keyword substrings appear inside
  `"@angular/core"`, `"@angular/cli"`, or `"@angular/common"`, and none of
  Angular's keyword substrings appear inside theirs. No false-positive
  cross-detection in either direction.
- Both Angular and Express can legitimately be detected on the same
  `package.json` (Angular Universal / SSR setups commonly add `express`) —
  this is existing, correct multi-framework-per-project behavior
  (`detectFrameworks` returns an array), not a bug to fix here.

## Edit: `frameworks/index.ts`

Add the import, insert into the array, and re-export — follow the exact
existing pattern (one line per framework, alphabetical-by-introduction-order
is NOT enforced; append at the end like every prior addition has):

```ts
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
```

Note the `.js` extension on the new import (`./angular.js`, not
`./angular.ts`) — required by the project's ESM import convention
(`conventions/code-style`), even though the file on disk is `angular.ts`.

## Edit: `__tests__/framework-registry.test.ts`

1. Add the import at the top, alongside the existing two:
   ```ts
   import { djangoConfig } from "../languages/frameworks/django.js";
   import { reactConfig } from "../languages/frameworks/react.js";
   import { angularConfig } from "../languages/frameworks/angular.js";
   ```

2. Add a new `it` inside the `describe("detectFrameworks", ...)` block
   (after the existing "detects React from package.json" case, ~line 47),
   mirroring that test's shape exactly:
   ```ts
   it("detects Angular from package.json", () => {
     const registry = new FrameworkRegistry();
     registry.register(angularConfig);
     const detected = registry.detectFrameworks({
       "package.json": '{"dependencies": {"@angular/core": "^17.0.0", "@angular/common": "^17.0.0"}}',
     });
     expect(detected).toHaveLength(1);
     expect(detected[0].id).toBe("angular");
   });
   ```

3. Fix the builtin-count assertion inside `describe("createDefault", ...)`
   (currently ~line 108-112):
   ```ts
   // before
   it("registers all 10 built-in framework configs", () => {
     const registry = FrameworkRegistry.createDefault();
     expect(registry.getAllFrameworks()).toHaveLength(10);
   });

   // after
   it("registers all 11 built-in framework configs", () => {
     const registry = FrameworkRegistry.createDefault();
     expect(registry.getAllFrameworks()).toHaveLength(11);
   });
   ```
   This is not optional: `pnpm --filter @understand-anything/core test`
   fails without it (the CI "Test core" step), independent of anything new
   this task adds.

4. Optional (not required to satisfy acceptance criteria, but consistent
   with the existing `"returns frameworks for all listed languages
   (cross-language)"` test at ~line 84): no change needed to the
   `getForLanguage("typescript")`/`getForLanguage("javascript")` assertions
   in that test or in `"includes frameworks for multiple languages"`
   (~line 114) — both use `.some(...)` / `toBeGreaterThanOrEqual(...)`,
   which remain true after adding Angular to `typescript` only.

## Acceptance criteria

- `understand-anything-plugin/packages/core/src/languages/frameworks/angular.ts`
  exists, exports `angularConfig`, matches the exact block above.
- `frameworks/index.ts` imports, registers (via `builtinFrameworkConfigs`),
  and re-exports `angularConfig`.
- `FrameworkRegistry.createDefault().getById("angular")?.displayName` is
  `"Angular"`.
- `FrameworkRegistry.createDefault().detectFrameworks({ "package.json":
  '{"dependencies":{"@angular/core":"^17.0.0"}}' })` returns exactly one
  result with `id === "angular"`.
- `pnpm --filter @understand-anything/core test` passes (including the
  updated 10→11 builtin-count assertion) — this is the schema validator
  equivalent for this task, since `FrameworkRegistry.register()` calls
  `FrameworkConfigSchema.parse()` on every registration, so a malformed
  `angularConfig` fails the test suite at import/registration time, not
  silently.
- `pnpm lint` passes on the three touched files (no unused imports, no
  `no-explicit-any` violations — N/A here, no `any` used).
- No existing test in `framework-registry.test.ts` or
  `language-registry.test.ts` regresses.

## Test skeleton (full diff shape for the test file's relevant regions)

See "Edit: `__tests__/framework-registry.test.ts`" above — the three edits
(import, new test, count fix) are the complete diff to that file; no other
lines change.
```

### `.ai/knowledgebase/tasks/UA-1/02-angular-prompt-snippet.md`

```
---
status: planned
depends: []
parallel: ok
---

# Task 02 (optional, lower priority): Angular prompt snippet for `/understand`

## Goal

Add `understand-anything-plugin/skills/understand/frameworks/angular.md`,
the prompt-addendum snippet the `/understand` skill appends to the
file-analyzer/architecture-analyzer prompts when Angular is detected — for
feature parity with all 10 existing frameworks, each of which has a
matching file in that directory (`django.md`, `fastapi.md`, `flask.md`,
`react.md`, `nextjs.md`, `express.md`, `vue.md`, `spring.md`, `rails.md`,
`gin.md`).

## Why this is a separate, optional task

Per `ticket.md` assumption 4 and `.ai/notes.md`: the `FrameworkConfig.
promptSnippetPath` field is a plain zod `min(1)` string, not resolved from
the config object by any code path. The actual consumer is
`understand-anything-plugin/skills/understand/SKILL.md` (Phase 3, step 3),
which independently derives `./frameworks/<framework-id-lowercase>.md`
relative to its own directory and — quoting the file — "If the file does
not exist for a detected framework, skip it silently and continue." This
means:

- Task 01 is fully sufficient for Angular *detection* (the ticket's stated
  scope) and for `framework-registry.test.ts` / `pnpm --filter
  @understand-anything/core test` to pass, with or without this task.
- This task only affects prompt quality during an actual `/understand` run
  on an Angular project (an LLM-agent-facing concern, not a testable core
  unit), which is why it is split out rather than bundled into task 01.

## Affected files

1. **NEW** `understand-anything-plugin/skills/understand/frameworks/angular.md`

No code files change; no test file changes (there is no automated test
covering `SKILL.md`'s snippet-injection step in the sampled test suite —
verify this still holds before treating "no test" as final; if a test does
cover it, add an Angular case there instead of skipping verification).

## Content shape

Follow `react.md`'s structure exactly (verified structure, see
`understand-anything-plugin/skills/understand/frameworks/react.md`):
- H1 title: `# Angular Framework Addendum`
- A blockquote note: injected into file-analyzer/architecture-analyzer
  prompts when Angular is detected; not a standalone prompt.
- `## Angular Project Structure` section.
- `### Canonical File Roles` — a `| File / Pattern | Role | Tags |` table
  covering at minimum the directories named in task 01's `layerHints`:
  `components/*.ts`, `directives/*.ts`, `services/*.ts`, `*.module.ts`,
  `guards/*.ts` (or `*.guard.ts`), `pipes/*.ts` (or `*.pipe.ts`),
  `interceptors/*.ts`, plus Angular-specific conventions: `*.component.ts`
  (paired `.html`/`.scss` co-located), `*.spec.ts` (Angular's default test
  suffix, distinct from the project-wide `*.test.ts` convention —
  file-analyzer should still tag these `test`), `src/main.ts` (bootstrap
  entry), `src/app/app.config.ts` (standalone providers config, Angular 17+
  default) or `src/app/app.module.ts` (classic `@NgModule` root, still
  common in pre-17 / non-standalone projects).
- `### Edge Patterns to Look For` — at least: dependency injection via
  constructor parameters (`depends_on` edges from a component/service to
  each injected service type); `@Input()`/`@Output()` component
  communication; route-guard wiring in `*-routing.module.ts` or
  standalone `provideRouter` route arrays (`depends_on` edges from route
  definitions to guarded components and guards).

## Acceptance criteria

- File exists at the exact path above.
- Structurally matches the other 10 snippet files (H1 title, blockquote
  note, `## <Framework> Project Structure`, a canonical-file-roles table,
  an edge-patterns section) — diff against `react.md` or `vue.md` for
  shape, not content.
- `pnpm lint` is unaffected (Markdown files are outside the ESLint
  `files`/`ignores` scope — confirm this file's directory isn't caught by
  any `eslint.config.mjs` ignore pattern that would otherwise matter; it
  isn't, since `.md` files aren't linted by the TS/JS ESLint config at all).
- Does not modify `angular.ts`, `frameworks/index.ts`, or any test file
  (those are task 01's exclusive scope — keep the two tasks' diffs
  non-overlapping).
```

### `.ai/knowledgebase/tasks/UA-1/kb-delta.yaml`

```yaml
pending:
  - node: .ai/notes.md
    change: >
      Update "Language/framework registry pattern" section: builtin
      framework count is 11 (not 10) after angularConfig is registered;
      __tests__/framework-registry.test.ts's exact-count assertion was
      bumped accordingly. If a 12th framework is ever added, the same
      literal must be bumped again.
  - node: domain/glossary.md
    change: >
      Angular joins the framework glossary as a TypeScript-only builtin
      FrameworkConfig (id "angular"), the first builtin config whose
      `languages` array has a single entry rather than
      ["typescript","javascript"].
  - node: architecture/overview.md
    change: >
      Optional: mention Angular alongside React/Vue/Next.js in the core
      module summary once task 01 lands, if the overview is felt to be
      stale — not required, the module list already says "10 builtin
      FrameworkConfig" generically enough that this is low-priority.
```

## .ai commit history

```
596759c plan: UA-1
a381af2 add-ticket: UA-1
35ec3cd explore: initial KB
a3226ec init: scaffold KB + phase docs (understand-anything)
```

## Plan-review outcome

Spawned a fresh `general-purpose` subagent (the harness's fixed agent-type
list does not expose the repo-local `reviewer` subagent type, so this
followed planning.md's fallback: "spawn a fresh general-purpose sub-agent
given only the plan and the acceptance criteria"). The subagent was given
only the plan/ticket file paths plus explicit instructions to cross-check
every claim against the actual source (`types.ts`, `framework-registry.ts`,
`frameworks/index.ts`, `react.ts`/`vue.ts`/`nextjs.ts`/`express.ts`,
`framework-registry.test.ts`) — it had no access to this session's
reasoning.

**Verdict: plan sound, no correctness gaps.** The reviewer independently
verified: every field of the proposed `angular.ts` block against
`FrameworkConfigSchema`; zero keyword-collision with the other 9
(pre-Angular) frameworks' `detectionKeywords` in both directions; the
`frameworks/index.ts` "before" state matches the plan's diff base exactly;
the test file's claimed line numbers (`toHaveLength(10)` at line 111, title
at line 109, React test ending at line 47) match the actual file; the
`promptSnippetPath`/`layerHints` non-consumption claim confirmed via
repo-wide grep; and that no other file (e.g. `core/src/index.ts`,
`languages/index.ts`) needs touching since they only re-export the
`builtinFrameworkConfigs` array, not individual configs.

One nitpick: `ticket.md`'s assumption 2 said "checked against all 9 other
frameworks" while listing 10 framework names — an off-by-one in the prose
only (the analysis itself correctly covered all 10). Fixed directly in
`ticket.md` after the review (10 other frameworks, not 9).

## Observations

The framework's phase-doc-first workflow (read `init.md`/`planning.md`
before acting) kept the explore and plan phases well-scoped without
re-deriving instructions; `probe.py`'s deterministic inventory correctly
seeded the module/build-command facts and saved a full manual pass over
`package.json`s. The registry-pattern sampling (types.ts + 6+ framework
configs + both test files) surfaced two non-obvious findings that a
shallower read would have missed and that materially changed the plan: (1)
`promptSnippetPath` and `layerHints` are declarative-only today — no
runtime consumer in `packages/core/src` — which is why the .md snippet was
split into an optional task rather than bundled in; and (2) the
`FrameworkRegistry.createDefault()` test hardcodes `toHaveLength(10)`,
which silently breaks CI if a new framework is added without updating it —
this was folded into task 01's mandatory scope even though the ticket text
never mentioned it. The planned `angular.ts` block is complete and correct
against `FrameworkConfigSchema` and the `react.ts`-established pattern
(confirmed independently by the fresh-context reviewer subagent, which
cross-checked it field-by-field against the zod schema and grepped for
keyword collisions across all 10 pre-existing frameworks). The one rough
edge was ambient: the repo-local `reviewer` subagent type isn't reachable
through this harness's fixed agent roster, so the review had to go through
the general-purpose fallback path explicitly named in `planning.md` — it
worked, but required writing a longer, more prescriptive review prompt to
compensate for the agent not having the `reviewer.md` persona baked in.
