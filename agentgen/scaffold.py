"""Writing a scaffold to disk.

Owns the file-level rules that make re-init safe: `write` records every
framework path for the version stamp, `write_owned` never reverts hand-filled
content to a stub, and `extract_generated` recovers the project-context
section so /explore output survives a regeneration.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from agentgen import content, render
from agentgen.const import *  # noqa: F403
from agentgen.content import *  # noqa: F403

_framework_paths: list = []

def write(path: Path, content: str, force: bool, created: list, skipped: list):
    """Framework-owned files (phase docs, skills, hooks, settings): the
    overwrite confirmation (force) regenerates them."""
    _framework_paths.append(path)
    if path.exists() and not force:
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)

def render_framework_json(root: Path, name: str, harness: str) -> str:
    """The scaffold's version stamp: which framework revision built it, under
    which harness, and every framework-owned path it emitted. /update reads
    this to know what to compare, migrate, and retire; without it an update
    can only overwrite blindly. Call after all other writes.

    `profile` is still recorded, always "small". Framework 5.22 removed the
    large profile, and the field is what lets /update recognize a scaffold
    stamped `"large"` as predating that and stop instead of guessing."""
    files = sorted({str(p.relative_to(root)) for p in _framework_paths}
                   | {FRAMEWORK_JSON})
    return json.dumps({
        "framework_version": FRAMEWORK_VERSION,
        "profile": "small",
        "harness": harness,
        "project": name,
        "generated": TODAY,
        "framework_files": files,
    }, indent=2) + "\n"

def write_owned(path: Path, stub: str, created: list, skipped: list,
                preserved: list):
    """Agent/user-owned content (notes, specs): write once. Existing content
    that differs from the stub is never overwritten, not even on
    overwrite-confirm; hand-filled knowledge must survive re-init."""
    if path.exists():
        if path.read_text(encoding="utf-8") == stub:
            skipped.append(path)
        else:
            preserved.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub, encoding="utf-8")
    created.append(path)

def extract_generated(root: Path) -> str:
    """Recover an existing GENERATED:project-context section so re-init never
    reverts Phase 1 output. Checks AGENTS.md first, then legacy locations."""
    for rel in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"):
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Marker text changed over versions; match on the stable prefix.
        begin = text.find("<!-- BEGIN GENERATED:project-context")
        if begin == -1:
            continue
        begin = text.find("-->", begin)
        end = text.find(GEN_END)
        if begin == -1 or end == -1 or end <= begin:
            continue
        body = text[begin + len("-->"):end].strip("\n")
        if body and "Populated in Phase 1" not in body:
            return body
    return None

def report(root: Path, created: list, skipped: list, preserved: list):
    for p in created:
        print(f"created   {p.relative_to(root)}")
    for p in skipped:
        print(f"skipped   {p.relative_to(root)} (exists)")
    for p in preserved:
        print(f"preserved {p.relative_to(root)} (hand-filled, not overwritten)")

def run_git(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)

def ensure_gitignore(root: Path):
    """Exclude .ai/ from the host project's repo (only if root is a git repo)."""
    if not (root / ".git").exists():
        return
    gitignore = root / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    if any(line.strip().lstrip("/").rstrip("/") == ".ai" for line in lines):
        return
    content = "\n".join(lines).rstrip("\n")
    content = (content + "\n" if content else "") + ".ai/\n"
    gitignore.write_text(content, encoding="utf-8")
    print(f"updated  {gitignore.relative_to(root)} (+ .ai/)")

def ensure_ai_gitignore(root: Path):
    """Keep volatile working state out of .ai's own repo: raw external copies
    (re-fetchable, would bloat KB history), the `.current` task cursor
    (per-checkout session state, not shared knowledge), and the /update
    rescue copy of the host-repo framework files (a throwaway snapshot, not
    history - the `.ai` repo already versions everything it owns)."""
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return
    gi = ai_dir / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    have = {line.strip().rstrip("/") for line in lines}
    add = [e for e in ("external/", ".current", "agent/.update-backup/")
           if e.rstrip("/") not in have]
    if not add:
        return
    content = "\n".join(lines).rstrip("\n")
    content = (content + "\n" if content else "") + "\n".join(add) + "\n"
    gi.write_text(content, encoding="utf-8")
    print(f"updated  .ai/.gitignore (+ {', '.join(add)})")

def ai_commit(root: Path, message: str):
    """Track .ai/ in its own repo; commit pending changes with message."""
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return
    if shutil.which("git") is None:
        print("warning: git not found; .ai changes not committed")
        return
    if not (ai_dir / ".git").exists():
        r = run_git(["init"], ai_dir)
        if r.returncode != 0:
            print(f"warning: git init failed in .ai: {r.stderr.strip()}")
            return
        print("initialized git repo in .ai/")
    run_git(["add", "-A"], ai_dir)
    if run_git(["diff", "--cached", "--quiet"], ai_dir).returncode == 0:
        return  # nothing staged
    r = run_git(["commit", "-m", message], ai_dir)
    if r.returncode != 0:
        print(f"warning: commit in .ai failed: {r.stderr.strip() or r.stdout.strip()}")
    else:
        print(f"committed in .ai: {message}")

def detect_scaffold(root: Path):
    """Inspect an existing scaffold and return (size, harness, name), or None
    if this directory has none. The fallback behind --detect, for scaffolds
    built before framework.json existed.

    size: 'large' when the KB manifest exists (a pre-5.22 scaffold, which this
          generator can no longer render), else 'small' when AGENTS.md does.
    harness: 'claude' when `.claude/` exists, else 'hermes' when
             `.agents/skills/` exists, else 'copilot' when
             `.github/prompts/` exists, else 'claude'.
    name: parsed from the AGENTS.md '# Agent: <name>' title, else the dir name.
    """
    agents = root / "AGENTS.md"
    if (root / ".ai" / "knowledgebase" / "manifest.yaml").exists():
        size = "large"
    elif agents.exists():
        size = "small"
    else:
        return None
    if (root / ".claude").exists():
        harness = "claude"
    elif (root / HERMES_SKILLS_DIR).exists():
        harness = "hermes"
    elif (root / ".github" / "prompts").exists():
        harness = "copilot"
    else:
        harness = "claude"
    name = root.name
    if agents.exists():
        for line in agents.read_text(encoding="utf-8",
                                     errors="replace").splitlines()[:3]:
            if line.startswith("# Agent:"):
                name = line.split(":", 1)[1].strip() or name
                break
    return size, harness, name

def bootstrap_update(root: Path) -> int:
    """Deliver the /update skill into a scaffold that predates it, and nothing
    else.

    The chicken-and-egg this solves: updating is a merge and belongs to the
    agent (CONCEPT.md section 24), but a scaffold built before v5.14 has no
    /update skill to run, and re-running init is not an alternative. Init
    overwrites whole files, so on an existing scaffold it destroys
    project-specific rules appended to AGENTS.md and permissions added to
    settings.json, and it cannot retire anything.

    Writing only the skill file is safe because skill files are entirely
    framework-owned: no GENERATED region, no user-edited part, nothing to
    merge. Every other framework file is left exactly as it is, for /update
    to merge properly on its first run.

    The stamp this writes deliberately records `framework_version: null` and
    an empty file list. Claiming the current version would tell /update the
    project is already up to date, and would leave it with the current file
    list, so nothing would ever be classified as retired. Null is the honest
    value and is the case /update's preflight already handles: profile,
    harness, and name are recorded so it need not re-detect them, and the
    version stays unknown so retirement falls to the orphan test.
    """
    detected = detect_scaffold(root)
    if detected is None:
        print("No agent scaffold found in this directory. Nothing to "
              "bootstrap; run init-agent to create one.", file=sys.stderr)
        return 1
    size, harness, name = detected

    stamp = root / FRAMEWORK_JSON
    if stamp.exists():
        try:
            recorded = json.loads(stamp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            recorded = {}
        if recorded.get("framework_version"):
            print(f"This scaffold is already stamped "
                  f"(framework {recorded['framework_version']}); it has "
                  f"/update already.\nRun /update in the project instead.",
                  file=sys.stderr)
            return 1

    if size == "large":
        print("This is a large-profile scaffold, and framework 5.22 removed "
              "the large profile.\nThere is no /update path across that "
              "boundary: scaffold fresh with init-agent\nand carry the "
              "knowledge over with /import.", file=sys.stderr)
        return 1

    specs = content.command_specs(harness, "$ARGUMENTS", "$ARGUMENTS")
    update_spec = [s for s in specs if s[0] == "update"]
    if not update_spec:
        print("error: this generator emits no /update skill.", file=sys.stderr)
        return 1

    if harness == "claude":
        rel = Path(".claude") / "skills" / "update" / "SKILL.md"
        body = content.render_skills(update_spec)["update/SKILL.md"]
    elif harness == "hermes":
        # Renamed: hermes reserves /update for a built-in command of its own.
        cmd = content.command_name("update", harness)
        rel = Path(HERMES_SKILLS_DIR) / cmd / "SKILL.md"
        body = content.render_hermes_skills(update_spec)[f"{cmd}/SKILL.md"]
    else:
        rel = Path(".github") / "prompts" / "update.prompt.md"
        body = content.render_prompt_files(update_spec)["update.prompt.md"]

    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")

    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps({
        "framework_version": None,   # unknown: this scaffold predates the stamp
        "profile": "small",
        "harness": harness,
        "project": name,
        "generated": None,
        "framework_files": [],       # unknown: nothing to retire from
        "bootstrapped": TODAY,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {rel}")
    print(f"wrote {FRAMEWORK_JSON} (version unknown: recorded harness "
          f"{harness} so the update need not re-detect it)")
    print("\nNothing else was touched. The agent does the merge; start it "
          "with:")
    if harness == "claude":
        print("  /update")
    elif harness == "hermes":
        print("  hermes skills trust     (once, in this repository)")
        print(f"  /{content.command_name('update', harness)}")
    else:
        # Prompt files are a VS Code feature. Copilot CLI does not read
        # .github/prompts/ at all, so it needs the kickoff sentence instead.
        print("  VS Code (Copilot Chat):  /update")
        print("  Copilot CLI:             Update the framework: read "
              f"{rel} first and follow it exactly.")
    return 0


def scaffold(root: Path, name: str, desc: str, harness: str,
             force: bool, commit_message: str = None,
             reference: bool = False) -> int:
    """Write the scaffold: a dense AGENTS.md, running notes, per-change specs,
    one deterministic inventory tool, and the harness entry files. `.ai/` is a
    private nested repo (notes + specs); AGENTS.md and the harness directory
    live in the host repo."""
    created, skipped, preserved = [], [], []
    _framework_paths.clear()

    archive = root / ".ai" / "changes" / "_archive"
    archive.mkdir(parents=True, exist_ok=True)
    if not any(archive.iterdir()):
        (archive / ".gitkeep").touch()

    # Agent/user-owned content: never clobbered once hand-filled.
    write_owned(root / ".ai" / "notes.md", render_notes_stub(),
                created, skipped, preserved)

    # Deterministic repo inventory, used at the start of /explore.
    write(root / TOOLS_DIR / "probe.py", render_tool_probe(),
          force, created, skipped)

    # AGENTS.md is framework-owned except its generated section: recover it
    # (also from legacy CLAUDE.md scaffolds) so re-init never reverts /explore.
    generated = extract_generated(root)
    write(root / "AGENTS.md",
          render_agents_md(name, desc, harness, generated),
          force, created, skipped)

    if harness == "claude":
        write(root / "CLAUDE.md", render_claude_pointer(), force, created, skipped)
        for rel, content in render_skills(
                command_specs(harness, "$ARGUMENTS", "$ARGUMENTS")).items():
            write(root / ".claude" / "skills" / rel, content,
                  force, created, skipped)
        write(root / ".claude" / "agents" / "reviewer.md",
              render_reviewer_agent(), force, created, skipped)
        write(root / ".claude" / "hooks" / "ai_repo_clean.py",
              render_hook_ai_repo_clean(), force, created, skipped)
        write(root / ".claude" / "settings.json",
              render_settings_json(), force, created, skipped)
    elif harness == "hermes":
        for rel, body in render_hermes_skills(
                command_specs(harness, HERMES_ARG_FOCUS,
                              HERMES_ARG_TICKET)).items():
            write(root / HERMES_SKILLS_DIR / rel, body,
                  force, created, skipped)
    else:
        for fname, content in render_prompt_files(
                command_specs(harness, "${input:focus}",
                              "${input:ticket}")).items():
            write(root / ".github" / "prompts" / fname, content,
                  force, created, skipped)

    # Version stamp last: it records every framework path written above.
    write(root / FRAMEWORK_JSON,
          render_framework_json(root, name, harness),
          force, created, skipped)

    if reference:
        return 0

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    ai_commit(root, commit_message or f"init: scaffold ({name})")

    report(root, created, skipped, preserved)
    entry = {"claude": ".claude", "hermes": HERMES_SKILLS_DIR}.get(
        harness, ".github/prompts")
    print(f"\n.ai: notes.md + changes/  |  AGENTS.md + {entry}"
          f"  |  project: {name}  |  harness: {harness}")
    if harness == "hermes":
        print(f"\nSkills live in {HERMES_SKILLS_DIR}/. Hermes loads project "
              "skills only from a trusted repo:")
        print("  hermes skills trust     (once, in this repository)")
        print("  /reload-skills          (in a running session)")
        print("Renamed to clear hermes built-ins: /import-agent, "
              "/framework-update.")
    if harness == "copilot":
        print("\nPrompt files (/explore, /spec, /build) work in VS Code only.")
        print("Copilot CLI reads AGENTS.md; state the workflow intent directly:")
        print("  Explore the project and fill the Project Context + .ai/notes.md.")
        print('  Spec change <id> "<title>": write .ai/changes/<id>/spec.md.')
        print("  Build change <id>: implement the spec, then review the diff.")
    return 0
