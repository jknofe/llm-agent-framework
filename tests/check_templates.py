#!/usr/bin/env python3
"""Checks that only became possible once templates were files.

Run: python3 tests/check_templates.py

Stdlib only, no framework. Each check answers a question that used to be
unanswerable while the content lived inside string literals:

  orphans    is every template actually reached by the generator?
  slots      does every slot a template declares get filled?
  unfilled   does any rendered artifact still contain a `${...}`?
  python     do the rendered tools and hooks parse as Python?
  json       does the rendered settings.json parse as JSON?
  register   do the templates honor the no-em-dash rule (CONCEPT section 8)?

The byte-identity harness lives outside this file: it renders all four
variants and diffs them against a known-good capture. This file checks
properties that hold regardless of what the output happens to be.
"""

import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from agentgen import content, render  # noqa: E402
from agentgen.const import SKILLS_LARGE, SKILLS_SMALL  # noqa: E402

VARIANTS = [(s, h) for s in ("large", "small") for h in ("claude", "copilot")]
failures = []


def fail(check, msg):
    failures.append(f"[{check}] {msg}")


def all_templates():
    return sorted(p.relative_to(render.TEMPLATES).as_posix()
                  for p in render.TEMPLATES.rglob("*") if p.is_file())


def rendered_artifacts():
    """Every (label, text) the generator can produce, across all variants."""
    out = []
    for size, harness in VARIANTS:
        specs = (content.command_specs(harness, "$F", "$T") if size == "large"
                 else content.command_specs_small(harness, "$F", "$T"))
        for name, desc, body in specs:
            out.append((f"{size}/{harness} skill:{name}", body))
            out.append((f"{size}/{harness} skill:{name} desc", desc))
        agents = (content.render_agents_md("p", "d", harness) if size == "large"
                  else content.render_agents_md_small("p", "d", harness))
        out.append((f"{size}/{harness} AGENTS.md", agents))
        out.append((f"{size}/{harness} reviewer",
                    content.render_reviewer_agent(small=(size == "small"))))
        out.append((f"{size}/{harness} settings.json",
                    content.render_settings_json(small=(size == "small"))))
    for fn in ("render_phase_init", "render_phase_planning",
               "render_phase_implementation"):
        f = getattr(content, fn)
        try:
            out.append((fn, f("claude")))
        except TypeError:
            out.append((fn, f()))
    for fn in ("render_tool_probe", "render_tool_gen_index",
               "render_tool_check_stale", "render_tool_gen_rules",
               "render_hook_protect_generated", "render_hook_ai_repo_clean",
               "render_hook_regen_index", "render_notes_stub"):
        out.append((fn, getattr(content, fn)()))
    return out


def check_orphans():
    """Every template file must be reached by some render call."""
    used = set()
    for path in (REPO / "agentgen").rglob("*.py"):
        used |= set(re.findall(r'["\']([\w\-/]+\.(?:md|py|txt|json))["\']',
                               path.read_text()))
    # skill bodies are addressed by roster name, not by literal path
    for name in SKILLS_LARGE:
        used.add(f"skills/large/{name}.md")
    for name in SKILLS_SMALL:
        used.add(f"skills/small/{name}.md")
    for rel in all_templates():
        if rel not in used:
            fail("orphans", f"template never referenced: {rel}")


def check_slots():
    """A template's declared slots must be a subset of what callers pass.

    safe_substitute silently leaves an unknown slot in place, so this is the
    only thing standing between a typo and a `${foo}` shipped into a scaffold.
    """
    for label, text in rendered_artifacts():
        for m in re.findall(r"\$\{?([a-z_][a-z_0-9]*)\}?", text):
            fail("slots", f"{label}: unfilled slot ${m}")


def check_unfilled():
    for label, text in rendered_artifacts():
        if "${" in text:
            fail("unfilled", f"{label}: contains a literal ${{...}}")
        if "@@S_" in text or "@@SLOT" in text:
            fail("unfilled", f"{label}: extraction sentinel leaked")


def check_python():
    for fn in ("render_tool_probe", "render_tool_gen_index",
               "render_tool_check_stale", "render_tool_gen_rules",
               "render_hook_protect_generated", "render_hook_ai_repo_clean",
               "render_hook_regen_index"):
        try:
            ast.parse(getattr(content, fn)())
        except SyntaxError as e:
            fail("python", f"{fn} renders invalid Python: {e}")


def check_json():
    for small in (True, False):
        try:
            json.loads(content.render_settings_json(small=small))
        except json.JSONDecodeError as e:
            fail("json", f"settings.json (small={small}) invalid: {e}")


def check_register():
    """CONCEPT section 8: generated artifacts use plain punctuation."""
    for rel in all_templates():
        if "—" in render.load(rel):
            fail("register", f"em dash in template: {rel}")


def main():
    for check in (check_orphans, check_slots, check_unfilled, check_python,
                  check_json, check_register):
        check()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print(f"ok: {len(all_templates())} templates, "
          f"{len(rendered_artifacts())} rendered artifacts, 6 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
