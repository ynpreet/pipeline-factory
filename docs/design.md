# Design notes — Pipeline Factory

## What the factory is

A software factory that turns a backlog ticket into a governed data
pipeline, with a human in the approval loop. The factory is the product:
it is not a single pipeline, it is the machine that builds pipelines.

## The loop, and why each step exists

1. **Backlog → spec.** A ticket is a wish; a spec is a contract. The
   factory drafts the contract from the ticket, and a human fills the
   schema. Nothing is generated from an unreviewed ticket.
2. **Spec → code.** Generation is deterministic templating, not vibes:
   the same spec always produces the same pipeline. That makes review
   and verification meaningful.
3. **Review.** Two sources: a local static checker (security /
   correctness / best practice) and real Qodo review findings imported
   as JSON. The PR Resolver pattern (read findings → choose scope →
   plan fixes) keeps the human in control of what gets fixed now.
4. **Verify.** Three layers: the generated tests run; policy checks run
   (no hardcoded secrets, every PII field de-identified, `eval`
   confined to the restricted `_derive` helper); quality gates are
   measured on a synthetic-data run. A claim alone is not evidence.
5. **Gate.** Approve is blocked unless verification passed. Escalate
   sends findings back to the agent. Every decision is logged.

## Factory standards (the factory eats its own dog food)

- **De-identify first.** PII is hashed before any other step touches a
  row. Raw PII never reaches governed output.
- **Quarantine, don't drop.** Invalid rows go to a quarantine file with
  a reason, so nothing is silently lost.
- **Audit everything.** Every generate / verify / review / gate decision
  is one JSON line in `evidence/events.jsonl`.
- **Synthetic data only.** The demo uses invented patient records. No
  real PHI, no credentials, no secrets anywhere in the repo.
- **Deterministic generation.** Same spec → same code. If the output
  changes, the spec changed, and the diff shows it.

## What is deliberately not built yet

- Qodo review integration beyond the findings importer (the free Qodo
  licence and daily-email Discussion links arrive with registration).
- A recurring automation job (PF-2 in the backlog) — Week 4 will decide
  its shape from the daily challenges.
- The public GitHub repo and the Discussion submission — both need
  Preet's tap, and the repo must stay local until then.
