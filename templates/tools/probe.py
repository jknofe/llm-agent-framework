#!/usr/bin/env python3
"""Command detection for /explore.

Prints the build/test/lint commands this project appears to use and the
documentation it already has. That is all: a module map or LOC table is a
repository overview, and an overview does not help an agent find anything
(CONCEPT.md section 38). Detection is a prompt for /explore's questions, not
an answer; the user's own commands win where the two disagree.

Read-only; stdlib only.

Usage: python3 .ai/agent/tools/probe.py   (from anywhere)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2].parent  # host repo root (above .ai/)

DEP_MANIFESTS = [
    "package.json", "Cargo.toml", "go.mod", "pyproject.toml", "setup.cfg",
    "setup.py", "requirements.txt", "tox.ini", "Gemfile", "Rakefile",
    "pom.xml", "build.gradle", "composer.json", "Makefile", "CMakeLists.txt",
    "snapcraft.yaml", "package.xml", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "compose.yml", "compose.yaml",
]
# Manifests that live below the repo root (checked against relative paths).
NESTED_MANIFESTS = ["snap/snapcraft.yaml", "debian/control"]


def run(args):
    try:
        r = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr
    except OSError:
        return 1, "", ""


def tracked_files():
    """git ls-files: deterministic + gitignore-aware. Fallback: os.walk."""
    code, out, _ = run(["git", "ls-files"])
    if code == 0 and out.strip():
        return [ROOT / line for line in out.splitlines() if line.strip()]
    files = []
    for p in ROOT.rglob("*"):
        if p.is_file() and "/.git/" not in str(p):
            files.append(p)
    return files


def host_sha():
    code, out, _ = run(["git", "rev-parse", "HEAD"])
    return out.strip() if code == 0 and out.strip() else "n/a (not a git repo)"


def read(name):
    try:
        return (ROOT / name).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect_commands(names, rels):
    """names = basenames at repo root; rels = all tracked paths, relative,
    forward-slashed (for manifests that live below the root)."""
    out = []
    if "package.json" in names:
        try:
            scripts = json.loads(read("package.json")).get("scripts", {})
        except ValueError:
            scripts = {}
        if scripts:
            out.append(("package.json scripts",
                        ["npm run " + k for k in sorted(scripts)]))
    if "Cargo.toml" in names:
        out.append(("Cargo", ["cargo build", "cargo test", "cargo clippy"]))
    if "go.mod" in names:
        out.append(("Go", ["go build ./...", "go test ./..."]))
    if names & {"pyproject.toml", "setup.cfg", "tox.ini", "setup.py"}:
        out.append(("Python", ["(see pyproject.toml / tox.ini for test+lint)"]))
    if names & {"Gemfile", "Rakefile"}:
        out.append(("Ruby", ["rake", "rspec"]))
    if "Makefile" in names:
        targets = sorted(set(
            re.findall(r"(?m)^([A-Za-z0-9_.-]+):(?!=)", read("Makefile"))))
        targets = [t for t in targets if t.lower() != ".phony"]
        if targets:
            out.append(("Makefile targets",
                        ["make " + t for t in targets[:15]]))
    ros_pkgs = sorted(r for r in rels
                      if r == "package.xml" or r.endswith("/package.xml"))
    if ros_pkgs and any(k in read(r) for r in ros_pkgs[:5]
                        for k in ("ament", "catkin")):
        out.append(("ROS 2 / colcon", [
            "rosdep install --from-paths . --ignore-src -y",
            "colcon build", "colcon test", "colcon test-result --verbose"]))
    repos_files = sorted(r for r in rels if r.endswith(".repos"))
    if repos_files:
        out.append(("vcstool", ["vcs import < " + f
                                for f in repos_files[:3]] + ["vcs pull"]))
    if "snapcraft.yaml" in names or "snap/snapcraft.yaml" in rels:
        out.append(("Snapcraft", ["snapcraft pack"]))
    if "debian/control" in rels or "debian/rules" in rels:
        out.append(("Debian packaging",
                    ["dpkg-buildpackage -us -uc -b", "lintian"]))
    dockerfiles = sorted(r for r in rels
                         if r == "Dockerfile" or r.endswith("/Dockerfile"))
    if dockerfiles:
        out.append(("Docker", [
            "docker build " + (f[:-len("Dockerfile")] or ".")
            for f in dockerfiles[:3]]))
    if names & {"docker-compose.yml", "docker-compose.yaml",
                "compose.yml", "compose.yaml"}:
        out.append(("Docker Compose",
                    ["docker compose build", "docker compose up -d"]))
    workflows = sorted(r for r in rels
                       if r.startswith(".github/workflows/")
                       and r.endswith((".yml", ".yaml")))
    if workflows:
        shown = workflows[:5]
        if len(workflows) > 5:
            shown.append("+" + str(len(workflows) - 5) + " more")
        out.append(("GitHub Actions (CI gates)", shown))
    return out


DOC_DIRS = ("docs/", "doc/", "documentation/")
DOC_FILES = ("CONTRIBUTING.md", "ARCHITECTURE.md", "DEVELOPMENT.md",
             "HACKING.md", "DESIGN.md")
README_MIN_WORDS = 200


def detect_docs(names, rels):
    """What the repository already documents. A context file that restates
    existing docs adds cost without adding information, so /explore points
    at these instead of summarizing."""
    out = []
    for name in sorted(names):
        if name.lower().startswith("readme"):
            words = len(read(name).split())
            if words >= README_MIN_WORDS:
                out.append(name + " (" + str(words) + " words)")
    for name in DOC_FILES:
        if name in names:
            out.append(name)
    for d in DOC_DIRS:
        n = sum(1 for r in rels if r.startswith(d))
        if n:
            out.append(d + " (" + str(n) + " files)")
    return out


def main():
    files = tracked_files()
    names_at_root = {p.name for p in files if p.parent == ROOT}
    rel_paths = set()
    for p in files:
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        rel_paths.add(str(rel).replace("\\", "/"))

    lines = ["# Detected commands (probe.py)", ""]
    lines.append("- Host commit: " + host_sha())
    lines.append("- Tracked files: " + str(len(files)))
    lines.append("")

    cmds = detect_commands(names_at_root, rel_paths)
    lines += ["## Build / test / lint (detected)", ""]
    if cmds:
        for tool, cs in cmds:
            lines.append("- **" + tool + "**: " + "; ".join(cs))
        lines.append("- confirm these with the user; their commands win")
    else:
        lines.append("- none detected (ask the user)")
    lines.append("")

    deps = sorted(names_at_root & set(DEP_MANIFESTS))
    deps += [m for m in NESTED_MANIFESTS if m in rel_paths]
    lines += ["## Dependency manifests", "",
              (", ".join(deps) if deps else "none at repo root"), ""]

    docs = detect_docs(names_at_root, rel_paths)
    lines += ["## Documentation present", ""]
    if docs:
        lines += ["- " + d for d in docs]
        lines.append("- point at these instead of summarizing the codebase")
    else:
        lines.append("- none (no README over 200 words, no docs/ tree)")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
