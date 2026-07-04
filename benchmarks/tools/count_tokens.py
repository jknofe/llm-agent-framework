#!/usr/bin/env python3
"""Token counter for benchmark runs (claude harness).

Sums API token usage for one benchmark cell from the Claude Code session
transcripts of its work dir. Claude Code writes one JSONL per session under
~/.claude/projects/<encoded-work-dir>/; every assistant line carries the API
call's usage block. The same call can appear on several lines (one per content
block), so lines are deduplicated by message id before summing. All sessions
in the project dir are summed together (resume-after-limit spawns additional
session files; duplicated history lines are caught by the same dedup) and
sub-agent (sidechain) usage is included, because those are real tokens the
cell consumed.

Usage:
  python3 count_tokens.py <WORK_DIR>          # e.g. /tmp/benchmark/runs/<id>/<repo>
  python3 count_tokens.py --projects-dir DIR  # explicit ~/.claude/projects/<name>

Output: a Markdown block to paste into the cell's results file. Informational
only, never gating; token totals are expected to drift across dates/models.
Read-only; stdlib only.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens",
              "cache_read_input_tokens", "output_tokens")


def candidate_dirs(work_dir: str):
    """Claude Code encodes the session cwd by replacing every non-alphanumeric
    character with '-'. Try the raw path, the resolved path, and the macOS
    /private variant."""
    p = Path(work_dir)
    raw = [str(p), str(p.resolve())]
    raw += ["/private" + r for r in raw if r.startswith("/tmp/")]
    seen, out = set(), []
    for r in raw:
        enc = re.sub(r"[^A-Za-z0-9]", "-", r)
        if enc not in seen:
            seen.add(enc)
            out.append(PROJECTS / enc)
    return out


def collect(project_dir: Path):
    """Return (per_model_totals, per_session_totals, api_calls, sessions,
    skipped_dup_lines). Files are walked oldest-first so a resume-forked
    session's copied history stays attributed to the original session."""
    totals = defaultdict(lambda: defaultdict(int))
    per_session = []
    seen_ids = set()
    files = sorted(project_dir.glob("*.jsonl"),
                   key=lambda f: f.stat().st_mtime)
    dups = 0
    for f in files:
        sess = defaultdict(int)
        for line in f.open(encoding="utf-8", errors="replace"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            msg = d.get("message") or {}
            usage = msg.get("usage")
            if d.get("type") != "assistant" or not usage:
                continue
            mid = msg.get("id") or d.get("requestId") or d.get("uuid")
            if mid in seen_ids:
                dups += 1
                continue
            seen_ids.add(mid)
            model = msg.get("model") or "unknown"
            for k in USAGE_KEYS:
                n = int(usage.get(k) or 0)
                totals[model][k] += n
                sess[k] += n
        per_session.append((f.stem, sess))
    return totals, per_session, len(seen_ids), len(files), dups


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("work_dir", nargs="?",
                    help="benchmark cell work dir (the agent's cwd)")
    ap.add_argument("--projects-dir",
                    help="explicit ~/.claude/projects/<name> dir (overrides "
                         "work_dir lookup)")
    ap.add_argument("--per-session", action="store_true",
                    help="also print one row per session file (oldest first; "
                         "for marginal-cost comparisons, e.g. the baseline "
                         "arm's B-amortized sequence)")
    args = ap.parse_args()
    if not args.work_dir and not args.projects_dir:
        ap.error("give WORK_DIR or --projects-dir")

    if args.projects_dir:
        pdir = Path(args.projects_dir)
    else:
        pdir = next((c for c in candidate_dirs(args.work_dir)
                     if c.is_dir()), None)
        if pdir is None:
            print("no transcript dir found under " + str(PROJECTS)
                  + " for " + args.work_dir, file=sys.stderr)
            print("candidates tried:", file=sys.stderr)
            for c in candidate_dirs(args.work_dir):
                print("  " + str(c), file=sys.stderr)
            return 1

    totals, per_session, calls, sessions, dups = collect(pdir)
    if not totals:
        print("no assistant usage entries in " + str(pdir), file=sys.stderr)
        return 1

    cols = ["Model", "Input", "Cache write", "Cache read", "Output", "Total"]
    lines = ["## Token usage (count_tokens.py, informational)", "",
             "- Transcript dir: `" + str(pdir) + "`",
             "- Sessions: " + str(sessions) + " | API calls: " + str(calls)
             + " | duplicate lines skipped: " + str(dups), "",
             "| " + " | ".join(cols) + " |",
             "|" + "---|" * len(cols)]
    grand = defaultdict(int)
    for model in sorted(totals):
        u = totals[model]
        row_total = sum(u[k] for k in USAGE_KEYS)
        if row_total == 0:      # harness-internal entries, e.g. <synthetic>
            continue
        lines.append("| " + model + " | "
                     + " | ".join(str(u[k]) for k in USAGE_KEYS)
                     + " | " + str(row_total) + " |")
        for k in USAGE_KEYS:
            grand[k] += u[k]
    lines.append("| **all** | "
                 + " | ".join(str(grand[k]) for k in USAGE_KEYS)
                 + " | " + str(sum(grand.values())) + " |")
    if args.per_session:
        lines += ["", "| Session (oldest first) | Input | Cache write "
                  "| Cache read | Output | Total |", "|" + "---|" * 6]
        for stem, u in per_session:
            row_total = sum(u[k] for k in USAGE_KEYS)
            if row_total == 0:
                continue
            lines.append("| " + stem + " | "
                         + " | ".join(str(u[k]) for k in USAGE_KEYS)
                         + " | " + str(row_total) + " |")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
