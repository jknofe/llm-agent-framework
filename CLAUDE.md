# CLAUDE.md

Dev guide for working **on** this framework. Do not scaffold `.ai/` here; this
repo is the generator, not a generated project.

## What this is

`init_agent.py` is a single stdlib-Python (3.x, no deps) scaffolder. It emits
all agent artifacts (AGENTS.md, skills, phase docs, hooks, tools) as string
templates. You change agent behavior by editing the `render_*` / `command_specs*`
functions, never by editing a generated file (those live in target projects).

- `init_agent.py` generator (the whole product)
- `CONCEPT.md` versioned design spec, source of truth (currently v5.6)
- `README.md` user-facing docs
- `install.sh` shell-function installer
- `benchmarks/` empirical validation runs (see its README)

## Feature development

Everything is a template inside `init_agent.py`. Where things live:

- Instructions file: `render_agents_md` (large), `render_agents_md_small` (small)
- Phase docs: `render_phase_init` / `render_phase_planning` / `render_phase_implementation`
- Skills / prompt bodies: `command_specs` (large), `command_specs_small` (small);
  rendered by `render_skills` (claude) and `render_prompt_files` (copilot)
- Embedded tool scripts: `render_tool_probe` / `render_tool_gen_index` /
  `render_tool_check_stale` / `render_tool_gen_rules`
- Hooks: `render_hook_*`; permissions: `render_settings_json`
- Re-init preservation logic: `write_owned` (keeps hand-filled content, never
  reverts to stubs)

Two axes cut through most functions: **profile** (large vs small `_small`
variant) and **harness** (`claude` vs `copilot`). When you add behavior, handle
both or state why one is skipped.

**Language register (CONCEPT.md §8):** normative docs (AGENTS.md, phase docs) in
plain imperative English; KB content (node summaries, tickets) telegraphic.
Identifiers, paths, commands verbatim. No em dashes.

Keep `CONCEPT.md` in sync: behavior changes get a dated entry under the revision
sections and a version bump. CONCEPT.md decides, the templates implement.

## Web research

Do it when a change touches an external ecosystem the generated agent must get
right (packaging policy, linter names, harness/tool APIs, SDK surfaces). Prefer
the `claude-api` skill for anything Claude/Anthropic API related instead of
answering from memory. Verify current tool/CLI behavior against docs before
encoding it into a template; a wrong fact here ships into every scaffold.

## Testing

Full procedure: **[TESTING.md](TESTING.md)**. The short version:

- Layer 1 (every change): syntax check, scaffold all four size/harness
  variants into a temp dir, grep the render, verify referenced tool paths run,
  check re-init preservation, sweep for benchmark-term leakage.
- Layer 2 (behavior changes): run a benchmark cell before and after; runbooks
  and the run index live under `benchmarks/`. Smoke = small profile,
  sonnet + medium, Satty debian-pkg task.

Non-negotiables: never scaffold into this repo root; PASS/FAIL comes from the
deterministic container gate only; generated artifacts stay ecosystem-neutral.
