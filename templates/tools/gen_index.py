#!/usr/bin/env python3
"""Regenerate .ai/knowledgebase/INDEX.md from manifest.yaml.

Deterministic; run this instead of editing INDEX.md by hand (a hook blocks
direct edits). Usage: python3 ${tools_dir}/gen_index.py
"""
import sys
from pathlib import Path

KB = Path(__file__).resolve().parents[2] / "knowledgebase"

${manifest_parser}

def main() -> int:
    manifest = KB / "manifest.yaml"
    if not manifest.exists():
        print(f"not found: {manifest}", file=sys.stderr)
        return 1
    project, nodes = parse_manifest(manifest.read_text(encoding="utf-8"))
    lines = [
        f"# Knowledge Base Index: {project}",
        "",
        "<!-- GENERATED from manifest.yaml by gen_index.py. Do not edit. -->",
        "",
        "| Node | Tier | Load when |",
        "|---|---|---|",
    ]
    for n in sorted(nodes, key=lambda n: n.get("path", "")):
        lines.append(
            f"| `{n.get('path', '')}` | {n.get('tier', '')}"
            f" | {n.get('summary', '')} |"
        )
    (KB / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {KB / 'INDEX.md'} ({len(nodes)} nodes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
