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
    if harness == "opencode":
        return f"exposed as commands under `{OPENCODE_DIR}/commands/`"
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
    return render.fill("instructions/agents.md",
                       ask_tool=ASK_TOOL[harness],
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
    settings, hooks and skills on claude, prompt files and hooks on copilot,
    commands, config and the plugin on opencode, and where the reference's own copy of
    this skill sits.

    The migrate list is frozen into every project at the version it was
    scaffolded with, so a project running this skill never knows the
    migrations of the version it is moving to. The body therefore defers to
    the reference's copy, which does (CONCEPT.md section 40).
    """
    if harness == "claude":
        reference_skill = ".claude/skills/framework-update/SKILL.md"
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
    elif harness == "opencode":
        reference_skill = f"{OPENCODE_DIR}/commands/framework-update.md"
        backup_paths = f"AGENTS.md and `{OPENCODE_DIR}/`"
        merge_cases = (
            f"     - `{OPENCODE_DIR}/opencode.json`: permission rules and other\n"
            "       settings a user added are not framework state. Union them\n"
            "       with the reference's; drop only rules the reference retired.\n"
            f"     - `{OPENCODE_DIR}/plugins/llm-agent.js`: a hook a user added\n"
            "       here, such as a lint gate, is not framework state. Keep it.\n"
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            "     - commands, agents or plugins present here but not in the\n"
            "       reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = (
            f"   - `{OPENCODE_DIR}/opencode.json` parses as JSON, and the two\n"
            f"     scripts under `{OPENCODE_DIR}/hooks/` that\n"
            f"     `{OPENCODE_DIR}/plugins/llm-agent.js` runs exist.\n")
    else:
        reference_skill = ".github/prompts/framework-update.prompt.md"
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

    # Step 0's hand-off (CONCEPT.md sections 64 and 68): the harness's
    # sub-agent by default, a Herdr tab when the user asks for `herdr`.
    update_prompt = {
        "claude": "/framework-update inline",
        "copilot": ("Run framework-update inline: read "
                    f"{UPDATE_FILES[harness]} and follow it."),
        # OpenCode's tab spawns the updater as a sub-agent (herdr_tab), and
        # a sub-agent's prompt cannot be a slash command.
        "opencode": "Run the framework update inline.",
    }[harness]
    handoff = (
        "   - By default, spawn a fresh `updater` sub-agent, passing no\n"
        "     model (its file names one), with the prompt `Run the framework\n"
        "     update inline.` (`Run the framework update inline, dry-run.`\n"
        "     with `dry-run`).\n"
        + "\n".join("   " + ln if ln else ln for ln in herdr_tab(
            harness, "updater", "update-<hhmmss>", update_prompt
        ).split("\n")).rstrip(" ") +
        "     `<hhmmss>` is the current time. Add `dry-run` to the prompt\n"
        "     when the user gave it; read the updater's last line with\n"
        "     `herdr agent read update-<hhmmss> --source recent-unwrapped\n"
        "     --lines 80`.\n")

    owned = ("`.ai/notes.md`, `.ai/notes/<topic>.md`, task files under\n"
             "`.ai/tasks/` (change specs under `.ai/changes/` before 8.0), and\n"
             "the `GENERATED:project-context` section of AGENTS.md")
    migrate = (
        "   - Framework 9.0 folds `/task-create`, `/task-do` and\n"
        "     `/task-list-all` into one `/task` (`create`, `do`, `list`). The\n"
        "     three old skill entries are retired framework files: delete\n"
        "     them through the recorded file list. Task files under\n"
        "     `.ai/tasks/` keep their format; nothing there changes.\n"
        "   - Framework 8.0 replaces `/spec` and `/build` with typed task\n"
        "     commands (since 9.0 the one `/task`), and change specs with\n"
        "     typed task files. The old skill entries are retired framework\n"
        "     files; the specs are hand-filled content, so migrate them, do\n"
        "     not regenerate them:\n"
        "     - `git -C .ai mv changes tasks`. If `tasks/` exists already,\n"
        "       move each directory under `changes/` into it instead, and\n"
        "       the contents of `changes/_archive/` into `tasks/_archive/`.\n"
        "       Then in every task directory, `_archive/` included,\n"
        "       `git -C .ai mv` its `spec.md` to `task.md`.\n"
        "     - In each file's frontmatter add `type: change` after `title`\n"
        "       and `updated:` with the `created` date. Rename the heading\n"
        "       `## Acceptance criteria` to `## Done when` and `## Tasks` to\n"
        "       `## Steps`, and add empty `## Findings` and `## Outcome`\n"
        "       sections before `## Notes`. Keep every goal, criterion,\n"
        "       task line, and checkbox state exactly as written.\n"
        "     - If `.ai/.current` names a spec, rewrite it to start with\n"
        "       `task: <id>` and point at the moved `task.md`.\n"
        f"     - Run `python3 {TOOLS_DIR}/tasks.py`: every migrated spec\n"
        "       must appear in the table with type `change`.\n"
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
        "   - A changed task format: bring existing `.ai/tasks/<id>/task.md`\n"
        "     files up to it, keeping every goal, criterion, step, and\n"
        "     finding intact.\n"
        "   - Moved or renamed directories: `git mv` inside `.ai` so the notes\n"
        "     history survives the move.\n")

    return render.fill("skills/bodies/update.md",
                       arg=arg,
                       backup_paths=backup_paths,
                       framework_json=FRAMEWORK_JSON,
                       handoff=handoff,
                       harness=harness,
                       merge_cases=merge_cases,
                       migrate=migrate,
                       owned=owned,
                       reference_skill=reference_skill,
                       updater_file=AGENT_FILES[harness]["updater"],
                       verify_extra=verify_extra,
                       verify_tools=(f"`{TOOLS_DIR}/probe.py` and "
                                     f"`{TOOLS_DIR}/tasks.py`"))

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
            body = render.render(body, tools_dir=TOOLS_DIR, task_dir=TASK_DIR,
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
            f"effort: {SKILL_EFFORT[name]}\n"
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

def render_opencode_commands(specs) -> dict:
    """OpenCode commands: .opencode/commands/<name>.md. The filename is the
    command, `$ARGUMENTS` the argument string. Only a user can run a command,
    so nothing like `disable-model-invocation` is needed. `specs` is a
    command_specs list."""
    out = {}
    for name, desc, body in specs:
        out[f"{name}.md"] = f'---\ndescription: "{desc}"\n---\n{body}'
    return out

def render_reviewer_agent() -> str:
    """The fresh-context adversarial reviewer used by /task do's review
    gate. A task's result is a diff, an Outcome, or both, so the reviewer
    checks whichever the task produced."""
    return render.fill(
        "agents/reviewer.md",
        coverage=("- Every Done-when criterion is met and covered by the check "
                  "that fits it,\n  in the diff or as a result recorded in "
                  "Findings: a test for logic, its\n  linter or validator "
                  "for a declarative file.\n"
                  "- Every claim in Outcome cites evidence in Findings, the "
                  "evidence was\n  produced in this task rather than "
                  "inferred, and the answer fits the\n  question in Goal. "
                  "An unsupported claim is a gap even if it sounds right.\n"
                  "- Every file-and-line citation the Outcome rests on "
                  "holds: open it and\n  confirm the source says what the "
                  "claim says. Spot-check up to three\n  citations in "
                  "Findings that the Outcome does not use."),
        desc=("Adversarial fresh-context review of a task's result (diff, "
              "Outcome, or both) against its Done-when criteria. Use for "
              "the review gate in /task do."),
        max_turns=ROLE_TURNS["reviewer"],
        input_block=("Input: the task file `.ai/tasks/<id>/task.md` (Goal, "
                     "Done when, Findings,\nOutcome) plus the code diff, "
                     "if the task changed code, and\n"
                     "`.ai/tasks/<id>/evidence.md` where a finding points "
                     "at it."))

def render_opencode_reviewer() -> str:
    """The same reviewer as an OpenCode V2 agent: a sub-agent by frontmatter,
    with edits denied where the claude agent lists its read-only tools."""
    desc, body = _split_frontmatter(render_reviewer_agent())
    return ("---\n"
            f'description: "{desc}"\n'
            "mode: subagent\n"
            f"steps: {ROLE_TURNS['reviewer']}\n"
            "permissions:\n"
            '  - { action: edit, resource: "*", effect: deny }\n'
            "---\n"
            f"{body}")

def render_worker_agent() -> str:
    """The worker sub-agent of /task do (CONCEPT.md section 56). It carries no
    `model:` line: a user may add one, and without one the
    harness default applies. Its body only points at
    work.md, the worker's contract, which stays harness-neutral."""
    return render.fill(
        "agents/worker.md",
        desc=("Works the steps of a task for /task do, which supervises it. "
              "Spawned by /task do and by init-agent's model check only."),
        max_turns=ROLE_TURNS["worker"], task_dir=TASK_DIR)

def render_opencode_worker() -> str:
    """The worker as an OpenCode V2 sub-agent, with the default permissions
    of a sub-agent: it edits, runs the tests and commits."""
    desc, body = _split_frontmatter(render_worker_agent())
    return (f'---\ndescription: "{desc}"\nmode: subagent\n'
            f"steps: {ROLE_TURNS['worker']}\n---\n{body}")

def render_updater_agent(harness: str) -> str:
    """The updater sub-agent /framework-update hands the update to (CONCEPT.md
    section 64). Like the other roles it carries no `model:` line until
    `init-agent --models` writes one. Its body points at the harness's own
    copy of the update command, which is the contract."""
    return render.fill(
        "agents/updater.md",
        desc=("Runs this project's framework update for /framework-update, "
              "which hands it over and checks the result. Spawned by "
              "/framework-update and by init-agent's model check only."),
        max_turns=ROLE_TURNS["updater"], update_file=UPDATE_FILES[harness])

def render_opencode_updater() -> str:
    """The updater as an OpenCode V2 sub-agent: it edits and commits `.ai`."""
    desc, body = _split_frontmatter(render_updater_agent("opencode"))
    return (f'---\ndescription: "{desc}"\nmode: subagent\n'
            f"steps: {ROLE_TURNS['updater']}\n---\n{body}")

def render_copilot_agent(which: str) -> str:
    """worker, reviewer or updater as a Copilot custom agent (.github/agents/
    <name>.agent.md). `description` is the one required key; the reviewer
    gets the read-only tool aliases plus the shell, its tools on claude."""
    source = {"worker": render_worker_agent,
              "reviewer": render_reviewer_agent,
              "updater": lambda: render_updater_agent("copilot")}[which]()
    desc, body = _split_frontmatter(source)
    tools = ('tools: ["read", "search", "execute"]\n'
             if which == "reviewer" else "")
    return (f'---\nname: {which}\ndescription: "{desc}"\n{tools}---\n'
            f"{body}")

def render_opencode_plugin() -> str:
    return render.load("hooks/opencode_plugin.js")

def render_hook_ai_repo_clean() -> str:
    return render.load("hooks/ai_repo_clean.py")

def render_hook_git_guard() -> str:
    return render.load("hooks/git_guard.py")

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

# Where a delegated role runs (CONCEPT.md section 68): the harness's own
# sub-agent by default, a Herdr tab when the user asks for `herdr`. The tab
# starts the harness's CLI on the role's model: `claude --agent <role>` was
# seen to run on the agent file's model (section 64); Copilot takes the
# file's `model:` line through `--model` (its help, 1.0.105 and 1.0.107).
# OpenCode's TUI has no model flag (2.2.5 answers `--model` with its usage
# text), so its tab starts plain and the prompt has that session spawn the
# role as its sub-agent, which runs on the agent file's model and is
# continued by session id (seen live, section 70).
HERDR_START = {
    "claude": ("claude", "--agent {role} --permission-mode <mode>",
               "`--agent {role}` runs that session on the {role}'s model;\n"
               "  `<mode>` is your own permission mode, left out when you\n"
               "  cannot tell."),
    "copilot": ("copilot", "--agent {role} --model <model>",
                "`<model>` is the `model:` line of `{file}`,\n"
                "  as written."),
    "opencode": ("opencode", "",
                 "OpenCode's own session in the tab only passes the prompt\n"
                 "  on: the {role} runs as its sub-agent, on the `model:` line\n"
                 "  of `{file}`."),
}

# What the tab is told. OpenCode's wraps the role's prompt in a spawn; to go
# on after a report it continues that sub-agent instead of starting one.
HERDR_PROMPT = {
    "opencode": ("Use the subagent tool with agent {role} and this prompt, "
                 "then print its last line: {prompt}"),
}
HERDR_CONTINUE = {
    "opencode": ("Continue the same {role} sub-agent with this prompt, then "
                 "print its last line: {prompt}"),
}


def herdr_prompt(harness: str, role: str, prompt: str, again=False) -> str:
    """The text `herdr agent prompt` sends for a role's prompt."""
    wrap = (HERDR_CONTINUE if again else HERDR_PROMPT).get(harness, "{prompt}")
    return wrap.format(role=role, prompt=prompt)

def herdr_tab(harness: str, role: str, name: str, prompt: str) -> str:
    """The Herdr-tab bullet for a role, indented as a list item."""
    kind, args, note = HERDR_START[harness]
    fmt = dict(role=role, file=AGENT_FILES[harness][role])
    return (
        "- When the user asked for `herdr`: if Herdr runs (`HERDR_ENV` is 1\n"
        "  and `herdr` is on PATH), it gets a tab of its own and you touch\n"
        "  no other tab; otherwise say so in one line and use the sub-agent.\n"
        "\n"
        "      herdr tab create --workspace \"$HERDR_WORKSPACE_ID\" \\\n"
        "        --cwd \"$PWD\" --label " + name + " --no-focus \\\n"
        "        | jq -r '.result.root_pane.pane_id'\n"
        "      herdr agent start " + name + " --kind " + kind +
        " --pane <pane>" +
        (" \\\n        -- " + args.format(**fmt) if args else "") + "\n"
        "      herdr agent prompt " + name + " \"" +
        herdr_prompt(harness, role, prompt) + "\"\n"
        "      herdr agent wait " + name + " --timeout 540000\n"
        "\n"
        "  " + note.format(**fmt) + "\n"
        "  Write every value in literally: `<pane>` is the id the first\n"
        "  command prints, and no shell variable survives from one command\n"
        "  to the next. Repeat the wait while it is `working`. A `blocked`\n"
        "  tab is a question or a permission prompt: show the user, and\n"
        "  never answer a permission prompt yourself. Leave the tab open\n"
        "  when it is done.\n")

def render_task_part(part: str, harness: str = "claude") -> str:
    """`/task`'s Create, Do, Work or Steps body (`create`, `do`, `work`,
    `steps`), written to TASK_DIR. Create and Do are read by the dispatching
    skill only when `tasks.py resolve` sends it there; Work is read by the
    worker Do hands its steps to (CONCEPT.md sections 50 and 52); Steps is
    the working steps both the worker and a session working inline read
    (section 77).

    Do varies on harness in one place, the start of a worker tab when the
    user asks for `herdr` (section 68); the default is the harness's
    sub-agent everywhere."""
    rel = {"create": "task/create.md", "do": "task/do.md",
           "work": "task/work.md", "steps": "task/steps.md"}[part]
    placement = (
        "You are the supervisor in this\n"
        "session either way; only where the worker runs varies:\n"
        "- By default, spawn it as your harness's sub-agent with that\n"
        "  prompt, passing no model.\n"
        + herdr_tab(harness, "worker", "<name>", "<the prompt>") +
        "  `<name>` is `worker-` and the task id, lowercased, at most 32\n"
        "  characters. If a tab of that name is still open from an earlier\n"
        "  session, continue it instead of opening another. Its report is\n"
        "  the `Worker round` line in the task file; continue it with\n"
        "  `herdr agent prompt <name> \"" +
        herdr_prompt(harness, "worker",
                     "Read work.md again, then Findings, and go on.", True) +
        "\"`.\n")
    return render.fill(rel, tools_dir=TOOLS_DIR, task_dir=TASK_DIR,
                       ask_tool=ASK_TOOL[harness],
                       worker_placement=placement)

def render_tool_tasks() -> str:
    """The task table and create-or-do resolver behind /task. Static, like
    the probe: parsing frontmatter is deterministic work, so a script does
    it."""
    return render.load("tools/tasks.py")

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

def render_opencode_config() -> str:
    """Project config (.opencode/opencode.json): the permission list of the
    claude settings in OpenCode V2's form. OpenCode allows by default, so
    these rules matter when a user's global config asks about shell commands;
    they keep exploration free of prompts there. The plugin in
    .opencode/plugins/ is discovered by its location and needs no entry."""
    rules = []
    for entry in render.sectioned_list("config/permissions.txt",
                                       sections=("shared",),
                                       tools_dir=TOOLS_DIR):
        command = entry[len("Bash("):-len(":*)")]
        rules.append({"action": "shell", "resource": f"{command} *",
                      "effect": "allow"})
    return json.dumps({"permissions": rules}, indent=2) + "\n"
