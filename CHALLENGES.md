# Qodo Hackathon — challenge log (23 weekdays, Nov 2 – Dec 2, 2026)

**Status Nov 12 (Day 9):** registration confirmed today (email from
info@qodo.ai, 17:41 ET), so no daily challenge emails have arrived
yet — the first challenge email lands Nov 13. The log below is built
from the public roadmap (hackathon.qodo.ai) and Qodo's public posts,
and will be reconciled against the daily emails as they arrive.
Nothing here is claimed as completed unless evidence is linked.
Verified Nov 12 evening: **24/24 factory tests pass, demo 7/7 checks**;
Day 4 (recurring intake) and Day 5 (first reviewed PR) are now
complete with evidence on file.

Legend: ✅ evidence on file · 🔄 built, awaiting email text to confirm ·
⏳ upcoming

## Week 1 — Build (Nov 2–6): idea → first reviewed PR

| Day | Date | Challenge (as known) | Evidence |
| --- | --- | --- | --- |
| 1 | Mon Nov 2 | Pick the idea, set up the repo | 🔄 Factory scaffolded Nov 12 (catch-up); `src/pipeline_factory/` |
| 2 | Tue Nov 3 | (email text pending) | 🔄 |
| 3 | Wed Nov 4 | CONNECT. BUILD. VERIFY. — connect a coding agent to the backlog (GitHub issues) | ✅ `backlog.py`: local backlog + `gh issue list`, issue → spec draft |
| 4 | Thu Nov 5 | Automate the intake — recurring job picks up "Ready to Build" tickets | ✅ `src/pipeline_factory/intake.py` + `factory intake` (cron: `*/30 * * * * factory intake`); `tests/test_intake.py` (8 tests); live run picked PF-3 → `examples/specs/lab-results-intake.yaml` (valid, verified 7/7); idempotent via `evidence/intake-state.json`; every pick logged to `evidence/events.jsonl` |
| 5 | Fri Nov 6 | First reviewed PR | ✅ Full loop run Nov 12, run `day5-run-001`, **approved**: `evidence/day5-first-reviewed-pr/` — spec + generated pipeline/tests + review report (4 findings, 0 high) + verify report (7/7) + gate decision; all steps in `evidence/events.jsonl` |

## Week 2 — Equip your factory (Nov 9–13): the right tools

| Day | Date | Challenge (as known) | Evidence |
| --- | --- | --- | --- |
| 6 | Mon Nov 9 | Equip: pick the tools | 🔄 Factory toolset: backlog → intake → spec → generate → verify → review → gate |
| 7 | Tue Nov 10 | PR Resolver skill — Qodo review findings straight to the coding agent | ✅ `review.py`: import Qodo findings, scope (high/medium/all), fix plan |
| 8 | Wed Nov 11 | (email text pending) | 🔄 |
| 9 | Thu Nov 12 | (email text pending) | ✅ v0.1 complete: 24/24 tests, demo 7/7 checks, gate approves; Day 4 intake + Day 5 first reviewed PR closed with evidence |
| 10 | Fri Nov 13 | (email text pending) | ⏳ First daily challenge email expected Nov 13 — reconcile against this log |

## Week 3 — Connect (Nov 16–20): tools + agents + review

| Day | Date | Challenge (as known) | Evidence |
| --- | --- | --- | --- |
| 11–15 | Nov 16–20 | Connect tools + agents + review end to end | ⏳ Factory loop already connects backlog → spec → generate → review → gate; will map to the daily texts |

## Week 4 — Automate (Nov 23–27): verify → approve or escalate

| Day | Date | Challenge (as known) | Evidence |
| --- | --- | --- | --- |
| 16–20 | Nov 23–27 | Automate verification; approve or escalate | ✅ `verify.py` (tests + policy + gates) and `gate.py` (approve blocked unless verification passes) already built; will map to the daily texts |

## Finale (Nov 30 – Dec 2)

| Day | Date | Challenge | Evidence |
| --- | --- | --- | --- |
| 21–23 | Nov 30–Dec 2 | Final submission | ⏳ Submit via GitHub Discussion thread from the daily emails (needs Preet's tap). Final cutoff: midnight PT Dec 2. |

## Weekly merch rounds

Nov 2–8, Nov 9–15, Nov 16–22, Nov 23–29 (close Sundays 23:59 CET).
No weekly submission made yet — first weekly submission goes in once
the daily email texts are reconciled.
