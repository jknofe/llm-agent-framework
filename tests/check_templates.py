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
  hermes     do the hermes skill descriptions fit that harness's 60-char cap,
             and does every harness expose the same command names?
  budget     does AGENTS.md stay a requirements file (CONCEPT section 36):
             under 600 words before the generated section on every harness,
             and no artifact still describes the retired overview digest?

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
from agentgen.const import HERMES_DESCRIPTIONS, SKILLS  # noqa: E402

HARNESSES = ("claude", "copilot", "hermes")
failures = []


def fail(check, msg):
    failures.append(f"[{check}] {msg}")


def all_templates():
    return sorted(p.relative_to(render.TEMPLATES).as_posix()
                  for p in render.TEMPLATES.rglob("*") if p.is_file())


def rendered_artifacts():
    """Every (label, text) the generator can produce, across all harnesses."""
    out = []
    for harness in HARNESSES:
        for name, desc, body in content.command_specs(harness, "$F", "$T"):
            out.append((f"{harness} skill:{name}", body))
            out.append((f"{harness} skill:{name} desc", desc))
        out.append((f"{harness} AGENTS.md",
                    content.render_agents_md("p", "d", harness)))
    out.append(("reviewer", content.render_reviewer_agent()))
    out.append(("settings.json", content.render_settings_json()))
    for fn in ("render_tool_probe", "render_hook_ai_repo_clean",
               "render_notes_stub", "render_claude_pointer"):
        out.append((fn, getattr(content, fn)()))
    return out


def check_orphans():
    """Every template file must be reached by some render call."""
    used = set()
    for path in (REPO / "agentgen").rglob("*.py"):
        used |= set(re.findall(r'["\']([\w\-/]+\.(?:md|py|txt|json))["\']',
                               path.read_text()))
    # skill bodies are addressed by roster name, not by literal path
    for name in SKILLS:
        used.add(f"skills/{name}.md")
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
    for fn in ("render_tool_probe", "render_hook_ai_repo_clean"):
        try:
            ast.parse(getattr(content, fn)())
        except SyntaxError as e:
            fail("python", f"{fn} renders invalid Python: {e}")


def check_json():
    try:
        json.loads(content.render_settings_json())
    except json.JSONDecodeError as e:
        fail("json", f"settings.json invalid: {e}")


def check_register():
    """CONCEPT section 8: generated artifacts use plain punctuation."""
    for rel in all_templates():
        if "—" in render.load(rel):
            fail("register", f"em dash in template: {rel}")


def check_hermes():
    """Hermes frontmatter rules the generator must not break: one short
    description per rostered command, at or below 60 characters, ending in a
    period, and a lowercase-hyphenated skill name matching its directory."""
    for name in sorted(SKILLS):
        desc = HERMES_DESCRIPTIONS.get(name)
        if desc is None:
            fail("hermes", f"no hermes description for /{name}")
            continue
        if len(desc) > 60:
            fail("hermes", f"/{name} description is {len(desc)} chars (max 60)")
        if not desc.endswith("."):
            fail("hermes", f"/{name} description does not end with a period")
    emitted = content.render_hermes_skills(
        content.command_specs("hermes", "$F", "$T"))
    for rel, text in emitted.items():
        cmd = rel.split("/")[0]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", cmd):
            fail("hermes", f"skill name not lowercase-hyphenated: {cmd}")
        if not text.startswith("---\n"):
            fail("hermes", f"{cmd}: SKILL.md does not open with ---")
        if f"\nname: {cmd}\n" not in text:
            fail("hermes", f"{cmd}: name does not match its directory")
    names = {rel.split("/")[0] for rel in emitted}
    for reserved in ("update", "import", "plan", "init", "review", "learn",
                     "memory", "skills", "config", "model", "help", "new",
                     "clear", "resume", "goal", "diff", "status", "export"):
        if reserved in names:
            fail("hermes", f"/{reserved} collides with a hermes built-in")

    # The same names on every harness (CONCEPT.md section 35). A per-harness
    # rename is what this used to do, and re-introducing one silently is the
    # regression worth catching.
    for harness in ("claude", "copilot"):
        other = {name for name, _d, _b in
                 content.command_specs(harness, "$F", "$T")}
        if other != names:
            fail("hermes", f"{harness} emits {sorted(other)}, "
                           f"hermes emits {sorted(names)}")


def check_budget():
    """CONCEPT section 36: the always-loaded file carries requirements, not
    an overview. Measured on the rendered file, before the generated
    section, on every harness; the copilot CLI note is the largest variant.
    The second half catches prose that still describes the pre-6.0 digest."""
    for harness in HARNESSES:
        text = content.render_agents_md("p", "d", harness)
        pre = text.split("<!-- BEGIN GENERATED")[0]
        words = len(pre.split())
        if words > 600:
            fail("budget", f"{harness} AGENTS.md is {words} words before the "
                           "generated section (max 600)")
    for label, text in rendered_artifacts():
        for stale in ("1500 tokens", "small profile", "small-profile",
                      "re-initializing as large", "size-profile"):
            if stale in text:
                fail("budget", f"{label}: still says '{stale}'")


def main():
    for check in (check_orphans, check_slots, check_unfilled, check_python,
                  check_json, check_register, check_hermes, check_budget):
        check()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print(f"ok: {len(all_templates())} templates, "
          f"{len(rendered_artifacts())} rendered artifacts, 8 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
