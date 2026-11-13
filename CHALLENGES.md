# Qodo Hackathon — challenge log (23 weekdays, Nov 2 – Dec 2, 2026)

**Status Nov 13 (Day 10, reconciled):** Preet registered late (Nov 12),
so the daily challenge emails for Nov 2–11 never arrived. The only
daily email received is Day 10 (Nov 13). Days 1–9 below are reconciled
from Qodo's public Instagram posts (@qodo_ai), the hackathon website /
rules / Luma page, and the Day 10 email (which names Day 9's topic).
Nothing is marked DONE without evidence on file in this repo.
Verified Nov 13: **24/24 factory tests pass, demo 7/7 checks, gate
approves.** Repo live: https://github.com/ynpreet/pipeline-factory
(public, 40 files + Day 10 additions).

Legend: ✅ DONE (evidence on file) · 🔄 BUILT (capability exists, but
a named step is not evidenced) · ❓ UNCONFIRMED (exact challenge text
not established — not guessed) · ⏳ upcoming

## Week 1 — Build (Nov 2–6): idea → first reviewed PR

| Day | Date | Challenge | Source | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Mon Nov 2 | **PICK. SHARE. VERIFY.** Pick one project, share the idea publicly, verify by signing up with Qodo, opening a PR, and getting the code reviewed. | Instagram @qodo_ai, reel `DfVZaSYAOAG` (Day One kickoff, posted Nov 4) | 🔄 BUILT | Idea picked (Pipeline Factory); repo set up and public (`ynpreet/pipeline-factory`, 40 files). **Not evidenced:** no GitHub PR was opened and no Qodo PR review is on file — the code was pushed directly to `main` (catch-up). |
| 2 | Tue Nov 3 | **WRITE. REVIEW. SHARE.** Write an AGENTS.md — instructions for the coding agent: project description, setup + verify commands, 3–5 project rules. Commit, push, check Qodo's review. | Instagram @qodo_ai, reel `DfVZk7Kirql` (Day Two, posted Nov 4) | ✅ DONE | `AGENTS.md` (created Nov 13): project description, setup + verify commands, 5 project rules drawn from `docs/design.md` factory standards. |
| 3 | Wed Nov 4 | **CONNECT. BUILD. VERIFY.** Connect a coding agent to the backlog (GitHub issues). | Instagram @qodo_ai, reel `DfWj5uTiecn` (Day Three, posted Nov 5) | ✅ DONE | `src/pipeline_factory/backlog.py` — local backlog + `gh issue list`, issue → spec draft. |
| 4 | Thu Nov 5 | Automate the intake — a recurring job that periodically checks tickets marked "Ready to Build" and runs the coding agent on them. | Instagram @qodo_ai, reel `Dfh-Dc6mbBK` (Day 4, posted Nov 9) | ✅ DONE | `src/pipeline_factory/intake.py` + `factory intake` (schedule `*/30 * * * * factory intake`); `tests/test_intake.py` (8 tests); live run picked PF-3 → `examples/specs/lab-results-intake.yaml` (valid, verified 7/7); idempotent via `evidence/intake-state.json`; every pick logged to `evidence/events.jsonl`. |
| 5 | Fri Nov 6 | First reviewed PR (Week 1 deliverable: "Idea → first reviewed PR"). | Hackathon roadmap (Week 1: "Idea → first reviewed PR", hackathon.qodo.ai) + Instagram @qodo_ai, reel `DfhaJ57DtXf` (Day 5 Week One recap, posted Nov 9) | ✅ DONE | Full loop run Nov 12, run `day5-run-001`, **approved**: `evidence/day5-first-reviewed-pr/` — spec + generated pipeline/tests + review report (4 findings, 0 high) + verify report (7/7) + gate decision; all steps in `evidence/events.jsonl`. Note: a full reviewed loop run, not a GitHub-hosted PR — no PR was opened. |

## Week 2 — Equip your factory (Nov 9–13): the right tools / set standards

| Day | Date | Challenge | Source | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| 6 | Mon Nov 9 | **THE AGENTIC TOOLBOX — Codebase Wisdom. REVIEW A TICKET.** Bring a GitHub Issue or Linear/Jira ticket, have the agent review the implementation plan, and use Codebase Wisdom to check it holds up and avoid reinventing existing solutions. | Instagram @qodo_ai, reel `Dfk8DqbCjR8` (Day 06, posted Nov 10) | 🔄 BUILT | Ticket→spec review flow exists: PF-3 reviewed and drafted to `examples/specs/lab-results-intake.yaml`, validated and verified 7/7. **Not evidenced:** no Qodo Codebase Wisdom tool invocation on file — the review was the factory's own spec validation. |
| 7 | Tue Nov 10 | **PR Resolver** skill — bring Qodo review findings directly to the coding agent (Read Findings → Choose Scope → Resolve; scope high, medium, or custom). | Instagram @qodo_ai, reel `DfmMPQeE9hE` (Day 07, posted Nov 11) | ✅ DONE | `src/pipeline_factory/review.py` — import Qodo findings as JSON, scope (high/medium/all), plan fixes. Exercised in Day 5 run: `evidence/day5-first-reviewed-pr/review-report.txt` (scope `high`, 0 selected, 4 lower-severity deferred). |
| 8 | Wed Nov 11 | (exact challenge text not established) | ❓ No reliable source found — no Day 8 post indexed on Instagram/LinkedIn and no daily email (registered late). | ❓ UNCONFIRMED | Most likely the remaining Agentic Toolbox skill, Qodo local review of staged/unstaged changes before committing (named as a step in the Day 10 email). The factory's local static reviewer in `src/pipeline_factory/review.py` covers that capability, but the Day 8 text itself is **not confirmed — do not treat as done**. |
| 9 | Thu Nov 12 | **Definition of Done.** Settle valid high and medium issues, verify the fixes, and flag low issues for the human's decision. | Day 10 email (Nov 13, msg `1a1d4cc4571e8b2b`): "Carry over yesterday's definition of done" + Luma Week 2 theme "Set standards for your project" | ✅ DONE | `docs/definition-of-done.md` (created Nov 13): the 7-item checklist (tests, policy, quality gates, review settled, required checks + Qodo review of head, human gate, evidence on file) + stall handling. Enforced by `verify.py` + `gate.py` (approve blocked unless verification passed). |
| 10 | Fri Nov 13 | **Factory with verification.** Post a diagram of the factory with its verification steps — path from ticket to main, quality gates at each check, paths back to a fix, decision points — and check it against one small real ticket. | Day 10 email (Nov 13, msg `1a1d4cc4571e8b2b`, from Filip Hric at Qodo) — direct, authoritative | ✅ DONE | `evidence/day10-factory-diagram.md` (created Nov 13): Mermaid flowchart (ticket → Codebase Wisdom → generate → local review → Review Resolver → verify → gate → main) + quality-gates table + check write-up against ticket PF-1 / run `day5-run-001` (what worked, what the human did, 3 honest gaps: no GitHub PR opened, no Qodo review of a PR head, Qodo CLI steps not run). |

## Week 3 — Connect (Nov 16–20): tools + agents + review

| Day | Date | Challenge | Source | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| 11–15 | Nov 16–20 | Connect tools + agents + review end to end | Roadmap (hackathon.qodo.ai) | ⏳ | Factory loop already connects backlog → spec → generate → review → gate; will map to the daily texts as emails arrive. |

## Week 4 — Automate (Nov 23–27): verify → approve or escalate

| Day | Date | Challenge | Source | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| 16–20 | Nov 23–27 | Automate verification; approve or escalate | Roadmap (hackathon.qodo.ai) | ⏳ | `verify.py` (tests + policy + gates) and `gate.py` (approve blocked unless verification passes) already built; will map to the daily texts. |

## Finale (Nov 30 – Dec 2)

| Day | Date | Challenge | Source | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| 21–23 | Nov 30–Dec 2 | Final submission | Roadmap + rules (hackathon.qodo.ai/rules) | ⏳ | Submit via GitHub Discussion thread from the daily emails (needs Preet's tap). Final cutoff: midnight PT Dec 2. `SUBMISSION-FINAL.md` is ready. |

## Weekly merch rounds

Nov 2–8, Nov 9–15, Nov 16–22, Nov 23–29 (close Sundays 23:59 CET).
No weekly submission made yet.

## Honest summary (Nov 13, Day 10)

- **DONE with evidence: Days 2, 3, 4, 5, 7, 9, 10** (7 of 10).
- **BUILT but a named step not evidenced: Days 1, 6** (2 of 10).
  The gap in both is the same: no GitHub PR was opened and no Qodo
  review (PR review, Codebase Wisdom) was run as a Qodo tool
  invocation. The factory's own review/validation covers the
  substance, but the Qodo-side evidence is missing. These close when
  a real PR goes through Qodo review.
- **UNCONFIRMED: Day 8** (1 of 10). Exact text not established; most
  likely Qodo local review. Not marked done.
- The factory itself is complete and green (24/24 tests, demo 7/7,
  gate approves) and the repo is live and public. The remaining work
  is the daily challenges as they arrive (Days 11–23) and the final
  Discussion submission (Nov 30–Dec 2).
