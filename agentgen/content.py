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

def render_claude_pointer() -> str:
    return (
        "# CLAUDE.md\n\n"
        "Canonical agent instructions live in AGENTS.md (vendor-neutral).\n"
        "Imported below; do not duplicate content here.\n\n"
        "@AGENTS.md\n"
    )

def render_agents_md(project_name: str, description: str = "",
                           harness: str = "claude",
                           generated_body: str = None) -> str:
    """AGENTS.md: dense and self-contained. The generated project-context
    section is the only knowledge store; the source code is read on demand."""
    if generated_body is None:
        seed = f"{description}\n" if description else ""
        generated_body = (f"{seed}<!-- Populated by /explore. "
                          "Do not edit by hand. -->")
    hook_note = (render.load("instructions/fragments/claude/hook-note.md")
                 if harness == 'claude' else '')
    entry_note = _entry_note(harness)
    cli_note = ""
    if harness == "copilot":
        cli_note = render.load("instructions/fragments/copilot/cli-note.md")
    elif harness == "hermes":
        cli_note = render.load("instructions/fragments/hermes/cli-note.md")
    goal_note = ""
    if harness == "claude":
        goal_note = render.load("instructions/fragments/claude/goal-note.md")
    return render.fill("instructions/agents.md",
                       cli_note=cli_note,
                       entry_note=entry_note,
                       gen_begin=GEN_BEGIN,
                       gen_end=GEN_END,
                       generated_body=generated_body,
                       goal_note=goal_note,
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
    settings, hooks and skills on claude, project skills on hermes, prompt
    files on copilot.
    """
    if harness == "claude":
        backup_paths = "AGENTS.md, CLAUDE.md, and `.claude/`"
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
        backup_paths = f"AGENTS.md and `{HERMES_SKILLS_DIR}/`"
        merge_cases = (
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            f"     - skills under `{HERMES_SKILLS_DIR}/` present here but not in\n"
            "       the reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = (
            f"   - Every `{HERMES_SKILLS_DIR}/<name>/SKILL.md` starts with `---` at\n"
            "     byte zero and its `name` matches its directory. Reload them in a\n"
            "     running session with `/reload-skills`.\n")
    else:
        backup_paths = "AGENTS.md and `.github/prompts/`"
        merge_cases = (
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            "     - prompt files under `.github/prompts/` present here but not in\n"
            "       the reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = ""

    owned = ("`.ai/notes.md`, `.ai/notes/<topic>.md`, change specs under\n"
             "`.ai/changes/`, and the `GENERATED:project-context` section of\n"
             "AGENTS.md")
    migrate = (
        "   - New or renamed sections in the project-context digest: add the\n"
        "     heading and move the matching content that is already there\n"
        "     under it. Do not re-derive the content from the codebase.\n"
        "   - A changed spec format: bring existing `.ai/changes/<id>/spec.md`\n"
        "     files up to it, keeping every goal, criterion, and task intact.\n"
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

def render_tidy_up_body(harness: str, arg: str) -> str:
    """Body of the /tidy-up skill: a bounded hygiene sweep over the host code.

    Four passes with deliberately different authority. Removing dead code and
    rewriting comments or prose is reversible and locally verifiable, so the
    agent does it. Deleting a file is neither, so that pass only proposes. The
    rule the whole procedure serves: a tidy-up may not change behavior, so
    every pass is gated on the same test and lint baseline captured up front.

    Harness decides whether the survey fan-out and the review gate can run in
    sub-agents.
    """
    if harness == "claude":
        survey_note = (
            "   Dispatch the survey fan-out to sub-agents where the harness\n"
            "   supports them: each returns a candidate list with evidence, not\n"
            "   file dumps. Decide every removal yourself.\n")
        review_note = (
            "   Run the `reviewer` sub-agent on the full diff. If it cannot be\n"
            "   spawned, use a fresh general-purpose sub-agent given only the\n"
            "   diff and the rule that behavior must not change.\n")
    else:
        survey_note = (
            "   Survey with your read and search tools; keep raw file dumps out\n"
            "   of context by searching for evidence, not by reading whole trees.\n")
        review_note = (
            "   Re-read the full diff in a clean context against the rule that\n"
            "   behavior must not change, and note that no reviewer sub-agent\n"
            "   was available.\n")

    record = (
        "   If a module disappeared or was renamed, update the module map in\n"
        "   the `GENERATED:project-context` section of AGENTS.md. Append any\n"
        "   durable finding to `.ai/notes.md`, for example a subsystem that\n"
        "   turned out to be unreachable.\n")

    return render.fill("skills/bodies/tidy-up.md",
                       arg=arg,
                       record=record,
                       review_note=review_note,
                       survey_note=survey_note)

def command_specs(harness: str, arg_focus: str, arg_ticket: str) -> list:
    """(name, description, body) for each command, in roster order.

    Each name resolves either to a template under templates/skills/ or to a
    composed body in COMPOSED_BODIES (those two vary on harness beyond simple
    slot filling). The description is the template's `description:`
    frontmatter line, kept next to the body it describes so the two cannot
    drift.
    """
    hook_offer = (render.load("skills/fragments/claude/hook-offer.md")
                  if harness == "claude" else "")
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
    "tidy-up": lambda harness, arg: render_tidy_up_body(harness, arg),
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

def render_tool_probe() -> str:
    """Deterministic repo inventory written into the scaffold. Static: the
    template is a real .py file under templates/tools/."""
    return render.load("tools/probe.py")

def render_settings_json() -> str:
    """Project settings (.claude/settings.json): a read-only permission allow
    list so exploration runs without a prompt per command, plus the Stop hook
    that enforces the .ai commit rule deterministically. Compound commands
    (a && b) prompt unless every part of the chain matches a rule, so common
    chain members (cd, echo, pwd, read-only git) are included as well."""
    allow = render.sectioned_list("config/permissions.txt",
                                  sections=("shared",), tools_dir=TOOLS_DIR)
    hooks = {
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
