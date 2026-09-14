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

def render_framework_json(root: Path, name: str, harness: str,
                          desc: str = "") -> str:
    """The scaffold's version stamp: which framework revision built it, under
    which harness, for which project, and every framework-owned path it
    emitted. /framework-update reads this to know what to compare, migrate, and retire;
    without it an update can only overwrite blindly. Call after all other
    writes.

    `project` and `description` are the two answers the user gave at init.
    They are recorded because nothing else keeps them: the description is
    seeded into the project-context section of AGENTS.md and /explore
    overwrites that section with what it found, so by the first update the
    original one-liner is gone. Anything that re-renders this scaffold later
    (an update's reference, a harness switch) would otherwise have to invent
    both, and would rename the project to its directory name.

    `profile` is still recorded, always "small". Framework 5.22 removed the
    large profile, and the field is what lets /framework-update recognize a scaffold
    stamped `"large"` as predating that and stop instead of guessing."""
    files = sorted({str(p.relative_to(root)) for p in _framework_paths}
                   | {FRAMEWORK_JSON})
    return json.dumps({
        "framework_version": FRAMEWORK_VERSION,
        "profile": "small",
        "harness": harness,
        "project": name,
        "description": desc,
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
    (per-checkout session state, not shared knowledge), and the two rescue
    copies of host-repo framework files, from /framework-update and from a harness
    switch (throwaway snapshots, not history - the `.ai` repo already versions
    everything it owns)."""
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return
    gi = ai_dir / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    have = {line.strip().rstrip("/") for line in lines}
    add = [e for e in ("external/", ".current", "agent/.update-backup/",
                       "agent/.harness-backup/")
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

def read_stamp(root: Path):
    """The scaffold's recorded version stamp as a dict, or None if this
    directory has none or it is unreadable."""
    stamp = root / FRAMEWORK_JSON
    if not stamp.exists():
        return None
    try:
        recorded = json.loads(stamp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return recorded if isinstance(recorded, dict) else None

def retire_harness_files(root: Path, previous: dict, old_harness: str) -> tuple:
    """Move the previous harness's entry files out of the way after a switch.

    Left in place they keep answering the same slash commands out of a
    document AGENTS.md no longer describes, which is the failure this exists
    to prevent: two live command sets disagreeing about the protocol.

    Only files the stamp actually recorded are retired. Anything the user put
    next to them is theirs, stays, and is reported instead, because the
    generator cannot tell a hand-written skill from one it forgot it wrote and
    guessing wrong costs the user work.

    They are moved to `.ai/agent/.harness-backup/<old-harness>/`, not deleted.
    The realistic loss is a `.claude/settings.json` carrying hand-added
    permissions, and a move is recoverable where a delete is not.

    Returns (retired, left_behind, backup_dir): paths relative to root.
    """
    recorded = previous.get("framework_files") or []
    written = {str(p.relative_to(root)) for p in _framework_paths}
    backup = root / HARNESS_BACKUP_DIR / old_harness
    retired = []
    for rel in sorted(set(recorded) - written - {FRAMEWORK_JSON}):
        src = root / rel
        if not src.is_file():
            continue
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        retired.append(rel)
    _prune_empty_dirs(root, retired)

    left = []
    for entry in HARNESS_ENTRY_PATHS.get(old_harness, []):
        path = root / entry
        if path.is_file():
            left.append(entry)
        elif path.is_dir():
            left += sorted(str(f.relative_to(root)) for f in path.rglob("*")
                           if f.is_file())
    return retired, left, Path(HARNESS_BACKUP_DIR) / old_harness

def _prune_empty_dirs(root: Path, moved: list):
    """Remove directories a retirement emptied, deepest first. Only ever
    removes a directory that has nothing left in it, so a user file anywhere
    under it keeps the whole chain."""
    parents = {(root / rel).parent for rel in moved}
    for path in sorted(parents, key=lambda p: len(p.parts), reverse=True):
        while path != root and path.is_dir() and not any(path.iterdir()):
            path.rmdir()
            path = path.parent

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
    """Deliver the /framework-update skill into a scaffold that predates it,
    and nothing else.

    The chicken-and-egg this solves: updating is a merge and belongs to the
    agent (CONCEPT.md section 24), but a scaffold built before v5.14 has no
    update skill to run, and re-running init is not an alternative. Init
    overwrites whole files, so on an existing scaffold it destroys
    project-specific rules appended to AGENTS.md and permissions added to
    settings.json, and it cannot retire anything.

    Writing only the skill file is safe because skill files are entirely
    framework-owned: no GENERATED region, no user-edited part, nothing to
    merge. Every other framework file is left exactly as it is, for /framework-update
    to merge properly on its first run.

    The stamp this writes deliberately records `framework_version: null` and
    an empty file list. Claiming the current version would tell /framework-update the
    project is already up to date, and would leave it with the current file
    list, so nothing would ever be classified as retired. Null is the honest
    value and is the case /framework-update's preflight already handles: profile,
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
                  f"an update skill already.\nRun /framework-update in "
                  f"the project instead.",
                  file=sys.stderr)
            return 1

    if size == "large":
        print("This is a large-profile scaffold, and framework 5.22 removed "
              "the large profile.\nThere is no update path across that "
              "boundary: scaffold fresh with init-agent\nand carry the "
              "knowledge over with /import.", file=sys.stderr)
        return 1

    specs = content.command_specs(harness, "$ARGUMENTS", "$ARGUMENTS")
    cmd = "framework-update"
    update_spec = [s for s in specs if s[0] == cmd]
    if not update_spec:
        print(f"error: this generator emits no /{cmd} skill.", file=sys.stderr)
        return 1

    if harness == "claude":
        rel = Path(".claude") / "skills" / cmd / "SKILL.md"
        body = content.render_skills(update_spec)[f"{cmd}/SKILL.md"]
    elif harness == "hermes":
        rel = Path(HERMES_SKILLS_DIR) / cmd / "SKILL.md"
        body = content.render_hermes_skills(update_spec)[f"{cmd}/SKILL.md"]
    else:
        rel = Path(".github") / "prompts" / f"{cmd}.prompt.md"
        body = content.render_prompt_files(update_spec)[f"{cmd}.prompt.md"]

    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")

    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps({
        "framework_version": None,   # unknown: this scaffold predates the stamp
        "profile": "small",
        "harness": harness,
        "project": name,
        "description": None,   # unrecoverable: /explore overwrote the seed
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
        print(f"  /{cmd}")
    elif harness == "hermes":
        print("  hermes skills trust     (once, in this repository)")
        print(f"  /{cmd}")
    else:
        # Prompt files are a VS Code feature. Copilot CLI does not read
        # .github/prompts/ at all, so it needs the kickoff sentence instead.
        print(f"  VS Code (Copilot Chat):  /{cmd}")
        print("  Copilot CLI:             Update the framework: read "
              f"{rel} first and follow it exactly.")
    return 0


def scaffold(root: Path, name: str, desc: str, harness: str,
             force: bool, commit_message: str = None,
             reference: bool = False, switch_from: dict = None) -> int:
    """Write the scaffold: a dense AGENTS.md, running notes, per-change specs,
    one deterministic inventory tool, and the harness entry files. `.ai/` is a
    private nested repo (notes + specs); AGENTS.md and the harness directory
    live in the host repo.

    `switch_from` is the previous version stamp when this run changes the
    scaffold's harness. The new harness's files are written normally; the old
    harness's recorded files are then retired, which is the whole difference
    between switching and layering a second command set on top of the first."""
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

    # Retire before the stamp: the stamp must record only what is now live,
    # and the retirement reads the paths this run wrote.
    retired, left_behind, backup = [], [], None
    if switch_from:
        retired, left_behind, backup = retire_harness_files(
            root, switch_from, switch_from.get("harness"))

    # Version stamp last: it records every framework path written above.
    write(root / FRAMEWORK_JSON,
          render_framework_json(root, name, harness, desc),
          force, created, skipped)

    if reference:
        return 0

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    if switch_from:
        commit_message = commit_message or (
            f"init: switch harness {switch_from.get('harness')} -> {harness}")
    ai_commit(root, commit_message or f"init: scaffold ({name})")

    report(root, created, skipped, preserved)
    for rel in retired:
        print(f"retired   {rel} (moved to {backup}/)")
    if switch_from:
        old_harness = switch_from.get("harness")
        print(f"\nSwitched harness: {old_harness} -> {harness}.")
        if retired:
            print(f"The {old_harness} entry files are in {backup}/; delete "
                  "that directory once you are\nsatisfied with the switch.")
        elif switch_from.get("framework_files"):
            print(f"Nothing to retire: no recorded {old_harness} file was "
                  "still present.")
        else:
            print(f"This scaffold recorded no file list, so no {old_harness} "
                  "file could be retired\nsafely. Remove them by hand: "
                  + ", ".join(HARNESS_ENTRY_PATHS.get(old_harness, [])) + ".")
        if left_behind:
            print(f"\nLeft in place under the old harness (not framework-"
                  "owned, so yours to keep or\nremove): "
                  + ", ".join(left_behind))
    entry = {"claude": ".claude", "hermes": HERMES_SKILLS_DIR}.get(
        harness, ".github/prompts")
    print(f"\n.ai: notes.md + changes/  |  AGENTS.md + {entry}"
          f"  |  project: {name}  |  harness: {harness}")
    if harness == "hermes":
        print(f"\nSkills live in {HERMES_SKILLS_DIR}/. Hermes loads project "
              "skills only from a trusted repo:")
        print("  hermes skills trust     (once, in this repository)")
        print("  /reload-skills          (in a running session)")
        print("Renamed to clear a hermes built-in: /framework-update.")
    if harness == "copilot":
        print("\nPrompt files (/explore, /spec, /build) work in VS Code only.")
        print("Copilot CLI reads AGENTS.md; state the workflow intent directly:")
        print("  Explore the project and fill the Project Context + .ai/notes.md.")
        print('  Spec change <id> "<title>": write .ai/changes/<id>/spec.md.')
        print("  Build change <id>: implement the spec, then review the diff.")
    return 0
