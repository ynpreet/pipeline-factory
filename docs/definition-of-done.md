# Definition of Done — Pipeline Factory

(Qodo Hackathon Day 9 — "Set standards for your project." Carried
into Day 10's factory diagram.)

A change is **done** only when every item below is true. "Done" means
verified and reviewable, not merely changed.

## The checklist

1. **Generated tests pass.** The pipeline's generated pytest suite
   runs green.
2. **Policy checks pass.** No hardcoded secrets; every PII field is
   de-identified; `eval` is confined to the restricted `_derive`
   helper.
3. **Quality gates pass on a synthetic-data run.** Completeness and
   uniqueness meet their thresholds (e.g. completeness >= 0.95,
   uniqueness >= 1.0); governed vs quarantined rows are split with
   reasons, nothing silently dropped.
4. **Review findings are settled.** Valid **high** and **medium**
   issues are fixed and the fixes verified. **Low** issues are flagged
   for the human's decision, not silently fixed or silently dropped.
   (PR Resolver pattern: read findings → choose scope → resolve.)
5. **Required checks pass and a Qodo review of the current PR head
   is complete.** Before merge, the required checks must be green and
   the current head must have a completed Qodo review.
6. **Human gate approves.** Approve is blocked unless verification
   passed. A human approves or escalates; the decision is logged.
7. **Evidence is on file.** The generate / review / verify / gate
   steps are in the append-only evidence log
   (`evidence/events.jsonl`), with their artifacts saved.

## How a stall is handled

If a fix-and-review loop stalls — a fix that reverses a prior
decision, a finding that keeps coming back, or a disagreement the
agent cannot resolve with evidence — the loop **stops** and the item
is escalated to the human with the evidence on both sides. The agent
does not loop forever and does not merge around a disagreement.

## What "done" is not

- A PR opened but not reviewed.
- Tests passing while a policy check fails.
- A review with unaddressed high or medium findings.
- A merge with no evidence-log entry.

## Where it is enforced

`factory verify` runs checks 1–3. `factory review` runs check 4
(local review + PR Resolver plan). `factory approve` enforces check 6
(it refuses to approve unless verification passed). Checks 5 and 7
are enforced by the human at the gate and by the evidence log.
