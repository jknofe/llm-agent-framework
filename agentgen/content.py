"""Every render_* entry point.

These are thin: each one computes whatever varies on harness and hands the
rest to a template under `templates/`. The prose itself is not here, which is
the point. Adding a skill means adding a template file and a name to the
roster in `const`, not editing a string in Python.
"""

import json

from agentgen import render
from agentgen.const import *  # noqa: F403  shared paths, markers, roster
# `import *` skips underscore names; this one is internal but shared.
from agentgen.const import _SKILL_DESCRIPTIONS

def _entry_note(harness: str) -> str:
    """Where AGENTS.md tells the reader the commands live, per harness."""
    if harness == "claude":
        return "packaged as Agent Skills under `.claude/skills/`"
    if harness == "hermes":
        return f"packaged as Agent Skills under `{HERMES_SKILLS_DIR}/`"
    return "exposed as prompt files under `.github/prompts/`"

def render_agents_md(project_name: str, description: str = "",
                           harness: str = "claude",
                           generated_body: str = None) -> str:
    """AGENTS.md: requirements only (framework v7). The generated section
    holds commands and rules; no overview of the codebase is written here or
    anywhere else, and the source is read on demand (CONCEPT.md section 38)."""
    if generated_body is None:
        seed = f"{description}\n" if description else ""
        generated_body = (f"{seed}<!-- Populated by /explore. "
                          "Do not edit by hand. -->")
    hook_note = render.load(f"instructions/fragments/{harness}/hook-note.md")
    entry_note = _entry_note(harness)
    cli_note = ""
    if harness == "copilot":
        cli_note = render.load("instructions/fragments/copilot/cli-note.md")
    elif harness == "hermes":
        cli_note = render.load("instructions/fragments/hermes/cli-note.md")
    return render.fill("instructions/agents.md",
                       cli_note=cli_note,
                       entry_note=entry_note,
                       gen_begin=GEN_BEGIN,
                       gen_end=GEN_END,
                       generated_body=generated_body,
                       hook_note=hook_note,
                       project_name=project_name)

def render_notes_stub() -> str:
    return render.fill("config/notes-stub.md")

def render_update_body(harness: str, arg: str) -> str:
    """Body of the /framework-update skill: an agent-driven framework update.

    A scaffolder can only own files whole (regenerate or freeze), which is why
    updating used to lose user edits, keep retired files, and never migrate the
    shape of hand-filled content. Those are merge decisions, so the agent makes
    them. The rule the whole procedure serves: what the project knows is the
    expensive artifact, so an update migrates it and never re-derives it.

    Varies on harness, which decides which framework files exist to merge:
    settings, hooks and skills on claude, project skills and hooks on hermes,
    prompt files and hooks on copilot.
    """
    if harness == "claude":
        backup_paths = "AGENTS.md and `.claude/`"
        merge_cases = (
            "     - `.claude/settings.json`: permission entries and hooks a user\n"
            "       added are not framework state. Union them with the\n"
            "       reference's; drop only entries the reference retired.\n"
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            "     - skills, hooks, or sub-agents present here but not in the\n"
            "       reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = (
            "   - `.claude/settings.json` parses as JSON and every hook command\n"
            "     it names points at a file that exists.\n")
    elif harness == "hermes":
        backup_paths = (f"AGENTS.md, `{HERMES_SKILLS_DIR}/` and "
                        f"`{HERMES_HOOKS_DIR}/`")
        merge_cases = (
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            f"     - skills under `{HERMES_SKILLS_DIR}/` or hooks under\n"
            f"       `{HERMES_HOOKS_DIR}/` present here but not in the\n"
            "       reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = (
            f"   - Every `{HERMES_SKILLS_DIR}/<name>/SKILL.md` starts with `---` at\n"
            "     byte zero and its `name` matches its directory. Reload them in a\n"
            "     running session with `/reload-skills`.\n"
            f"   - `{HERMES_HOOKS_DIR}/hermes-hooks.yaml` matches the entries in\n"
            "     `~/.hermes/config.yaml`; if they differ, show the user the\n"
            "     diff to merge, since the framework never writes outside the\n"
            "     repository. The dispatcher copy at\n"
            "     `~/.hermes/agent-hooks/llm-agent-hook.py` is the user's to\n"
            "     refresh from `hermes_dispatch.py` when it changed.\n")
    else:
        backup_paths = (f"AGENTS.md, `.github/prompts/` and "
                        f"`{COPILOT_HOOKS_DIR}/`")
        merge_cases = (
            f"     - `{COPILOT_HOOKS_DIR}/llm-agent.json`: hook entries a user\n"
            "       added are not framework state. Union them with the\n"
            "       reference's; drop only entries the reference retired.\n"
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            "     - prompt files under `.github/prompts/` or hooks under\n"
            f"       `{COPILOT_HOOKS_DIR}/` present here but not in the\n"
            "       reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = (
            f"   - `{COPILOT_HOOKS_DIR}/llm-agent.json` parses as JSON and every\n"
            "     hook command it names points at a file that exists.\n")

    owned = ("`.ai/notes.md`, `.ai/notes/<topic>.md`, change specs under\n"
             "`.ai/changes/`, and the `GENERATED:project-context` section of\n"
             "AGENTS.md")
    migrate = (
        "   - Framework 7.1 retires the `CLAUDE.md` pointer on the claude\n"
        "     harness: Claude Code 2.1.277 and later reads AGENTS.md itself\n"
        "     when no CLAUDE.md exists in the working directory or above it.\n"
        "     Delete the pointer only if it holds nothing but the `@AGENTS.md`\n"
        "     import; text the user added below the import makes it the\n"
        "     user's file, so keep it. Keep it too, and say why, when a\n"
        "     CLAUDE.md or CLAUDE.local.md sits in a parent directory or the\n"
        "     sessions run without AGENTS.md support (Amazon Bedrock,\n"
        "     telemetry disabled): there Claude never reads AGENTS.md on its\n"
        "     own and the import is what loads it.\n"
        "   - Framework 7.0 retires `.ai/notes/map.md` as framework output.\n"
        "     Do not delete it and do not remove its pointer from\n"
        "     `.ai/notes.md`: the moment the framework stopped generating it\n"
        "     it became ordinary notes content the user may have edited, and\n"
        "     an update never deletes a notes leaf. Report it as no longer\n"
        "     maintained by the framework and leave trimming it to the user.\n"
        "     The same holds for anything else under `.ai/notes/`.\n"
        "   - Framework 6.0 splits the project-context digest, for a scaffold\n"
        "     coming from 5.x: AGENTS.md keeps only requirements\n"
        "     (build/test/lint commands, required or forbidden tools, project\n"
        "     rules, pointers to existing docs, cap ~300 tokens); the purpose\n"
        "     paragraph, stack, module map and glossary move verbatim to\n"
        "     `.ai/notes/map.md`, linked from `.ai/notes.md` as\n"
        "     `- [map](notes/map.md) - module map, stack, glossary`. Move the\n"
        "     content that is there; do not re-derive it from the codebase,\n"
        "     and drop nothing. 7.0 stops maintaining that leaf but still\n"
        "     wants the content off AGENTS.md rather than lost.\n"
        "   - New or renamed sections in the digest: add the heading and move\n"
        "     the matching content that is already there under it.\n"
        "   - A changed spec format: bring existing `.ai/changes/<id>/spec.md`\n"
        "     files up to it, keeping every goal, criterion, and task intact.\n"
        "     7.0 did not change it; leave existing specs and anything under\n"
        "     `.ai/changes/_archive/` exactly as they are.\n"
        "   - Moved or renamed directories: `git mv` inside `.ai` so the notes\n"
        "     history survives the move.\n")

    return render.fill("skills/bodies/update.md",
                       arg=arg,
                       backup_paths=backup_paths,
                       framework_json=FRAMEWORK_JSON,
                       harness=harness,
                       merge_cases=merge_cases,
                       migrate=migrate,
                       owned=owned,
                       verify_extra=verify_extra,
                       verify_tools=f"`{TOOLS_DIR}/probe.py`")

def command_specs(harness: str, arg_focus: str, arg_ticket: str) -> list:
    """(name, description, body) for each command, in roster order.

    Each name resolves either to a template under templates/skills/ or to a
    composed body in COMPOSED_BODIES (those two vary on harness beyond simple
    slot filling). The description is the template's `description:`
    frontmatter line, kept next to the body it describes so the two cannot
    drift.
    """
    hook_offer = render.load(f"skills/fragments/{harness}/hook-offer.md")
    specs = []
    for name in SKILLS:
        if name in COMPOSED_BODIES:
            desc = _SKILL_DESCRIPTIONS[name]
            body = COMPOSED_BODIES[name](harness, arg_ticket)
        else:
            raw = render.load(f"skills/{name}.md")
            desc, body = _split_frontmatter(raw)
            body = render.render(body, tools_dir=TOOLS_DIR,
                                 arg_focus=arg_focus, arg_ticket=arg_ticket,
                                 hook_offer=hook_offer)
        specs.append((name, desc, body))
    return specs

COMPOSED_BODIES = {
    "framework-update": lambda harness, arg: render_update_body(harness, arg),
}

def _split_frontmatter(raw: str):
    """Return (description, body) from a skill template's `---` header."""
    if not raw.startswith("---\n"):
        raise ValueError("skill template missing frontmatter")
    end = raw.index("\n---\n", 3)
    header = raw[4:end]
    body = raw[end + 5:]
    for line in header.splitlines():
        if line.startswith("description:"):
            return line[len("description:"):].strip(), body
    raise ValueError("skill template frontmatter has no description")

def render_skills(specs) -> dict:
    """Agent Skills (SKILL.md, open standard): .claude/skills/<name>/SKILL.md.
    Read by Claude Code and other SKILL.md-compatible harnesses. Every skill is
    a user-sequenced pipeline step with side effects (KB writes, code changes,
    `.ai` commits), so `disable-model-invocation: true` keeps the model from
    auto-triggering them mid-conversation; only an explicit /name invokes them.
    `specs` is a command_specs list."""
    out = {}
    for name, desc, body in specs:
        hint = ARG_HINTS.get(name)
        hint_line = f"argument-hint: \"{hint}\"\n" if hint else ""
        out[f"{name}/SKILL.md"] = (
            "---\n"
            f"name: {name}\n"
            f'description: "{desc}"\n'
            f"{hint_line}"
            "disable-model-invocation: true\n"
            "---\n"
            f"{body}"
        )
    return out

def render_hermes_skills(specs) -> dict:
    """Hermes project skills: `.agents/skills/<name>/SKILL.md`.

    Same open SKILL.md standard as the claude harness and the same bodies; the
    frontmatter is what differs. Hermes wants a semantic version, a platform
    list and its own metadata block, and it caps the description at 60
    characters, so the long template descriptions give way to
    HERMES_DESCRIPTIONS. `disable-model-invocation` is a claude key and is not
    emitted here; hermes has no equivalent, so the skills stay model-loadable
    on that harness. Names match the other harnesses exactly; where a name
    would collide with a hermes built-in the framework renames it everywhere
    rather than only here (CONCEPT.md section 35).

    Hermes only discovers these once the repository is trusted, which the user
    does with `hermes skills trust`; the AGENTS.md note says so.
    """
    out = {}
    for name, _desc, body in specs:
        out[f"{name}/SKILL.md"] = (
            "---\n"
            f"name: {name}\n"
            f"description: {HERMES_DESCRIPTIONS[name]}\n"
            f"version: {FRAMEWORK_VERSION}.0\n"
            # Audited rather than copied: every skill drives the agent's own
            # tools plus python3 and git, and all three platforms have those.
            "platforms: [linux, macos, windows]\n"
            "metadata:\n"
            "  hermes:\n"
            "    tags: [agent-framework, workflow]\n"
            "---\n"
            f"{body}"
        )
    return out

def render_prompt_files(specs) -> dict:
    """Copilot prompt files: .github/prompts/<name>.prompt.md, VS Code only.
    `specs` is a command_specs list."""
    out = {}
    for name, desc, body in specs:
        out[f"{name}.prompt.md"] = (
            "---\n"
            f'description: "{desc}"\n'
            "mode: agent\n"
            "---\n"
            f"{body}"
        )
    return out

def render_reviewer_agent() -> str:
    """The fresh-context adversarial reviewer used by /build's review gate."""
    return render.fill(
        "agents/reviewer.md",
        coverage=("- Every acceptance criterion is implemented and, where "
                  "testable, tested.\n"
                  "- The spec is self-contained: paths explicit, interfaces "
                  "stated."),
        desc=("Adversarial fresh-context review of a change's diff against "
              "its acceptance criteria. Use for the review gate in /build."),
        input_block=("Input: a code diff plus the change's acceptance "
                     "criteria in\n`.ai/changes/<id>/spec.md`."))

def render_hook_ai_repo_clean() -> str:
    return render.load("hooks/ai_repo_clean.py")

def render_hook_git_guard() -> str:
    return render.load("hooks/git_guard.py")

def render_hook_hermes_dispatch() -> str:
    return render.load("hooks/hermes_dispatch.py")

def render_hermes_hooks_yaml() -> str:
    return render.load("config/hermes-hooks.yaml")

def render_copilot_hooks_json() -> str:
    """Copilot hooks (.github/hooks/llm-agent.json): the same two scripts as
    the claude scaffold, in the Copilot CLI schema that VS Code and the cloud
    agent read as well. Commands are repository-relative; the scripts chdir
    to the payload's cwd themselves. No matcher: tool names differ per
    surface (bash, runTerminalCommand) and the guard filters on a `command`
    argument instead."""
    hooks = {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {
                    "type": "command",
                    "bash": f"python3 {COPILOT_HOOKS_DIR}/git_guard.py",
                    "timeoutSec": 15,
                }
            ],
            "agentStop": [
                {
                    "type": "command",
                    "bash": f"python3 {COPILOT_HOOKS_DIR}/ai_repo_clean.py",
                    "timeoutSec": 15,
                }
            ],
        },
    }
    return json.dumps(hooks, indent=2) + "\n"

def render_tool_probe() -> str:
    """Command and documentation detection, written into the scaffold and run
    at the start of /explore. Static: the template is a real .py file under
    templates/tools/."""
    return render.load("tools/probe.py")

def render_settings_json() -> str:
    """Project settings (.claude/settings.json): a read-only permission allow
    list so exploration runs without a prompt per command, plus the Stop hook
    that enforces the .ai commit rule and the PreToolUse hook that enforces
    the two git guardrails deterministically. Compound commands
    (a && b) prompt unless every part of the chain matches a rule, so common
    chain members (cd, echo, pwd, read-only git) are included as well."""
    allow = render.sectioned_list("config/permissions.txt",
                                  sections=("shared",), tools_dir=TOOLS_DIR)
    hooks = {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                                   '.claude/hooks/git_guard.py"',
                    }
                ],
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                                   '.claude/hooks/ai_repo_clean.py"',
                    }
                ],
            }
        ]
    }
    settings = {"permissions": {"allow": allow}, "hooks": hooks}
    return json.dumps(settings, indent=2) + "\n"
