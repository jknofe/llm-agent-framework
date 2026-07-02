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

No unit-test suite. Validate mechanically:

1. Syntax: `python3 -c "import ast; ast.parse(open('init_agent.py').read())"`
2. Scaffold into a throwaway dir (init writes to CWD) and inspect:
   ```
   d=$(mktemp -d); ( cd "$d" && python3 /path/init_agent.py \
     --name t --description d --size small --harness claude -y )
   ```
   Run for both `--size small|large` and both `--harness claude|copilot`.
3. Grep the generated files to confirm your template change rendered, and that
   any referenced tool path actually exists and runs (e.g. `probe.py` ships in
   both profiles). A dangling path in a template is a silent break.
4. Re-init preservation: scaffold, hand-edit a KB/notes/project-context file,
   re-run init, confirm it reports `preserved` and did not revert.
5. End-to-end: the `benchmarks/` runs are the real regression harness. A
   behavior change worth shipping is worth a benchmark cell (small profile,
   Satty debian-pkg task) before and after.

Always scaffold into a temp dir, never into this repo root.
