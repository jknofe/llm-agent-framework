#!/usr/bin/env python3
"""Token, time and tool-call metrics per step of one run, sub-agents included.
Usage: metrics.py <harness> <run-dir>  -> prints JSON, one entry per session.

Claude Code: the session transcripts of the run directory and their
subagents/ files, usage deduplicated by message id. OpenCode: every session
whose location is the run directory, root and child, from the server API;
root sessions are matched to steps by their first message.
"""
import glob, json, os, re, subprocess, sys
from datetime import datetime

HARNESS, RUN = sys.argv[1], os.path.realpath(sys.argv[2])
ZERO = lambda: {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0}


def step_of(args):
    a = (args or "").strip()
    m = re.match(r"(do|create)\s+(\S+)", a)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    return "list" if a.startswith("list") else a[:40]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def claude():
    enc = RUN.replace("/", "-").replace(".", "-")
    proj = os.path.expanduser(f"~/.claude/projects/{enc}")
    out = []
    for f in sorted(glob.glob(f"{proj}/*.jsonl"), key=os.path.getmtime):
        sid = os.path.basename(f)[:-6]
        main, tools, args, t = ZERO(), 0, None, []
        seen, model = {}, set()
        for line in open(f):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("timestamp") and d.get("type") in ("user", "assistant"):
                t.append(ts(d["timestamp"]))
            if args is None and "<command-args>" in line and d.get("type") == "user":
                m = re.search(r"<command-args>(.+?)</command-args>", line)
                args = m.group(1) if m else None
            if d.get("type") != "assistant":
                continue
            m = d.get("message", {})
            if m.get("model"):
                model.add(m["model"])
            if m.get("id") and m.get("usage"):
                seen[m["id"]] = m["usage"]
            for c in m.get("content") or []:
                tools += c.get("type") == "tool_use"
        for u in seen.values():
            main["in"] += u.get("input_tokens", 0)
            main["out"] += u.get("output_tokens", 0)
            main["cache_read"] += u.get("cache_read_input_tokens", 0)
            main["cache_write"] += u.get("cache_creation_input_tokens", 0)
        effort = sorted(set(re.findall(r'"effort":"([a-z]+)"', open(f).read())))
        subs = []
        for s in glob.glob(f"{proj}/{sid}/subagents/*.jsonl"):
            su, sseen, smodel, stools = ZERO(), {}, set(), 0
            agent = None
            meta = s[:-len(".jsonl")] + ".meta.json"
            if os.path.isfile(meta):
                agent = json.load(open(meta)).get("agentType")
            for line in open(s):
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                agent = agent or d.get("agentType") or d.get("subagent_type")
                if d.get("type") != "assistant":
                    continue
                m = d.get("message", {})
                if m.get("model"):
                    smodel.add(m["model"])
                if m.get("id") and m.get("usage"):
                    sseen[m["id"]] = m["usage"]
                for c in m.get("content") or []:
                    stools += c.get("type") == "tool_use"
            for u in sseen.values():
                su["in"] += u.get("input_tokens", 0)
                su["out"] += u.get("output_tokens", 0)
                su["cache_read"] += u.get("cache_read_input_tokens", 0)
                su["cache_write"] += u.get("cache_creation_input_tokens", 0)
            subs.append({"agent": agent, "models": sorted(smodel),
                         "effort": sorted(set(re.findall(r'"effort":"([a-z]+)"',
                                                          open(s).read()))),
                         "tokens": su, "tools": stools})
        if args is None:
            continue
        out.append({"step": step_of(args), "session": sid[:8],
                    "models": sorted(model), "effort": effort,
                    "tokens": main, "tools": tools,
                    "seconds": round(max(t) - min(t)) if t else None,
                    "subagents": subs})
    return out


def opencode():
    oc = os.path.expanduser("~/.opencode/bin/opencode")
    r = subprocess.run([oc, "api", "GET", "/api/session"], cwd=RUN,
                       capture_output=True, text=True)
    d = json.loads(r.stdout)
    items = d.get("data", d) if isinstance(d, dict) else d
    items = items if isinstance(items, list) else items.get("items", [])
    mine = [s for s in items
            if os.path.realpath((s.get("location") or {}).get("directory", ""))
            == RUN]

    def tok(s):
        t = s.get("tokens") or {}
        c = t.get("cache") or {}
        return {"in": t.get("input", 0),
                "out": t.get("output", 0) + t.get("reasoning", 0),
                "cache_read": c.get("read", 0), "cache_write": c.get("write", 0)}

    def export(sid):
        e = subprocess.run([oc, "session", "export", sid], cwd=RUN,
                           capture_output=True, text=True)
        return json.loads(e.stdout)

    def tools_in(o):
        n = 0
        if isinstance(o, dict):
            if o.get("type") == "tool" and "name" in o:
                n += 1
            n += sum(tools_in(v) for v in o.values())
        elif isinstance(o, list):
            n += sum(tools_in(v) for v in o)
        return n

    out = []
    for s in sorted((s for s in mine if not s.get("parentID")),
                    key=lambda s: (s.get("time") or {}).get("created", 0)):
        ex = export(s["id"])
        first = next((m.get("text", "") for m in ex.get("messages", [])
                      if m.get("text")), "")
        m = re.search(r"Arguments:\s*\n(.*)", first)
        tm = s.get("time") or {}
        end = tm.get("idle") or tm.get("updated") or tm.get("created")
        subs = []
        for c in mine:
            if c.get("parentID") == s["id"]:
                subs.append({"agent": c.get("agent"),
                             "models": [(c.get("model") or {}).get("id")],
                             "effort": [(c.get("model") or {}).get("variant")],
                             "tokens": tok(c),
                             "tools": tools_in(export(c["id"]).get("messages"))})
        out.append({"step": step_of(m.group(1) if m else ""),
                    "session": s["id"][:14],
                    "models": [(s.get("model") or {}).get("id")],
                    "effort": [(s.get("model") or {}).get("variant")],
                    "tokens": tok(s), "tools": tools_in(ex.get("messages")),
                    "seconds": round((end - tm.get("created", end)) / 1000),
                    "subagents": subs})
    return out


print(json.dumps(claude() if HARNESS == "claude" else opencode(), indent=1))
