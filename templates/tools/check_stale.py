#!/usr/bin/env python3
"""List stale KB nodes: nodes whose `covers` globs match files changed in
the host repo since the node's `updated` date.

Usage: python3 ${tools_dir}/check_stale.py   (from the project root or anywhere)
Exit code 1 when stale nodes were found (CI-friendly), else 0.

Glob matching uses fnmatch (`*` crosses `/`), checked against the full path
and the basename, so `src/**`, `*.toml` and `Makefile` all behave as expected.
"""
import fnmatch
import subprocess
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]
KB = AI / "knowledgebase"
ROOT = AI.parent

${manifest_parser}

def changed_since(date: str, cache: dict) -> list:
    """Files touched by commits strictly after the given day. Bare dates in
    git --since resolve to the current time of day; pin to end of day so a
    node is never stale on the day it was updated."""
    if date not in cache:
        r = subprocess.run(
            ["git", "log", f"--since={date} 23:59:59", "--name-only",
             "--pretty=format:"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"git log failed: {r.stderr.strip()}", file=sys.stderr)
            sys.exit(2)
        cache[date] = sorted({
            line.strip() for line in r.stdout.splitlines() if line.strip()
        })
    return cache[date]


def main() -> int:
    manifest = KB / "manifest.yaml"
    if not manifest.exists():
        print(f"not found: {manifest}", file=sys.stderr)
        return 2
    _, nodes = parse_manifest(manifest.read_text(encoding="utf-8"))
    cache, stale = {}, []
    for n in nodes:
        covers = parse_yaml_list(n.get("covers", ""))
        updated = n.get("updated", "")
        if not covers or not updated:
            continue
        hits = sorted({
            f for f in changed_since(updated, cache) for g in covers
            if fnmatch.fnmatch(f, g) or fnmatch.fnmatch(Path(f).name, g)
        })
        if hits:
            stale.append((n.get("id", "?"), updated, hits))
    if not stale:
        print("OK: no stale nodes")
        return 0
    for node_id, updated, hits in stale:
        sample = ", ".join(hits[:5]) + (" ..." if len(hits) > 5 else "")
        print(f"STALE {node_id} (updated {updated}): {sample}")
    print(f"{len(stale)} stale node(s). Refresh them and bump `updated`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
