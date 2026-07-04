# Benchmark Result: ng-plan-s5m-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | ng-plan-s5m-2026-07-03 |
| Cell | understand-anything / plan-only |
| Profile | large |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-04T04:18:34 |
| End | 2026-07-04T04:29:09 |
| Duration | ~10m35s |
| Gate | **PASS** (5/5) |

Target repo: https://github.com/Egonex-AI/Understand-Anything.git, pinned
`0e8ad84a2a5236dca533beef618d71ee3f4568f6`.
Scaffolded with `init_agent.py --name understand-anything --description
"TypeScript / Angular monorepo (pnpm workspaces)" --size large --harness
claude -y`.

## Ticket + plan produced

- Ticket: `.ai/knowledgebase/tasks/FRM-ANGULAR/ticket.md` - "Add Angular
  framework detection to core registry", 7 numbered assumptions recorded
  (languages scope, detection keywords, manifest files, entry points,
  layerHints mapping, prompt-snippet out-of-scope decision, required
  10->11 count-assertion fix).
- Plan: `.ai/knowledgebase/tasks/FRM-ANGULAR/plan.md` - 2 tasks:
  - `01-add-angular-framework-config.md`: new `src/languages/frameworks/angular.ts`
    (`angularConfig`) + the three-site registration edit in
    `src/languages/frameworks/index.ts` (import / array / export).
  - `02-add-angular-registry-test.md` (depends on 01): positive
    detection test, negative false-positive test (added during plan
    review), and the required `toHaveLength(10)` -> `(11)` fix in
    `src/__tests__/framework-registry.test.ts`.
- Plan review: fresh-context `general-purpose` sub-agent used as the
  `reviewer` role (native `reviewer` agent type not spawnable from this
  outer harness; used the autonomous-mode fallback specified in
  `.ai/agent/phases/planning.md` step 6 - given only ticket.md + plan.md
  + task files). Found one real gap (no regression test for the
  false-positive-avoidance rationale behind the narrowed
  `detectionKeywords`); fixed by adding the negative test to task 02.
  Outcome recorded in plan.md's "Plan review" section. Status left
  `planned` (ready for implementation, not started).

## .ai commit history

```
1bea3b7 plan-review: FRM-ANGULAR - add false-positive regression test, record review
8cca376 plan: FRM-ANGULAR
f92167f add-ticket: FRM-ANGULAR
a1a6d65 explore: fill KB nodes (glossary, testing, build, ci-cd, code-style, git-workflow), notes assumptions/gotchas, regen INDEX
d8a0c83 explore: fill architecture/overview (core framework registry)
77ea797 init: scaffold KB + phase docs (understand-anything)
```

## Static gate checks (STEP 5)

**1. plan.md schema-valid (frontmatter keys present incl. kb-commit): PASS**
`.ai/knowledgebase/tasks/FRM-ANGULAR/plan.md:1-7` has `ticket: FRM-ANGULAR`,
`status: planned`, `read-first: .ai/agent/phases/implementation.md`,
`kb-commit: f92167f92315d6e85c7b248abb3afb36e09967e0`, `updated: 2026-07-04`.

**2. Every task file self-contained per the task-file format: PASS**
Both `01-add-angular-framework-config.md` and
`02-add-angular-registry-test.md` have frontmatter (`status`, `depends`,
`parallel`), explicit affected-file paths, pre-bound KB node ids, the
full expected `angularConfig` object / test-diff signatures, and test
skeletons - each readable standalone without the other or this session's
context.

**3. Every affected file named in the plan exists at the pinned SHA: PASS**
Verified with `test -f` at repo root
(`/tmp/benchmark/runs/ng-plan-s5m-2026-07-03/understand-anything`, HEAD =
`0e8ad84a2a5236dca533beef618d71ee3f4568f6`):
- `understand-anything-plugin/packages/core/src/languages/frameworks/index.ts` - EXISTS
- `understand-anything-plugin/packages/core/src/__tests__/framework-registry.test.ts` - EXISTS
- `understand-anything-plugin/packages/core/src/languages/types.ts` - EXISTS
- `understand-anything-plugin/packages/core/src/languages/configs/index.ts` - EXISTS
- `understand-anything-plugin/packages/core/src/languages/configs/typescript.ts` - EXISTS (confirms `"typescript"` is a registered language id, satisfying `angularConfig.languages`)
(The new file `frameworks/angular.ts` does not exist yet by design - it is
the task's deliverable, not a pre-existing affected file.)

**4. Planned FrameworkConfig validates against FrameworkConfigSchema: PASS**

Schema (`understand-anything-plugin/packages/core/src/languages/types.ts:51-60`):
```ts
export const FrameworkConfigSchema = z.object({
  id: z.string().min(1),
  displayName: z.string().min(1),
  languages: z.array(z.string().min(1)).min(1),
  detectionKeywords: z.array(z.string()).min(1),
  manifestFiles: z.array(z.string()).min(1),
  promptSnippetPath: z.string().min(1),
  entryPoints: z.array(z.string()).optional(),
  layerHints: z.record(z.string(), z.string()).optional(),
});
```

Proposed config (plan task 01):
```ts
export const angularConfig = {
  id: "angular",
  displayName: "Angular",
  languages: ["typescript"],
  detectionKeywords: ["@angular/core", "@angular/common", "@angular/cli"],
  manifestFiles: ["package.json"],
  promptSnippetPath: "./frameworks/angular.md",
  entryPoints: ["src/main.ts", "src/app/app.module.ts", "src/app/app.config.ts"],
  layerHints: { components: "ui", pages: "ui", services: "service",
    guards: "middleware", interceptors: "middleware", pipes: "utility",
    directives: "ui", store: "service", modules: "config" },
} satisfies FrameworkConfig;
```

Field-by-field: `id`/`displayName` nonempty strings - present/typed.
`languages` array len 1 >= 1, element nonempty, `"typescript"` a real
registered language id - present/typed. `detectionKeywords` 3 nonempty
strings, len >= 1 - present/typed. `manifestFiles` 1 nonempty string, len
>= 1 - present/typed. `promptSnippetPath` nonempty string - present/typed
(existence of the referenced `.md` file is not schema-checked, by design,
same as every other built-in framework). `entryPoints` optional array of
nonempty strings, present - typed. `layerHints` optional
`Record<string,string>`, present, all keys/values nonempty strings -
typed. All required fields present and correctly typed; optional fields
also present and valid.

**5. The three registration sites actually exist in the repo: PASS**
`understand-anything-plugin/packages/core/src/languages/frameworks/index.ts`:
- Site 1 (import block): line 12 - `import { ginConfig } from "./gin.js";` (new `angularConfig` import to be appended here)
- Site 2 (`builtinFrameworkConfigs` array): line 24 - `ginConfig,` immediately before the closing `];` at line 25
- Site 3 (named export block): line 37 - `ginConfig,` immediately before the closing `};` at line 38

All three sites are distinct lines within the single file
`frameworks/index.ts` (confirmed by `grep -n "ginConfig"` returning
exactly lines 12, 24, 37 - the last existing framework's three mentions,
which is where Angular's three mentions get appended).

**GATE: PASS** - all five checks true.

## Observations

1. The task's premise ("Angular monorepo") was factually wrong for this
   codebase - Understand-Anything is a TS/JS static-analysis tool with no
   Angular code anywhere; Angular is a *new detectable framework* to add
   to its language-agnostic registry, not an existing stack. Explore
   caught and corrected this in `architecture/overview.md` (assumption 1)
   rather than propagating the seeded description at face value.
2. The "three registration sites" turned out to be three lines inside one
   file (`frameworks/index.ts`: import / array / export), not three
   separate files - worth calling out explicitly since a shallower reading
   of "three-place registration" could mistakenly imply three files.
3. The plan-review sub-agent earned its keep: it caught a real gap
   (missing false-positive regression test) that a same-context
   self-review likely would have rationalized away, since the false-
   positive-avoidance rationale was mentioned in the ticket but the test
   task didn't act on it.
4. `promptSnippetPath` pointing at a non-existent `angular.md` is legal
   per the schema (no existence check anywhere in the registry or its
   tests) - this was verified rather than assumed, and explicitly scoped
   out with a numbered assumption rather than silently left ambiguous.
5. The native `reviewer` sub-agent type defined in the scaffolded
   `.claude/agents/reviewer.md` was not spawnable from this outer
   benchmark harness (only `claude`, `claude-code-guide`, `Explore`,
   `general-purpose`, `Plan`, `statusline-setup` were available); the
   framework's own documented fallback (spawn a fresh `general-purpose`
   sub-agent with only the plan + acceptance criteria) was used instead,
   per `.ai/agent/phases/planning.md` step 6, and is recorded as such in
   plan.md.
