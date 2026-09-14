# CLAUDE.md

Dev guide for working **on** this framework. Do not scaffold `.ai/` here; this
repo is the generator, not a generated project.

## What this is

`init_agent.py` is a stdlib-Python (3.x, no deps) scaffolder. The prose lives
in real files under `templates/`; the Python only fills slots and decides what
varies. You change agent behavior by editing a template, never by editing a
generated file (those live in target projects).

- `init_agent.py` + `agentgen/` the generator (`const` paths and roster,
  `render` slot filling, `content` the render_* entry points, `scaffold` what
  gets written where)
- `templates/` every artifact the scaffold emits, as files
- `CONCEPT.md` versioned design spec, source of truth (currently v7.0)
- `README.md` user-facing docs
- `install.sh` shell-function installer
- `tests/check_templates.py` the property gate (orphans, slots, register,
  hermes frontmatter, AGENTS.md budget)
- `benchmarks/fixed-runbook.md` fully-pinned reproducible benchmark (only
  MODEL/EFFORT are user-set); recorded runs land in `benchmarks/<run>/`

## Feature development

Where things live:

- Instructions file: `templates/instructions/agents.md` plus per-harness
  fragments under `instructions/fragments/<harness>/`
- Skill bodies: `templates/skills/<name>.md`, one per rostered command; the
  two that vary on harness beyond slot filling are composed in
  `content.COMPOSED_BODIES` from `templates/skills/bodies/`
- Rendered per harness by `render_skills` (claude), `render_hermes_skills`,
  `render_prompt_files` (copilot)
- Embedded tool script: `render_tool_probe` (`templates/tools/probe.py`)
- Hooks: `templates/hooks/`; permissions: `render_settings_json` over
  `templates/config/permissions.txt`
- Adding or removing a command: the roster in `const.SKILLS`, plus its
  `HERMES_DESCRIPTIONS` and `ARG_HINTS` entries. `check_templates` fails if
  a template is orphaned or a hermes description is missing or too long.
- Re-init preservation logic: `write_owned` (keeps hand-filled content, never
  reverts to stubs)
- Framework updates: `render_update_body` (the `/framework-update` skill body,
  varies on harness), the `.ai/agent/framework.json` stamp
  (`render_framework_json`, fed by `write`), and the two CLI flags that serve
  the skill, `--detect` and `--emit-reference`. Bump `FRAMEWORK_VERSION` with
  the CONCEPT.md version. Retiring a framework file is a supported operation:
  drop the `write()` call and `/framework-update` deletes it from existing
  projects via the recorded file list. Do not add a Python update path;
  updating is a merge and belongs to the agent (CONCEPT.md section 24).

One axis cuts through most functions: **harness** (`claude`, `copilot`,
`hermes`). When you add behavior, handle all three or state why one is
skipped. The profile axis is gone (5.22 removed the large profile).

**Language register (CONCEPT.md section 8):** normative docs (AGENTS.md,
skill bodies) in plain imperative English; notes content telegraphic.
Identifiers, paths, commands verbatim. No em dashes.

**What the framework claims (CONCEPT.md section 38):** durable knowledge the
repository cannot state itself, and an opt-in spec-and-build path. A change
that adds an always-loaded summary of the codebase, or that makes spec or
review the default, contradicts a measurement; argue it in CONCEPT.md first.

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

- Layer 1 (every change): `python3 tests/check_templates.py`, syntax check,
  scaffold all three harness variants into a temp dir, grep the render,
  verify referenced tool paths run, check re-init preservation, sweep for
  benchmark-term leakage.
- Layer 2 (behavior changes): run a benchmark cell before and after; the
  fully-pinned procedure is `benchmarks/fixed-runbook.md`. Smoke = sonnet +
  medium (fixed-runbook cell 1, sh-refactor).

Non-negotiables: never scaffold into this repo root; PASS/FAIL comes from the
deterministic container gate only; generated artifacts stay ecosystem-neutral.
