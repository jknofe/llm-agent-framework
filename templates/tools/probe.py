#!/usr/bin/env python3
"""Deterministic repo inventory for Phase 1 (Initialization).

Prints a compact, stable-sorted Markdown snapshot of the host project so the
agent can seed the mechanical project-context fields (stack, build/test/lint
commands, module map) without spending tokens on discovery, and sample the tree
instead of scanning it. Read-only; stdlib only.

Usage: python3 .ai/agent/tools/probe.py   (from anywhere)
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2].parent  # host repo root (above .ai/)
TOP_LANGS = 12
TOP_DIRS = 20
TOP_ENTRIES = 20

LANGS = {
    ".py": "Python", ".rs": "Rust", ".go": "Go", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby",
    ".php": "PHP", ".c": "C", ".h": "C/C++ header", ".hpp": "C++ header",
    ".cpp": "C++", ".cc": "C++", ".cs": "C#", ".swift": "Swift",
    ".scala": "Scala", ".sh": "Shell", ".bash": "Shell", ".sql": "SQL",
    ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".json": "JSON", ".html": "HTML", ".css": "CSS", ".scss": "CSS",
}
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


def loc(path):
    try:
        with path.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


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


ENTRY_BASENAMES = ("main.", "index.", "app.", "__main__.py", "cli.")
ENTRY_PREFIXES = ("cmd/", "bin/", "src/main", "src/bin/")

# Code-only subset of LANGS for the total-LOC line: docs, data, and markup are
# excluded so the number matches the size-profile boundary (~10k LOC).
NON_CODE_EXTS = {".md", ".yaml", ".yml", ".toml", ".json",
                 ".html", ".css", ".scss"}


def main():
    files = tracked_files()
    names_at_root = {p.name for p in files if p.parent == ROOT}
    rel_paths = set()
    exts = Counter()
    dir_files = defaultdict(int)
    dir_loc = defaultdict(int)
    code_loc = 0
    entries = []
    for p in files:
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        rels = str(rel).replace("\\", "/")
        rel_paths.add(rels)
        seg = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        dir_files[seg] += 1
        ext = p.suffix.lower()
        if ext in LANGS:
            exts[LANGS[ext]] += 1
            n = loc(p)
            dir_loc[seg] += n
            if ext not in NON_CODE_EXTS:
                code_loc += n
        base = p.name
        if base.startswith(ENTRY_BASENAMES) or rels.startswith(ENTRY_PREFIXES):
            entries.append(rels)

    lines = ["# Repo inventory (probe.py)", ""]
    lines.append("- Host commit: " + host_sha())
    lines.append("- Tracked files: " + str(len(files)))
    lines.append("- Code LOC (docs/data/markup excluded): " + str(code_loc)
                 + " (size-profile boundary ~10k)")
    lines.append("")

    lines += ["## Languages", "", "| Language | Files |", "|---|---|"]
    for lang, n in exts.most_common(TOP_LANGS):
        lines.append("| " + lang + " | " + str(n) + " |")
    lines.append("")

    cmds = detect_commands(names_at_root, rel_paths)
    lines += ["## Build / test / lint (detected)", ""]
    if cmds:
        for tool, cs in cmds:
            lines.append("- **" + tool + "**: " + "; ".join(cs))
    else:
        lines.append("- none detected (ask the user)")
    lines.append("")

    lines += ["## Module map (top-level, by LOC)", "",
              "| Path | Files | LOC |", "|---|---|---|"]
    ranked = sorted(dir_files, key=lambda d: (-dir_loc[d], d))[:TOP_DIRS]
    for d in ranked:
        lines.append("| " + d + " | " + str(dir_files[d]) + " | "
                     + str(dir_loc[d]) + " |")
    lines.append("")

    deps = sorted(names_at_root & set(DEP_MANIFESTS))
    deps += [m for m in NESTED_MANIFESTS if m in rel_paths]
    lines += ["## Dependency manifests", "",
              (", ".join(deps) if deps else "none at repo root"), ""]

    lines += ["## Entry-point candidates", ""]
    if entries:
        for e in sorted(set(entries))[:TOP_ENTRIES]:
            lines.append("- " + e)
    else:
        lines.append("- none matched (inspect the module map)")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
