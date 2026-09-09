#!/usr/bin/env python3
"""
init_agent.py - Scaffold a project-aware LLM agent (interactive, run in the
project root). The script only initializes; everything afterwards is done by
the agent through skills and folder conventions:

  /explore [focus]       sample the codebase; fill the AGENTS.md project
                         context and .ai/notes.md
  /spec <id> <title>     write .ai/changes/<id>/spec.md for a non-trivial
                         change (goal, acceptance criteria, task checklist)
  /build <id>            implement the spec's tasks, review the diff against
                         the criteria, finish
  /import-kb <source>    import an existing knowledge base of any structure:
                         read, classify, and distill it into the project
                         context + notes.md
  /import <source>       migrate an existing .ai/ folder (older framework
                         version or other layout) into the current structure:
                         knowledge and in-flight change specs
  /tidy-up [scope]       hygiene sweep that may not change behavior: remove
                         dead code, propose obsolete files for removal,
                         shorten overlong comments, drop em dashes from prose
  /framework-update      move the scaffold to the current framework version:
                         merge the framework files, retire what the framework
                         dropped, migrate hand-filled content into the new
                         shape. Never re-explores
  archive                no command: ask the agent to archive a finished
                         change; the rules live in AGENTS.md

Prompts: project name, one-line description, harness (claude/copilot/hermes).
Enter accepts the default; on an existing scaffold the defaults are what the
version stamp recorded, so Enter keeps the project as it is. The name and
description are recorded there because nothing else keeps them: /explore
overwrites the AGENTS.md section the description is seeded into. Pointing --harness at a different harness than the
one an existing scaffold was built for switches it: the new entry files are
written and the old ones the version stamp recorded are moved to
.ai/agent/.harness-backup/<old-harness>/ (moved, not deleted; files the stamp
never recorded are left alone and reported). It asks first unless -y is given. Non-TTY runs use the defaults unless overridden by
the flags below. If a scaffold already exists, init asks before overwriting
framework files; hand-filled content (notes, specs, the generated
project-context section) is always preserved, never reverted to stubs. To move
an existing scaffold to a newer framework version, run the agent's /framework-update
skill rather than re-running init: updating is a merge (keep user edits,
retire dropped files, migrate hand-filled content into a changed shape), and
merges need judgment this script does not have.

There is one profile. Framework 5.22 removed the large profile (KB manifest,
hot/cold nodes, INDEX, on-demand phase docs, deterministic KB tools, ticket
pipeline): the source is read on demand instead, knowledge lives in a dense
AGENTS.md plus .ai/notes.md, and each non-trivial change gets a lightweight
spec and one fresh-context review gate.

Context layout:
  AGENTS.md                    canonical instructions (vendor-neutral):
                               conventions, right-sizing rules, commands, and
                               the generated project-context section. Read
                               natively by Copilot and Hermes; imported via
                               CLAUDE.md for Claude Code
  CLAUDE.md (claude)           one-line pointer: @AGENTS.md
  .ai/notes.md                 running memory: gotchas, runbooks, unwritten
                               rules
  .ai/changes/<id>/spec.md     per-change spec: goal, acceptance criteria,
                               task checklist
  .ai/.current                 gitignored task cursor: cross-session resume
                               pointer (active change, files)
  .ai/agent/tools/probe.py     deterministic repo inventory, used by /explore
  .claude/skills/*/SKILL.md    Agent Skills (open standard)
  .agents/skills/*/SKILL.md    hermes harness: same content as project skills,
                               loaded once `hermes skills trust` has run in the
                               repo. /import is a hermes built-in, so it
                               ships as /import-agent there; every other
                               command has one name on every harness
  .github/prompts/*.prompt.md  copilot harness: same content as prompt files
  .claude/settings.json        permission allow list + Stop hook (claude only)
  .claude/hooks/*.py           hook scripts: remind about uncommitted .ai
                               changes
  .claude/agents/reviewer.md   fresh-context adversarial reviewer subagent

Versioning:
  .ai/ is excluded from the host project's repo (init appends it to the
  project .gitignore) and tracked in its own git repo at .ai/.git. init
  makes the first commit; afterwards the agent commits .ai changes itself
  (protocol rule in AGENTS.md, enforced by a Stop hook on claude).

Generated docs use two language registers (concept v5, CONCEPT.md section 8):
normative docs in plain imperative English, recorded knowledge (notes, specs)
telegraphic. Identifiers verbatim.

Usage:
  python init_agent.py        (or: init-agent)            interactive
  python init_agent.py --name foo --desc "..." --harness claude
  Flags: --name, --description/--desc, --harness {claude,copilot,hermes},
  -y/--yes (overwrite framework files without prompting).
  Any omitted value is prompted for, or uses its default on a non-TTY.

  Two flags exist only to serve the agent's /framework-update skill, which is
  how an existing scaffold moves to a newer framework version:
  --detect                print this directory's scaffold stamp as JSON
                          (harness, framework version, project name and
                          description, file list)
  --emit-reference DIR    render a pristine scaffold of the current framework
                          into DIR, with no git or host-project side effects,
                          as the comparison target /framework-update diffs against
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from agentgen import content, render, scaffold
from agentgen.const import *  # noqa: F403
from agentgen.content import *  # noqa: F403
from agentgen.scaffold import *  # noqa: F403

try:
    # Enables arrow keys / line editing in input() prompts (ask()).
    import readline  # noqa: F401
except ImportError:
    pass  # not available on all platforms (e.g. Windows); plain input then


def ask(text: str, default: str = "") -> str:
    """Interactive prompt with default. Returns the default without prompting
    when stdin is not a terminal (scripted/CI use)."""
    if not sys.stdin.isatty():
        return default
    suffix = f" [{default}]" if default else " (Enter to skip)"
    try:
        return input(f"{text}{suffix}: ").strip() or default
    except EOFError:
        return default

def ask_choice(text: str, options: list, default: str) -> str:
    """Numbered selection prompt: pick by number or name, Enter = default.
    Returns the default without prompting when stdin is not a terminal."""
    if not sys.stdin.isatty():
        return default
    print(f"{text}:")
    for i, opt in enumerate(options, 1):
        mark = "  (default)" if opt == default else ""
        print(f"  {i}) {opt}{mark}")
    while True:
        try:
            raw = input(f"Select [Enter = {default}]: ").strip().lower()
        except EOFError:
            return default
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print(f"  invalid choice: {raw}")

def write_debug_probe(root: Path) -> None:
    """--debug-probe: run the freshly scaffolded probe.py and drop its report
    as PROBE.md in the current directory, so the inventory can be inspected
    without running /explore. Plain debug artifact, not a scaffold file."""
    probe = root / TOOLS_DIR / "probe.py"
    try:
        r = subprocess.run([sys.executable, str(probe)],
                           capture_output=True, text=True, cwd=str(root))
    except OSError as e:
        print(f"warning: --debug-probe failed to run probe.py: {e}")
        return
    if r.returncode != 0 or not r.stdout.strip():
        print("warning: --debug-probe: probe.py failed: "
              + (r.stderr.strip() or f"exit {r.returncode}"))
        return
    (root / "PROBE.md").write_text(r.stdout, encoding="utf-8")
    print("wrote PROBE.md (debug inventory; delete or gitignore it)")

def cmd_detect(root: Path) -> int:
    """--detect: describe the scaffold in this directory as JSON, for the
    /framework-update skill. Prefers the recorded framework.json (authoritative: it also
    lists the framework files that version emitted); falls back to inspecting
    the tree for scaffolds built before the stamp existed."""
    stamp = root / FRAMEWORK_JSON
    if stamp.exists():
        try:
            print(stamp.read_text(encoding="utf-8").rstrip())
            return 0
        except OSError:
            pass
    detected = detect_scaffold(root)
    if detected is None:
        print("No agent scaffold found in this directory.", file=sys.stderr)
        return 1
    size, harness, name = detected
    print(json.dumps({
        "framework_version": None,   # predates the stamp
        "profile": size,
        "harness": harness,
        "project": name,
        "generated": None,
        "framework_files": [],       # unknown: nothing to retire from
    }, indent=2))
    return 0

def cmd_emit_reference(target: str, args) -> int:
    """--emit-reference DIR: render a pristine scaffold into DIR and stop.
    No git init, no gitignore edits, no commits, no host-project side effects.
    This is the comparison target the /framework-update skill diffs a real project
    against, so it must be a plain render of the current framework."""
    dest = Path(target).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"error: --emit-reference target is not empty: {dest}",
              file=sys.stderr)
        return 1
    harness = args.harness or "claude"
    name = args.name if args.name is not None else "reference"
    desc = args.description if args.description is not None else ""
    dest.mkdir(parents=True, exist_ok=True)
    rc = scaffold(dest, name, desc, harness, True, reference=True)
    if rc == 0:
        print(f"reference {harness} scaffold "
              f"(framework {FRAMEWORK_VERSION}) rendered to {dest}")
    return rc

def cmd_init(args=None) -> int:
    root = Path.cwd()

    if args and getattr(args, "detect", False):
        return cmd_detect(root)
    if args and getattr(args, "emit_reference", None):
        return cmd_emit_reference(args.emit_reference, args)
    if args and getattr(args, "bootstrap_update", False):
        return bootstrap_update(root)

    marker = root / "AGENTS.md"

    # What a previous run recorded, read before prompting: a re-init that
    # cannot see it falls back to the directory name and an empty description,
    # which silently renames the project and drops its one-liner. The stamp is
    # the only place either survives, since /explore overwrites the AGENTS.md
    # section the description was seeded into.
    previous = read_stamp(root) if marker.exists() else None
    if previous is None and marker.exists():
        detected = detect_scaffold(root)
        previous = {"harness": detected[1], "project": detected[2]} if detected \
            else None
    prev = previous or {}

    name = (args.name if args and args.name is not None
            else ask("Project name", prev.get("project") or root.name))
    desc = (args.description if args and args.description is not None
            else ask("Project description, one line",
                     prev.get("description") or ""))
    harness = (args.harness if args and args.harness
               else ask_choice("Harness", ["claude", "copilot", "hermes"],
                               prev.get("harness") or "claude"))

    force = bool(args and args.yes)

    # A harness switch is an init, not an update: the entry files are pure
    # framework output with nothing to merge, so the generator owns the move.
    # What it must not do is write the new set and leave the old one live.
    switch_from = None
    if marker.exists():
        if previous and previous.get("harness") not in (None, harness):
            switch_from = previous
            old_harness = previous["harness"]
            if not force:
                print(f"This scaffold is set up for the {old_harness} harness.")
                print(f"Switching to {harness} regenerates the framework files "
                      f"and retires the {old_harness}\nentry files it recorded "
                      f"into {HARNESS_BACKUP_DIR}/{old_harness}/ (moved, not "
                      "deleted).\nNotes, specs and the project context are "
                      "preserved.")
                answer = ask(f"Switch harness {old_harness} -> {harness}? "
                             "(y/N)", "n")
                if answer.lower() not in ("y", "yes"):
                    print(f"Aborted; nothing was written. Re-run with "
                          f"--harness {old_harness} to keep the current one.",
                          file=sys.stderr)
                    return 1
            # A switch has to regenerate: AGENTS.md, and every skill body that
            # names a renamed command, describe the harness they were built
            # for. Skipping them as "exists" would leave the scaffold talking
            # about the harness it just moved off.
            force = True

    if marker.exists() and not force:
        answer = ask("Scaffold exists. Overwrite regenerates framework files "
                     "(instructions, skills, hooks, settings); hand-filled "
                     "content (notes, specs) is preserved either way. "
                     "Overwrite? (y/N)", "n")
        force = answer.lower() in ("y", "yes")

    rc = scaffold(root, name, desc, harness, force, switch_from=switch_from)
    if rc == 0 and args and getattr(args, "debug_probe", False):
        write_debug_probe(root)
    return rc

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", help="project name (skip the prompt)")
    ap.add_argument("--description", "--desc", dest="description",
                    help="one-line project description (skip the prompt)")
    ap.add_argument("--size", choices=["small"],
                    help=argparse.SUPPRESS)   # accepted so /framework-update skill
                                              # bodies written before 5.22
                                              # keep working; there is only
                                              # one profile now
    ap.add_argument("--harness", choices=["claude", "copilot", "hermes"],
                    help="target harness (skip the prompt); default claude. "
                         "On an existing scaffold built for a different "
                         "harness this switches it: the new entry files are "
                         "written and the old ones the version stamp recorded "
                         "are moved to .ai/agent/.harness-backup/<old>/. "
                         "Confirmed interactively unless -y is given")
    ap.add_argument("-y", "--yes", action="store_true",
                    help="overwrite framework files without prompting")
    ap.add_argument("--detect", action="store_true",
                    help="print this directory's scaffold stamp as JSON "
                         "(profile, harness, framework version, framework "
                         "file list) and exit; used by the /framework-update skill")
    ap.add_argument("--emit-reference", metavar="DIR",
                    help="render a pristine scaffold of the current framework "
                         "into DIR (must be empty or absent) and exit, with "
                         "no git or host-project side effects. The comparison "
                         "target for the /framework-update skill; use --harness to "
                         "match the project being updated")
    ap.add_argument("--bootstrap-update", action="store_true",
                    help="deliver the /framework-update skill into an existing scaffold "
                         "that predates it, and nothing else. Profile and "
                         "harness are detected, never prompted. Use this "
                         "instead of re-running init on an existing scaffold: "
                         "init overwrites whole files and would discard rules "
                         "appended to AGENTS.md and permissions added to "
                         "settings.json. Afterwards run /framework-update in the project")
    ap.add_argument("--debug-probe", action="store_true",
                    help="after scaffolding, run the generated probe.py and "
                         "write its report to PROBE.md in the current "
                         "directory (inspection aid, not part of the "
                         "scaffold; delete or gitignore it)")
    return cmd_init(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
