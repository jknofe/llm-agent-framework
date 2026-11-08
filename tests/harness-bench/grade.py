#!/usr/bin/env python3
"""Grade one run from its files. Usage: grade.py <run-dir> -> JSON on stdout.

Never reads an agent's summary: only the task files, the .ai history, the
host diff, and reference answers computed from satty at the pinned commit.
"""
import json, re, subprocess, sys
from pathlib import Path

RUN = Path(sys.argv[1])
BASE = "f578432"
# The expected path follows the 11.6 rule: inline when at most one open step
# edits a host file. readme-config-reference has one editing step (write the
# table), so it is inline; readme-shortcut-tables has two, so it goes to the
# worker.
INLINE = ["input-scale-window", "nextrelease-typo", "readme-troubleshooting",
          "keybinds-consistency", "readme-config-reference"]
WORKER = ["readme-shortcut-tables"]


def git(*a, cwd=RUN):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True,
                          text=True).stdout


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def boxes(text, name):
    s = section(text, name)
    return len(re.findall(r"^- \[x\]", s, re.M)), len(re.findall(r"^- \[[ x]\]", s, re.M))


def task(tid):
    f = RUN / ".ai/tasks" / tid / "task.md"
    return f.read_text() if f.is_file() else ""


def worker_rule(tid):
    """A worker round commit must not tick a done-when box, write the
    Outcome or set the status (work.md)."""
    bad = []
    for line in git("log", "--format=%H %s", "--", f"tasks/{tid}/task.md",
                    cwd=RUN / ".ai").splitlines():
        sha, subj = line.split(" ", 1)
        if "worker round" not in subj.lower():
            continue
        after = git("show", f"{sha}:tasks/{tid}/task.md", cwd=RUN / ".ai")
        before = git("show", f"{sha}^:tasks/{tid}/task.md", cwd=RUN / ".ai")
        if boxes(after, "Done when")[0] > boxes(before, "Done when")[0]:
            bad.append(f"{sha[:7]} ticked done-when")
        if section(after, "Outcome").strip() != section(before, "Outcome").strip():
            bad.append(f"{sha[:7]} wrote Outcome")
        st = lambda t: (re.search(r"^status:\s*(\S+)", t, re.M) or [None, None])[1]
        if st(after) in ("done", "blocked") and st(after) != st(before):
            bad.append(f"{sha[:7]} set status {st(after)}")
    return bad


def base(path):
    return git("show", f"{BASE}:{path}")


def kbd_tokens(text):
    return re.findall(r"<kbd>[^<]+</kbd>", text)


def shortcuts_region(text):
    a = text.find("#### General")
    b = text.find("### Pointer Tool")
    return text[a:b] if a != -1 and b != -1 else ""


def config_general():
    """Active option names and values in [general] of the pinned config."""
    out, on = {}, False
    for line in base("config.toml").splitlines():
        if line.startswith("["):
            on = line.strip() == "[general]"
            continue
        m = re.match(r"([a-z][a-z0-9-]*)\s*=\s*(.+)$", line)
        if on and m:
            out[m.group(1)] = m.group(2).strip()
    return out


def content_checks(readme, texts):
    c = {}
    t = texts["input-scale-window"]
    out = section(t, "Outcome")
    c["input-scale-window"] = bool(re.search(r"main\.rs", out)) and bool(
        re.search(r"imp\.rs|zoom", out, re.I))
    c["nextrelease-typo"] = ("NEXTRELASE" not in readme
                             and "pixelate<sup>NEXTRELEASE</sup>" in readme
                             and base("release.nu") == (RUN / "release.nu").read_text())
    c["readme-troubleshooting"] = bool(re.search(r"^## Troubleshooting", readme, re.M))
    c["keybinds-consistency"] = "copy-filepath" in texts["keybinds-consistency"]
    # Shortcut tables: every original <kbd> token of the two lists survives,
    # the lists became tables, and each Config action exists in the code.
    orig = kbd_tokens(shortcuts_region(base("README.md")))
    now = shortcuts_region(readme)
    missing = [k for k in set(orig) if now.count(k) < orig.count(k)]
    rs = (RUN / "src/keybindings.rs").read_text()
    actions = re.findall(r"^\|[^|\n]*\|[^|\n]*\|\s*`?([a-z][a-z0-9:-]*)`?\s*\|", now, re.M)
    # Tool names are the strings Tools::from_str accepts (src/tools/mod.rs).
    mod = (RUN / "src/tools/mod.rs").read_text()
    tools = set(re.findall(r'"([a-z][a-z-]*)" => Ok\(Self::', mod))
    unknown = sorted({a for a in actions if f'"{a}"' not in rs and a not in tools})
    c["readme-shortcut-tables"] = {"ok": not missing and "Config action" in now
                                   and not unknown,
                                   "missing_kbd": missing[:5],
                                   "unknown_actions": unknown[:5]}
    # Config reference: one row per active [general] option, default matching.
    gen = config_general()
    m = re.search(r"^### Configuration reference\n(.*?)(?=^#{1,3} |\Z)", readme, re.M | re.S)
    rows = {}
    for line in (m.group(1) if m else "").splitlines():
        r = re.match(r"^\|\s*`?([a-z][a-z0-9-]*)`?\s*\|\s*(.*?)\s*\|", line)
        if r and r.group(1) != "option":
            rows[r.group(1)] = r.group(2).strip("` ")
    absent = sorted(set(gen) - set(rows))
    extra = sorted(set(rows) - set(gen))
    wrong = sorted(k for k in set(gen) & set(rows)
                   if re.sub(r"[\s`\"']", "", gen[k]) not in re.sub(r"[\s`\"'\\]", "", rows[k]))
    c["readme-config-reference"] = {"ok": bool(m) and not absent and not extra
                                    and not wrong, "options": len(gen),
                                    "rows": len(rows), "absent": absent[:5],
                                    "extra": extra[:5], "wrong_default": wrong[:5]}
    return c


def main():
    texts = {t: task(t) for t in INLINE + WORKER}
    readme = (RUN / "README.md").read_text()
    content = content_checks(readme, texts)
    out = {"run": RUN.name, "tasks": {}}
    for tid in INLINE + WORKER:
        t = texts[tid]
        st = (re.search(r"^status:\s*(\S+)", t, re.M) or [None, "missing"])[1]
        ticked, total = boxes(t, "Done when")
        f = section(t, "Findings")
        worker = bool(re.search(r"Worker round", f))
        review = re.search(r"Review: ([^:\n]+)", f)
        cc = content[tid]
        out["tasks"][tid] = {
            "status": st, "done_when": f"{ticked}/{total}",
            "review": review.group(1).strip() if review else None,
            "worker": worker,
            "delegation": bool(re.search(r"Delegation:", f)),
            "path_ok": worker == (tid in WORKER),
            "worker_rule": worker_rule(tid) if worker else [],
            "content_ok": cc["ok"] if isinstance(cc, dict) else cc,
            "content": cc if isinstance(cc, dict) else None,
        }
    changed = [p for p in git("diff", "--name-only", "HEAD").split() if p]
    changed += [p[3:] for p in git("status", "--porcelain").splitlines()
                if p.startswith("??")]
    out["host_changes"] = sorted(set(changed))
    out["scope_ok"] = set(changed) <= {"README.md"}
    for tid in ("plan-pixelate-placeholder", "plan-cli-reference"):
        t = task(tid)
        out["tasks"][tid] = {
            "exists": bool(t),
            "type": (re.search(r"^type:\s*(\S+)", t, re.M) or [None, None])[1],
            "done_when_items": boxes(t, "Done when")[1],
            "steps": boxes(t, "Steps")[1],
            "tracker": bool(section(t, "Tracker").strip()),
        }
    table = subprocess.run(["python3", ".ai/agent/tools/tasks.py"], cwd=RUN,
                           capture_output=True, text=True).stdout
    out["list_flags"] = sum(1 for l in table.splitlines()
                            if l.startswith("|") and "❗" in l)
    out["passed"] = sum(1 for tid in INLINE + WORKER
                        if out["tasks"][tid]["status"] == "done"
                        and out["tasks"][tid]["content_ok"]
                        and not out["tasks"][tid]["worker_rule"])
    print(json.dumps(out, indent=1))


main()
