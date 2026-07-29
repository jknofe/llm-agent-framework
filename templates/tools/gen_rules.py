#!/usr/bin/env python3
"""Regenerate path-scoped Claude Code rules from conventions KB nodes.

Cold `conventions/*` nodes with non-empty `covers` globs render to
`.claude/rules/<id>.md` with `paths:` frontmatter, so the harness injects the
convention deterministically whenever matching files are touched, with no manifest
lookup by the model needed. Hot nodes are excluded (already embedded in the
AGENTS.md project-context section); nodes without `covers` cannot be
path-scoped and stay on the manifest protocol.

The rule files are build artifacts: a marker line tags them, stale ones are
deleted on regeneration, and a PreToolUse hook blocks direct edits. Claude
harness only; on others the manifest protocol covers conventions.

Usage: python3 ${tools_dir}/gen_rules.py
"""
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]
KB = AI / "knowledgebase"
RULES = AI.parent / ".claude" / "rules"
MARKER = "${rules_marker}"

${manifest_parser}

def node_body(path: Path) -> str:
    """Node content without its frontmatter block."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def main() -> int:
    manifest = KB / "manifest.yaml"
    if not manifest.exists():
        print(f"not found: {manifest}", file=sys.stderr)
        return 1
    _, nodes = parse_manifest(manifest.read_text(encoding="utf-8"))
    written = set()
    for n in nodes:
        node_id = n.get("id", "")
        covers = parse_yaml_list(n.get("covers", ""))
        if (not node_id.startswith("conventions/")
                or n.get("tier") != "cold" or not covers):
            continue
        src = KB / n.get("path", "")
        if not src.exists():
            continue
        name = node_id.replace("/", "-") + ".md"
        paths = ", ".join(f'"{g}"' for g in covers)
        RULES.mkdir(parents=True, exist_ok=True)
        (RULES / name).write_text(
            "---\n"
            f"paths: [{paths}]\n"
            "---\n"
            f"<!-- GENERATED from .ai/knowledgebase/{n.get('path', '')} "
            f"{MARKER} -->\n\n"
            + node_body(src),
            encoding="utf-8",
        )
        written.add(name)
        print(f"wrote {RULES / name}")
    # Remove generated rules whose node vanished or lost its covers/cold tier.
    if RULES.is_dir():
        for f in RULES.glob("*.md"):
            if f.name not in written and MARKER in f.read_text(encoding="utf-8"):
                f.unlink()
                print(f"removed stale {f}")
    if not written:
        print("no cold conventions nodes with covers; nothing to render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
