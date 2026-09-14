#!/usr/bin/env python3
"""measure.py AGENT_ID LABEL -> markdown block: tokens (agent + children), API calls, reads of notes/map."""
import json, sys, glob, os, subprocess
from pathlib import Path
D = Path.home()/".claude/projects/-home-johannes-git-llm-agent-framework/a47c2f10-dc02-4619-a093-1010cd9dca3b/subagents"
aid, label = sys.argv[1], sys.argv[2]
ids = [aid]
for m in D.glob("agent-*.meta.json"):
    if json.loads(m.read_text()).get("parentAgentId") == aid:
        ids.append(m.name[len("agent-"):-len(".meta.json")])
tot = {"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0}
calls = 0; reads = {"notes.md":0,"map.md":0,"AGENTS.md":0}; per = []
for i in ids:
    seen=set(); c=0; t=dict.fromkeys(tot,0)
    for line in open(D/f"agent-{i}.jsonl"):
        try: d=json.loads(line)
        except: continue
        m=d.get("message",{})
        if d.get("type")!="assistant": continue
        for blk in m.get("content",[]):
            if blk.get("type")=="tool_use":
                s=json.dumps(blk.get("input",{}))
                for k in reads:
                    if k in s and blk.get("name") in ("Read","Bash","Grep"): reads[k]+=1
        u=m.get("usage")
        if not u or m.get("id") in seen: continue
        seen.add(m.get("id")); c+=1
        for k in t: t[k]+=u.get(k,0)
    per.append((i, c, t)); calls+=c
    for k in tot: tot[k]+=t[k]
total = sum(tot.values())
print(f"## Token usage: {label}\n")
print(f"- agents counted: {len(ids)} (main + {len(ids)-1} children) | API calls: {calls}")
print(f"- reads mentioning notes.md/map.md/AGENTS.md in tool inputs: {reads}")
print("\n| Part | API calls | Input | Cache write | Cache read | Output | Total |\n|---|---|---|---|---|---|---|")
for i,c,t in per:
    print(f"| {'main' if i==aid else 'child'} | {c} | {t['input_tokens']} | {t['cache_creation_input_tokens']} | {t['cache_read_input_tokens']} | {t['output_tokens']} | {sum(t.values())} |")
print(f"| **all** | {calls} | {tot['input_tokens']} | {tot['cache_creation_input_tokens']} | {tot['cache_read_input_tokens']} | {tot['output_tokens']} | **{total}** |")
