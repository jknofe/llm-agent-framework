import re
rows=[]
for line in open("/tmp/benchmark/results/seq-ledger.md"):
    c=[x.strip() for x in line.strip().strip("|").split("|")]
    if len(c)<9 or not c[0].isdigit(): continue
    rows.append(dict(rep=int(c[0]),arm=c[1],s=c[2],task=c[3],gate=c[4],cog=c[5],steps=int(c[6]),out=int(c[7]),tot=int(c[8]),dur=c[9]))
def get(rep,arm,s): return next((r for r in rows if r["rep"]==rep and r["arm"]==arm and r["s"]==s),None)
print("## Marginal (T2+T3) per replication\n")
print("| Rep | Arm | Steps | Output | Total | T2 total | T3 total | T3 vs T2 |\n|---|---|---|---|---|---|---|---|")
wins=0
for rep in (1,2,3):
    vals={}
    for arm in ("F","B"):
        a,b=get(rep,arm,"s2"),get(rep,arm,"s3")
        if not (a and b): continue
        vals[arm]=(a["steps"]+b["steps"],a["out"]+b["out"],a["tot"]+b["tot"],a["tot"],b["tot"])
        print(f"| {rep} | {arm} | {vals[arm][0]} | {vals[arm][1]:,} | {vals[arm][2]:,} | {a['tot']:,} | {b['tot']:,} | {100*(b['tot']-a['tot'])/a['tot']:+.0f}% |")
    if "F" in vals and "B" in vals:
        d=100*(vals["F"][2]-vals["B"][2])/vals["B"][2]; wins+= vals["F"][2]<vals["B"][2]
        print(f"| {rep} | F vs B | | | **{d:+.0f}%** | | | |")
print(f"\nFramework marginal cheaper in {wins} of 3 replications.\n")
print("## Total sequence per replication\n")
print("| Rep | F (s0+T1+T2+T3) | B (T1+T2+T3) | F vs B |\n|---|---|---|---|")
for rep in (1,2,3):
    F=[get(rep,"F",s) for s in ("s0","s1","s2","s3")]; B=[get(rep,"B",s) for s in ("s1","s2","s3")]
    if all(F) and all(B):
        f=sum(r["tot"] for r in F); b=sum(r["tot"] for r in B)
        print(f"| {rep} | {f:,} | {b:,} | {100*(f-b)/b:+.0f}% |")
print("\n## Correctness and knowledge signals\n")
print("| Arm | T1 gate PASS | T2/T3 hidden PASS | COG clean (T2,T3) |\n|---|---|---|---|")
for arm in ("F","B"):
    t1=sum(1 for r in rows if r["arm"]==arm and r["s"]=="s1" and r["gate"].startswith("PASS"))
    h=sum(1 for r in rows if r["arm"]==arm and r["s"] in("s2","s3") and "hidden 3/3" in r["gate"])
    cg=sum(1 for r in rows if r["arm"]==arm and r["s"] in("s2","s3") and r["cog"].startswith("0"))
    n=sum(1 for r in rows if r["arm"]==arm and r["s"] in("s2","s3"))
    print(f"| {arm} | {t1}/3 | {h}/{n} | {cg}/{n} |")
