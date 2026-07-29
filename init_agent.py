#!/usr/bin/env python3
"""
init_agent.py - Scaffold a project-aware LLM agent (interactive, run in the
project root). The script only initializes; everything afterwards is done by
the agent through skills and folder conventions:

  /explore               Phase 1: build the knowledge base
  /add-ticket            store a ticket as markdown in the .ai/tickets/ inbox
                         (or drop a <ID>-<slug>.md file there yourself)
  /plan <id>             Phase 2: turn an inbox ticket into tasks/<id>/
  /implement <id>        Phase 3: work the planned task files
  /add-reference         register external material (repos, docs) under
                         .ai/external/ + a references/<name> KB node
                         (or place material in .ai/external/ yourself)
  /import-kb <source>    import an existing knowledge base of any structure:
                         read, classify, and transform it into .ai (KB nodes +
                         notes.md large; project-context + notes.md small)
  /import <source>       migrate an existing .ai/ folder (older framework
                         version or other layout) into the current structure:
                         knowledge and lifecycle state (tickets, tasks, changes)
  /tidy-up [scope]       hygiene sweep that may not change behavior: remove
                         dead code, propose obsolete files for removal,
                         shorten overlong comments, drop em dashes from prose
  /update                move the scaffold to the current framework version:
                         merge the framework files, retire what the framework
                         dropped, migrate hand-filled content into the new
                         shape. Never re-explores; the KB is carried forward
  archive                no command: ask the agent to archive a finished
                         ticket; the rules live in AGENTS.md

Prompts: project name, one-line description, project size (auto/large/small),
harness (claude/copilot). Enter accepts the default. The size prompt defaults
to auto: the profile auto-detected from the codebase LOC (small <=10k, large
above); pick large or small to override. --size auto selects it without
prompting and --size large|small forces a profile. Non-TTY runs use the
auto-detected size (and the other defaults) unless overridden by the flags
below. If a scaffold
already exists, init asks before
overwriting framework files; hand-filled content (KB nodes, manifest, INDEX,
notes, specs, the generated project-context section) is always preserved,
never reverted to stubs. To move an existing scaffold to a newer framework
version, run the agent's /update skill rather than re-running init: updating
is a merge (keep user edits, retire dropped files, migrate hand-filled content
into a changed shape), and merges need judgment this script does not have.

Size profiles (auto-selected from codebase LOC when --size is omitted or auto):
  large            Full framework: KB (manifest, hot/cold nodes, INDEX),
                   on-demand phase docs, deterministic KB tools, ticket
                   pipeline. For large codebases where context must be rationed.
  small            For codebases up to ~10k LOC, where the source is small
                   enough to read on demand. No KB/manifest/phase docs/tools:
                   a dense AGENTS.md (commands + conventions + generated
                   project-context), running memory in .ai/notes.md, a
                   lightweight per-change spec (.ai/changes/<id>/spec.md) and
                   one fresh-context review gate. Skills: /explore /spec /build
                   /import-kb /import /tidy-up /update.

Context layout:
  AGENTS.md                    canonical instructions (vendor-neutral): KB
                               protocol, budgets, generated project-context,
                               phase pointers. Read natively by Copilot;
                               imported via CLAUDE.md for Claude Code
  CLAUDE.md (claude)           one-line pointer: @AGENTS.md
  .ai/notes.md                 running memory (both profiles): gotchas,
                               runbooks, unwritten rules; promote durable
                               items into KB nodes (large profile)
  .ai/.current                 gitignored task cursor: cross-session resume
                               pointer (active ticket/change, task file, files)
  .ai/agent/phases/*.md        phase docs, single source of truth, loaded on
                               demand only when the phase runs
  .ai/agent/tools/*.py         deterministic helpers (gen_index, check_stale)
  .claude/skills/*/SKILL.md    Agent Skills (open standard): thin pointers to
                               the phase docs, self-contained add-* helpers
  .github/prompts/*.prompt.md  copilot harness: same content as prompt files
  .claude/settings.json        permission allow list + hooks (claude only)
  .claude/hooks/*.py           hook scripts: protect generated files, remind
                               about uncommitted .ai changes
  .claude/agents/reviewer.md   fresh-context adversarial reviewer subagent

Versioning:
  .ai/ is excluded from the host project's repo (init appends it to the
  project .gitignore) and tracked in its own git repo at .ai/.git. init
  makes the first commit; afterwards the agent commits .ai changes itself
  (protocol rule in AGENTS.md, enforced by a Stop hook on claude).

Generated docs use two language registers (concept v5, CONCEPT.md section 8):
normative docs (AGENTS.md, phase docs) in plain imperative English, KB
content (node summaries, tickets) telegraphic. Identifiers verbatim.

Usage:
  python init_agent.py        (or: init-agent)            interactive
  python init_agent.py --size auto  --name foo --desc "…"  auto-pick profile
  python init_agent.py --size small --name foo --desc "…" force small profile
  Flags: --name, --description/--desc, --size {large,small,auto}, --harness
  {claude,copilot}, -y/--yes (overwrite framework files without prompting).
  Any omitted value is prompted for, or uses its default on a non-TTY.

  Two flags exist only to serve the agent's /update skill, which is how an
  existing scaffold moves to a newer framework version:
  --detect                print this directory's scaffold stamp as JSON
                          (profile, harness, framework version, file list)
  --emit-reference DIR    render a pristine scaffold of the current framework
                          into DIR, with no git or host-project side effects,
                          as the comparison target /update diffs against
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
    /update skill. Prefers the recorded framework.json (authoritative: it also
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
    This is the comparison target the /update skill diffs a real project
    against, so it must be a plain render of the current framework."""
    dest = Path(target).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"error: --emit-reference target is not empty: {dest}",
              file=sys.stderr)
        return 1
    size = args.size if args.size and args.size != "auto" else "large"
    harness = args.harness or "claude"
    name = args.name if args.name is not None else "reference"
    desc = args.description if args.description is not None else ""
    dest.mkdir(parents=True, exist_ok=True)
    if size == "small":
        rc = scaffold_small(dest, name, desc, harness, True, reference=True)
    else:
        rc = scaffold_large(dest, name, desc, harness, True, reference=True)
    if rc == 0:
        print(f"reference {size}/{harness} scaffold "
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

    name = (args.name if args and args.name is not None
            else ask("Project name", root.name))
    desc = (args.description if args and args.description is not None
            else ask("Project description, one line"))
    requested = args.size if args and args.size else None
    if requested and requested != "auto":
        size = requested
    else:
        # No profile given, or "auto": weigh the codebase and recommend one.
        est = estimate_loc(root)
        auto_size = choose_size(est)
        print(f"auto-size: {est} lines of code across source files "
              f"-> {auto_size} profile")
        size = auto_size
        if requested != "auto":     # unspecified + interactive: let user vet it
            choice = ask_choice("Project size", ["auto", "large", "small"],
                                "auto")
            size = auto_size if choice == "auto" else choice
    harness = (args.harness if args and args.harness
               else ask_choice("Harness", ["claude", "copilot"], "claude"))

    marker = (root / ".ai" / "knowledgebase" / "manifest.yaml"
              if size == "large" else root / "AGENTS.md")
    force = bool(args and args.yes)
    if marker.exists() and not force:
        answer = ask("Scaffold exists. Overwrite regenerates framework files "
                     "(instructions, skills, hooks, settings); hand-filled "
                     "content (KB, notes, specs) is preserved either way. "
                     "Overwrite? (y/N)", "n")
        force = answer.lower() in ("y", "yes")

    if size == "small":
        rc = scaffold_small(root, name, desc, harness, force)
    else:
        rc = scaffold_large(root, name, desc, harness, force)
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
    ap.add_argument("--size", choices=["large", "small", "auto"],
                    help="size profile (skip the prompt). Omit or use 'auto' "
                         "to pick automatically from the codebase LOC "
                         "(small <=10k, large above)")
    ap.add_argument("--harness", choices=["claude", "copilot"],
                    help="target harness (skip the prompt); default claude")
    ap.add_argument("-y", "--yes", action="store_true",
                    help="overwrite framework files without prompting")
    ap.add_argument("--detect", action="store_true",
                    help="print this directory's scaffold stamp as JSON "
                         "(profile, harness, framework version, framework "
                         "file list) and exit; used by the /update skill")
    ap.add_argument("--emit-reference", metavar="DIR",
                    help="render a pristine scaffold of the current framework "
                         "into DIR (must be empty or absent) and exit, with "
                         "no git or host-project side effects. The comparison "
                         "target for the /update skill; use --size/--harness "
                         "to match the project being updated")
    ap.add_argument("--bootstrap-update", action="store_true",
                    help="deliver the /update skill into an existing scaffold "
                         "that predates it, and nothing else. Profile and "
                         "harness are detected, never prompted. Use this "
                         "instead of re-running init on an existing scaffold: "
                         "init overwrites whole files and would discard rules "
                         "appended to AGENTS.md and permissions added to "
                         "settings.json. Afterwards run /update in the project")
    ap.add_argument("--debug-probe", action="store_true",
                    help="after scaffolding, run the generated probe.py and "
                         "write its report to PROBE.md in the current "
                         "directory (inspection aid, not part of the "
                         "scaffold; delete or gitignore it)")
    return cmd_init(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
