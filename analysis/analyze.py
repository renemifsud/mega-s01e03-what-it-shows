#!/usr/bin/env python3
"""Reproducible analysis of ticket #4471 (kb export). Read-only.
Usage: python3 analyze.py [--json]"""
import json, re, sys, collections as C, datetime as D, pathlib
ROOT = pathlib.Path(__file__).parent / "kb/support-kb/src/lib/data"
raw = json.loads((ROOT / "reports-4471.json").read_text())
tenants = {json.loads(p.read_text())["handle"]: json.loads(p.read_text()) for p in (ROOT / "tenants").glob("*.json")}
notes = json.loads((ROOT / "desk-notes.json").read_text())

# 1. one id, one report (causes.ts uniqueById: last row wins; rows are identical anyway)
byid = {}
dups = C.Counter(r["id"] for r in raw)
for r in raw: byid[r["id"]] = r
reports = [r for r in byid.values() if r["mergedInto"] == 4471]

MONTHS = {m: i+1 for i, m in enumerate("January February March April May June July August September October November December".split())}
DATE = re.compile(r"(?:(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) )?(\d{1,2}) (" + "|".join(MONTHS) + ")")
WD = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()

def symptom(body):
    ds = [(w, int(d), MONTHS[m]) for w, d, m in DATE.findall(body)]
    if len(ds) >= 2:
        (_, d1, m1), (_, d2, m2) = ds[0], ds[1]
        if d1 == m2 and m1 == d2: return "swap", ds
        a, b = D.date(2026, m1, d1), D.date(2026, m2, d2)
        if abs((a - b).days) == 1: return "one-day", ds
        return "other", ds
    if re.search(r"one day off|showed as (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\.|got (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b.*got", body):
        return "one-day", ds
    if re.search(r"October bookings came through for January", body): return "swap", ds
    return "vague", ds

def day_first(locale):
    # same question causes.ts asks Intl; answered from CLDR for these locales (all day-first; en-US is not)
    return locale != "en-US"

def code_cause(r):  # causes.ts causeOf, verbatim logic
    t = tenants.get(r["tenant"])
    if not t or not day_first(t["locale"]): return None
    return "hint" if r["channel"] == "form" and t["form"] == "booking-v3" else "parser"

rows = []
for r in reports:
    s, ds = symptom(r["body"])
    cc = code_cause(r)
    t = tenants[r["tenant"]]
    if s == "one-day" or r["id"] in notes["oneDayMove"]: problem = "one-day"
    elif cc == "hint": problem = "hint"
    else: problem = "parser"
    rows.append(dict(id=r["id"], tenant=r["tenant"], form=t["form"], locale=t["locale"], channel=r["channel"],
                     subject=r["subject"], tag=r["meta"]["intakeTag"], browser=r["meta"]["browserLocale"],
                     symptom=s, code=cc, problem=problem, received=r["receivedAt"], body=r["body"]))

json.dump({p: [x["id"] for x in rows if x["problem"] == p] for p in ["parser", "hint", "one-day"]}, open(pathlib.Path(__file__).parent / "drafts/ids-by-problem.json", "w"), indent=1)
if "--json" in sys.argv:
    print(json.dumps(rows, indent=1)); sys.exit()

print(f"rows in export: {len(raw)}  unique ids: {len(byid)}  duplicate rows: {sum(n-1 for n in dups.values() if n>1)} ({sorted(k for k,n in dups.items() if n>1)})")
print(f"merged into #4471 after dedupe: {len(reports)}")
print("symptom x code-cause:", dict(C.Counter((x['symptom'], x['code']) for x in rows)))
print()
for p in ["parser", "hint", "one-day"]:
    g = [x for x in rows if x["problem"] == p]
    print(f"== {p}: {len(g)} reports")
    print("  tenants:", dict(C.Counter(x['tenant'] for x in g).most_common()))
    print("  channels:", dict(C.Counter(x['channel'] for x in g)), " forms:", dict(C.Counter(x['form'] for x in g)))
    print("  symptom:", dict(C.Counter(x['symptom'] for x in g)), " intakeTag:", dict(C.Counter(x['tag'] for x in g)))
    days = sorted(x['received'][:10] for x in g); print("  seen:", days[0], "->", days[-1])
    print("  examples:", [x['id'] for x in g][:8])
    if p == "one-day":
        for x in g: print("   ", x['id'], x['tenant'], x['channel'], x['received'], '|', x['body'])
    if p in ("parser","hint"):
        v = [x for x in g if x['symptom']=='vague']
        for x in v: print("   vague:", x['id'], x['tenant'], x['channel'], '|', x['body'])
print()
print("desk-notes oneDayMove:", notes["oneDayMove"], "-> found by body:", [i for i in notes['oneDayMove'] if next(x for x in rows if x['id']==i)['problem']=='one-day'])
print("intakeTag vs problem:", dict(C.Counter((x['tag'], x['problem']) for x in rows)))
print("subjects per problem:"); [print("  ", p, dict(C.Counter(x['subject'] for x in rows if x['problem']==p))) for p in ["parser","hint","one-day"]]
