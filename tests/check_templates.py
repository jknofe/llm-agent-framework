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
  names      does every harness expose the same command names?
  reference  does the /framework-update body name the path where the
             reference scaffold really holds its own copy of that skill?
  budget     does AGENTS.md stay a requirements file (CONCEPT sections 36
             and 38, 72): under 700 words before the generated section on every
             harness, and no artifact still describes the retired overview
             digest, the retired map leaf, or the commands v7.0 dropped?

The byte-identity harness lives outside this file: it renders all four
variants and diffs them against a known-good capture. This file checks
properties that hold regardless of what the output happens to be.
"""

import ast
import contextlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from agentgen import content, render  # noqa: E402
from agentgen.const import HARNESSES, SKILLS  # noqa: E402
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
    for part in ("create", "do", "work", "steps"):
        for harness in HARNESSES:
            out.append((f"{harness} task part:{part}",
                        content.render_task_part(part, harness)))
    out.append(("reviewer", content.render_reviewer_agent()))
    for harness in HARNESSES:
        out.append((f"{harness} worker",
                    content.render_worker_agent(harness)))
    out.append(("opencode worker", content.render_opencode_worker()))
    out.append(("copilot worker", content.render_copilot_agent("worker")))
    for harness in HARNESSES:
        out.append((f"{harness} updater",
                    content.render_updater_agent(harness)))
    out.append(("opencode updater", content.render_opencode_updater()))
    out.append(("copilot updater", content.render_copilot_agent("updater")))
    out.append(("settings.json", content.render_settings_json()))
    out.append(("copilot hooks.json", content.render_copilot_hooks_json()))
    out.append(("opencode config", content.render_opencode_config()))
    out.append(("opencode reviewer", content.render_opencode_reviewer()))
    out.append(("opencode plugin", content.render_opencode_plugin()))
    for fn in ("render_tool_probe", "render_tool_tasks",
               "render_hook_ai_repo_clean", "render_hook_git_guard",
               "render_hook_reviewer_guard", "render_hook_notes_session",
               "render_notes_stub"):
        out.append((fn, getattr(content, fn)()))
    return out


def check_orphans():
    """Every template file must be reached by some render call."""
    used = set()
    for path in (REPO / "agentgen").rglob("*.py"):
        for lit in re.findall(
                r'["\']([\w\-/{}]+\.(?:md|py|txt|json|yaml|js))["\']',
                path.read_text()):
            # per-harness fragments are addressed as f"...{harness}/x.md"
            if "{harness}" in lit:
                used |= {lit.replace("{harness}", h) for h in HARNESSES}
            else:
                used.add(lit)
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
    for fn in ("render_tool_probe", "render_tool_tasks",
               "render_hook_ai_repo_clean"):
        try:
            ast.parse(getattr(content, fn)())
        except SyntaxError as e:
            fail("python", f"{fn} renders invalid Python: {e}")


def check_json():
    for label, fn in (("settings.json", content.render_settings_json),
                      ("copilot hooks.json", content.render_copilot_hooks_json),
                      ("opencode config", content.render_opencode_config)):
        try:
            json.loads(fn())
        except json.JSONDecodeError as e:
            fail("json", f"{label} invalid: {e}")


# The one command a skill may run before the model sees it (CONCEPT.md
# section 84): Claude Code and OpenCode run `!`...`` in a shell as the
# command is rendered, outside the model's control, and abort or expand
# arguments in ways prose that merely quotes the syntax would trigger.
ALLOWED_INJECTIONS = {"claude": {"python3 .ai/agent/tools/tasks.py models "
                                 "--list --exit-zero"},
                      "opencode": {"python3 .ai/agent/tools/tasks.py models "
                                   "--list --exit-zero"},
                      "copilot": set()}
INJECT_RE = re.compile(r"(?:^|(?<=\s))!`([^`\n]*)`")


def check_injection_syntax():
    """Every `!`...`` in a rendered command is a known, argument-free
    injection; a stray one would run in a shell, and a command with `$`
    in it could carry the user's arguments into the shell. Also: an
    OpenCode command expands $1, $2 and needs $ARGUMENTS, and a Claude
    skill with an injection pre-approves its script in `allowed-tools`."""
    for harness in HARNESSES:
        specs = content.command_specs(harness, "$ARGUMENTS", "$ARGUMENTS")
        if harness == "claude":
            files = content.render_skills(specs)
        elif harness == "opencode":
            files = content.render_opencode_commands(specs)
        else:
            files = content.render_prompt_files(specs)
        for fname, text in files.items():
            found = INJECT_RE.findall(text)
            if text.count("!`") != len(found) or "```!" in text:
                fail("injection", f"{harness} {fname}: a !`...` or ```! "
                                  "that is not a plain inline injection")
            for command in found:
                if command not in ALLOWED_INJECTIONS[harness]:
                    fail("injection", f"{harness} {fname}: runs "
                                      f"{command!r}, not an allowed command")
                if "$" in command:
                    fail("injection", f"{harness} {fname}: {command!r} could "
                                      "carry arguments into the shell")
            if found and harness == "claude" and "allowed-tools: Bash(" \
                    not in text:
                fail("injection", f"{fname}: injects without allowed-tools")
            if harness == "opencode":
                if re.search(r"\$\d", text):
                    fail("opencode", f"{fname}: $N would be expanded")
                if "$ARGUMENTS" not in text:
                    fail("opencode", f"{fname}: no $ARGUMENTS, arguments "
                                     "get appended")


def check_register():
    """CONCEPT section 8: generated artifacts use plain punctuation."""
    for rel in all_templates():
        if "—" in render.load(rel):
            fail("register", f"em dash in template: {rel}")


def check_names():
    """The same command names on every harness (CONCEPT.md section 35). A
    per-harness rename is what this used to do, and re-introducing one
    silently is the regression worth catching."""
    emitted = {h: {name for name, _d, _b in
                   content.command_specs(h, "$F", "$T")} for h in HARNESSES}
    first = emitted[HARNESSES[0]]
    for h in HARNESSES[1:]:
        if emitted[h] != first:
            fail("names", f"{h} emits {sorted(emitted[h])}, "
                          f"{HARNESSES[0]} emits {sorted(first)}")


def check_reference():
    """/framework-update takes its migration list from the reference's own
    copy of the skill (CONCEPT section 40). If the path it names is not where
    the scaffold writes that copy, the agent finds nothing and falls back to
    the stale list, silently. Render a reference per harness and look."""
    from agentgen import scaffold
    for harness in HARNESSES:
        body = dict((n, b) for n, _d, b in
                    content.command_specs(harness, "$F", "$T"))[
                        "framework-update"]
        m = re.search(r"<tmpdir>/(\S+)", body)
        if not m:
            fail("reference", f"{harness}: update body names no reference "
                              "skill path")
            continue
        with tempfile.TemporaryDirectory() as tmp, \
                contextlib.redirect_stdout(io.StringIO()):
            scaffold.scaffold(Path(tmp), "p", "d", harness, force=True,
                              reference=True)
            if not (Path(tmp) / m.group(1)).is_file():
                fail("reference", f"{harness}: reference has no "
                                  f"{m.group(1)}")


def check_budget():
    """CONCEPT sections 36 and 38: the always-loaded file carries
    requirements, not an overview. Measured on the rendered file, before the
    generated section, on every harness; the copilot CLI note is the largest
    variant. The second half catches prose that still describes the pre-6.0
    digest, the map leaf 7.0 stopped generating, or a retired command
    (8.0 retired /spec and /build together with `.ai/changes/`).

    `notes/map.md` is exempt in one place: the /framework-update body has to
    name the leaf to say it must not be deleted. That is checked below rather
    than waived, so a map instruction cannot creep back in anywhere else.
    The same holds for `.ai/changes/`: only the update body, which migrates
    it, may name it.
    """
    for harness in HARNESSES:
        text = content.render_agents_md("p", "d", harness)
        pre = text.split("<!-- BEGIN GENERATED")[0]
        words = len(pre.split())
        if words > 700:
            fail("budget", f"{harness} AGENTS.md is {words} words before the "
                           "generated section (max 700)")
    for label, text in rendered_artifacts():
        # "module map" is not banned outright: the templates say "no module
        # map" to forbid one, and the update body has to name the retired
        # leaf. What is banned is the path, which only an instruction to
        # write or read the leaf would contain.
        for stale in ("1500 tokens", "small profile", "small-profile",
                      "re-initializing as large", "size-profile",
                      "/tidy-up", "/import-kb", "/import-agent"):
            if stale in text:
                fail("budget", f"{label}: still says '{stale}'")
        if "notes/map.md" in text and not label.endswith(
                "skill:framework-update"):
            fail("budget", f"{label}: names notes/map.md, retired as "
                           "framework output in 7.0")
        migrates = label.endswith("skill:framework-update")
        for retired in ("`/spec", "`/build", "spec.md", ".ai/changes"):
            if retired in text and not migrates:
                fail("budget", f"{label}: still names {retired!r}, retired "
                               "in 8.0")
        for retired in ("/task-create", "/task-do", "/task-list-all"):
            if retired in text and not migrates:
                fail("budget", f"{label}: still names {retired!r}, folded "
                               "into /task in 9.0")


def check_worker_files():
    """CONCEPT section 77: the worker reads work.md and steps.md only, so
    neither names do.md, the supervisor's part."""
    for harness in HARNESSES:
        for part in ("work", "steps"):
            if "do.md" in content.render_task_part(part, harness):
                fail("worker", f"{harness} {part}.md names do.md")


def check_worker_contract():
    """CONCEPT section 85: on Claude Code and OpenCode the worker's agent
    body is the contract itself, rendered from the one template that also
    writes work.md; Copilot's body points at the file instead. A prompt that
    still says to read work.md first would spend the turn the change saved."""
    for harness, agent in (("claude", content.render_worker_agent("claude")),
                           ("opencode", content.render_opencode_worker())):
        contract = content.render_task_part("work", harness).strip()
        if contract not in agent:
            fail("worker", f"{harness} worker body lacks the work.md contract")
        do = content.render_task_part("do", harness)
        if "work.md and follow it" in do:
            fail("worker", f"{harness} do.md still sends the worker to read "
                           "work.md at start")
        if "init-agent's model check" not in agent:
            fail("worker", f"{harness} worker lost the model-check guard")
    pointer = content.render_copilot_agent("worker")
    if ".ai/agent/task/work.md" not in pointer or \
            "Work (the worker's body)" in pointer:
        fail("worker", "copilot worker body is not the pointer")
    if "work.md and follow it" not in content.render_task_part("do",
                                                               "copilot"):
        fail("worker", "copilot do.md does not send its worker to work.md")


def main():
    for check in (check_orphans, check_slots, check_unfilled, check_python,
                  check_json, check_injection_syntax, check_register, check_names,
                  check_reference,
                  check_budget, check_worker_files, check_worker_contract):
        check()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print(f"ok: {len(all_templates())} templates, "
          f"{len(rendered_artifacts())} rendered artifacts, 11 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
