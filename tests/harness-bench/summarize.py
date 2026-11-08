#!/usr/bin/env python3
"""Combine the counted runs into one comparison. Usage: summarize.py r3 r4 r5

Per harness: correctness from the grades, then tokens, time and tool calls
from the metrics, split by role (supervisor session, worker, reviewer),
reported as median and range over the runs.
"""
import json, statistics, sys
from pathlib import Path

import os
R = Path(os.environ.get("BENCH_DIR", Path.home() / "tmp/harness-bench")) / "results"
# Usage: summarize.py claude=r3,r6,r7 opencode=r3,r4,r5
SEL = dict(arg.split("=", 1) for arg in sys.argv[1:])
HARN = ["claude", "opencode"]
RUNS_OF = {h: SEL[h].split(",") for h in HARN}


def load(kind, h, r):
    p = R / f"{h}-{r}.{kind}.json"
    return json.loads(p.read_text()) if p.is_file() else None


def role(sub):
    a = (sub.get("agent") or "").lower()
    return "worker" if "worker" in a else "reviewer" if "review" in a else "other"


def mr(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "-"
    return f"{statistics.median(xs):,.0f} ({min(xs):,.0f}-{max(xs):,.0f})"


print("runs: " + "; ".join(f"{h} {','.join(RUNS_OF[h])}" for h in HARN) + "\n")
print("## Correctness\n")
print("| | " + " | ".join(HARN) + " |\n|---|" + "---|" * len(HARN))
rows = {}
for h in HARN:
    gs = [g for g in (load("grade", h, r) for r in RUNS_OF[h]) if g]
    tasks = [t for g in gs for k, t in g["tasks"].items() if "status" in t]
    rows.setdefault("tasks passed", []).append(
        f"{sum(g['passed'] for g in gs)}/{6 * len(gs)}")
    rows.setdefault("correct path (inline/worker)", []).append(
        f"{sum(t['path_ok'] for t in tasks)}/{len(tasks)}")
    rows.setdefault("worker rule breaks", []).append(
        str(sum(len(t["worker_rule"]) for t in tasks)))
    wt = [g["tasks"]["readme-shortcut-tables"] for g in gs]
    rows.setdefault("worker task: delegated", []).append(
        f"{sum(t['worker'] for t in wt)}/{len(wt)}")
    rows.setdefault("worker task: review kind", []).append(
        ", ".join(sorted({(t['review'] or '-')[:22] for t in wt})))
    rows.setdefault("scope only README.md", []).append(
        f"{sum(g['scope_ok'] for g in gs)}/{len(gs)}")
    rows.setdefault("creates well-formed", []).append(
        f"{sum(1 for g in gs for k in ('plan-pixelate-placeholder', 'plan-cli-reference') if g['tasks'][k]['exists'] and g['tasks'][k]['done_when_items'] and g['tasks'][k]['tracker'])}/{2 * len(gs)}")
for k, v in rows.items():
    print(f"| {k} | " + " | ".join(v) + " |")

print("\n## Tokens per run (median, range), all 9 sessions\n")
print("| | " + " | ".join(HARN) + " |\n|---|" + "---|" * len(HARN))
agg = {}
for h in HARN:
    per_run = []
    for r in RUNS_OF[h]:
        m = load("metrics", h, r)
        if not m:
            continue
        t = {f"{who} {k}": 0 for who in ("supervisor", "worker", "reviewer")
             for k in ("out", "in+cache_write", "cache_read")}
        t.update({"seconds": 0, "tools": 0, "sessions": len(m)})
        models = set()
        for s in m:
            tk = s["tokens"]
            t["supervisor out"] += tk["out"]
            t["supervisor in+cache_write"] += tk["in"] + tk["cache_write"]
            t["supervisor cache_read"] += tk["cache_read"]
            t["seconds"] += s["seconds"] or 0
            t["tools"] += s["tools"]
            for sub in s["subagents"]:
                who = role(sub)
                if who == "other":
                    who = "worker"
                st = sub["tokens"]
                t[f"{who} out"] += st["out"]
                t[f"{who} in+cache_write"] += st["in"] + st["cache_write"]
                t[f"{who} cache_read"] += st["cache_read"]
                t["tools"] += sub["tools"]
                models.update(f"{who}:{x}" for x in sub["models"] if x)
        for s_ in m:
            models.update(f"supervisor-effort:{e}" for e in s_.get("effort", []) if e)
            for sub in s_["subagents"]:
                models.update(f"{role(sub)}-effort:{e}" for e in sub.get("effort", []) if e)
        t["models"] = models
        per_run.append(t)
    agg[h] = per_run
# Estimated list-price cost, $ per million tokens (claude-api skill, cached
# 2026-10-06). Cache write taken as 1.25x input (5-minute TTL) and Haiku's
# cache read as 0.1x input: the skill states those as approximations.
PRICE = {"fable": {"in": 10.00, "out": 50.00, "cr": 0.25},
         "opus": {"in": 4.00, "out": 20.00, "cr": 0.20},
         "sonnet": {"in": 2.00, "out": 10.00, "cr": 0.20},
         "haiku": {"in": 0.10, "out": 0.50, "cr": 0.01}}
# Which model each role ran, from the profile (ROLE_MODELS in profiles/*.env).
ROLE_MODEL = dict(kv.split("=") for kv in os.environ.get(
    "ROLE_MODELS", "supervisor=sonnet,worker=haiku,reviewer=sonnet").split(","))
for h in HARN:
    for t in agg[h]:
        cost = 0.0
        for who, mdl in ROLE_MODEL.items():
            p_ = PRICE[mdl]
            cost += (t[f"{who} out"] * p_["out"]
                     + t[f"{who} in+cache_write"] * p_["in"] * 1.25
                     + t[f"{who} cache_read"] * p_["cr"]) / 1e6
        t["est. cost (US cents)"] = round(cost * 100)
first = next((agg[h][0] for h in HARN if agg[h]), {})
keys = [k for k in first if k != "models"]
for k in keys:
    print(f"| {k} | " + " | ".join(mr([t.get(k) for t in agg[h]]) for h in HARN) + " |")
print()
for h in HARN:
    ms = sorted(set().union(*[t["models"] for t in agg[h]])) if agg[h] else []
    print(f"{h} models and effort seen: {', '.join(ms) or '-'}")
