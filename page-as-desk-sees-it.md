<!-- Plain rendering of src/routes/kb/incidents/4471/problems/+page.svx through layouts/runbook.svelte,
     with the components evaluated against the 2026-10-04 export. Rendered as of 2026-10-29.
     Counts and the "days ago" are computed at render time, so they move as the desk keeps working. -->

support desk · kb

# #4471 · three problems, not one

owner **René Mifsud** · (open) · reviewed 2026-10-29 · 0 days ago

[#4471](/kb/incidents/4471) merged every report about dates by subject line. Read by cause, the
reports split into three problems. Each one now has its own ticket.

> ⚠ Fixing the parser does not close #4471. Two of the three problems survive that fix.

## The problems

**412** reports merged into #4471 · **3** problems

| problem | reports | tenants | seen |
|---|---|---|---|
| `parser` | 374 | 11 | 2026-04-01 → 2026-10-04 |
| `hint` | 33 | 3 | 2026-04-17 → 2026-09-22 |
| `one-day` | 5 | 5 | 2026-04-02 → 2026-10-04 |

1. **parser**: the shared parser reads every date month first. Our tenants write the day first,
   so day and month swap. Ticket: renemifsud/mega-s01e03-what-it-shows#1.
2. **hint**: the booking-v3 form prints `MM/DD/YYYY` under its date field and then reads the
   date day first. People type what the hint says. Day and month swap. Ticket: renemifsud/mega-s01e03-what-it-shows#2.
3. **one-day**: some dates show one day early, and the day depends on where the reader is.
   Nothing is swapped. Ticket: renemifsud/mega-s01e03-what-it-shows#3.

## How the reports were placed

- One id, one report: the export repeats some rows, and they are counted once.
- The cause comes from the tenant and the way in (`causes.ts`), not the subject and not the intake tag.
- A report the desk read as a one-day move (`desk-notes.json`) counts as **one-day**, not under the tenant's swap cause.

## What to change in triage

Subject lines do not tell causes apart (decision 0001). The same subject turns up in all three
problems. Check the tenant, the form and the way in before merging.

desk ref **DR-PSPH-N8ZF**

---
Pages are written by people. Tables and charts are built from data at render time.
