#!/usr/bin/env python3
"""The desk's view of a merged ticket, from a kb export (zip or unpacked dir).
Runs the kb's own rule (src/lib/kb/causes.ts + CauseTable.svelte):
  one id, one report (uniqueById, last row wins) -> keep mergedInto == ticket
  -> cause by tenant (locale via Node Intl, the same call dayFirst() makes) and way in
  -> desk-notes.json: oneDayMove ids split out as 'one-day'; any other key is reported, not guessed.
Usage:
  python3 desk_view.py EXPORT [--ticket 4471] [--old OLD_EXPORT] [--json]
"""
import json, sys, zipfile, subprocess, argparse, collections as C, pathlib, io

def load(path):
    p = pathlib.Path(path)
    files = {}
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.endswith(".json"): files[n] = z.read(n).decode()
    else:
        for f in p.rglob("*.json"):
            if "node_modules" not in f.parts: files["/" + f.resolve().as_posix()] = f.read_text()
    pick = lambda suffix: [v for k, v in files.items() if k.endswith(suffix)]
    reports = [r for s in pick("src/lib/data/reports-4471.json") for r in json.loads(s)]
    notes = json.loads((pick("src/lib/data/desk-notes.json") or ["{}"])[0])
    tenants = {t["handle"]: t for k, v in files.items() if "/src/lib/data/tenants/" in k for t in [json.loads(v)]}
    return reports, notes, tenants

def day_first(locales):
    js = ("const L=JSON.parse(process.argv[1]);const o={};for(const l of L){const p=new Intl.DateTimeFormat(l,{year:'numeric',month:'2-digit',day:'2-digit'})"
          ".formatToParts(new Date(Date.UTC(2026,0,2,12))).map(x=>x.type);o[l]=p.indexOf('day')<p.indexOf('month')}console.log(JSON.stringify(o))")
    return json.loads(subprocess.check_output(["node", "-e", js, json.dumps(sorted(locales))]))

def view(path, ticket):
    reports, notes, tenants = load(path)
    df = day_first({t["locale"] for t in tenants.values()})
    uniq = list({r["id"]: r for r in reports}.values())
    merged = [r for r in uniq if r.get("mergedInto") == ticket]
    one_day = set(notes.get("oneDayMove", []))
    def cause(r):
        t = tenants.get(r["tenant"])
        if not t or not df[t["locale"]]: return "unplaced"
        return "hint" if r["channel"] == "form" and t["form"] == "booking-v3" else "parser"
    out = C.defaultdict(list)
    for r in merged:
        out["one-day" if r["id"] in one_day else cause(r)].append(r)
    return dict(rows=len(reports), unique=len(uniq), merged=len(merged), notes_keys=sorted(notes),
                desk_table={k: sum(1 for r in merged if cause(r) == k) for k in ("parser", "hint", "unplaced")},
                problems={k: dict(count=len(v), tenants=dict(C.Counter(r["tenant"] for r in v).most_common()),
                                  first=min(r["receivedAt"][:10] for r in v), last=max(r["receivedAt"][:10] for r in v),
                                  ids=[r["id"] for r in v]) for k, v in out.items()},
                _byid={r["id"]: r for r in uniq})

a = argparse.ArgumentParser(); a.add_argument("export"); a.add_argument("--ticket", type=int, default=4471)
a.add_argument("--old"); a.add_argument("--json", action="store_true"); o = a.parse_args()
v = view(o.export, o.ticket)
if o.json:
    print(json.dumps({k: x for k, x in v.items() if k != "_byid"}, indent=1)); sys.exit()
print(f"rows {v['rows']} · unique ids {v['unique']} · merged into #{o.ticket}: {v['merged']} · desk-notes keys {v['notes_keys']}")
print("desk CauseTable (by tenant, one-day moves left in place):", v["desk_table"])
for k, p in sorted(v["problems"].items(), key=lambda x: -x[1]["count"]):
    print(f"  {k:8} {p['count']:4}  tenants {len(p['tenants'])}  seen {p['first']} -> {p['last']}  e.g. {p['ids'][:5]}")
if o.old:
    w = view(o.old, o.ticket)
    A, B = w["_byid"], v["_byid"]
    print(f"\nvs {o.old}: added ids {sorted(set(B)-set(A))[:30]} removed ids {sorted(set(A)-set(B))[:30]}")
    ch = [i for i in set(A) & set(B) if A[i] != B[i]]
    print(f"changed reports: {len(ch)}", [(i, [k for k in B[i] if A[i].get(k) != B[i].get(k)]) for i in sorted(ch)[:20]])
    for k in v["problems"].keys() | w["problems"].keys():
        print(f"  {k}: {w['problems'].get(k, {}).get('count', 0)} -> {v['problems'].get(k, {}).get('count', 0)}")
