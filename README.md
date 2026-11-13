# Pipeline Factory — Qodo Hackathon entry

**An AI-assisted software factory: backlog ticket → governed data pipeline,
with review, verification, and a human approval gate.**

Built for the [Qodo Hackathon](https://hackathon.qodo.ai/) (Nov 2 – Dec 2, 2026).
Final submission: Dec 2, 2026, midnight PT. Judging by Dec 9.

## The factory loop

```
backlog ticket ──> spec ──> generate ──> review ──> verify ──> approve / escalate
   (PF-1)      (YAML)    (code+tests)  (Qodo/local) (tests, policy, gates) (human gate)
```

1. **Backlog** — a ticket arrives (local `backlog.yaml`, or `gh issue list`).
   The factory drafts a pipeline spec from it.
2. **Spec** — one YAML file describing a governed pipeline: source schema
   (with PII flags), transforms (deidentify / validate / derive), quality
   gates (completeness / uniqueness), destination (governed + quarantine).
3. **Generate** — the factory writes real, runnable pipeline code
   (stdlib-only Python), a pytest suite, and docs from the spec.
4. **Review** — local static review (security / correctness / best
   practice) plus import of real Qodo review findings; the PR Resolver
   pattern picks a scope (high / medium / all) and plans fixes.
5. **Verify** — the generated tests run, policy checks run (no hardcoded
   secrets, every PII field de-identified, `eval` confined to the
   restricted `_derive` helper), and quality gates are measured on a
   synthetic-data run.
6. **Gate** — a human approves or escalates. Approval is blocked unless
   verification passed. Every decision is written to the evidence log.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -e .[dev]
.venv/bin/factory demo          # full loop on the sample spec
.venv/bin/python -m pytest tests/ -q   # factory's own tests (24)
```

## Commands

```bash
factory validate <spec.yaml>
factory generate <spec.yaml> [--out DIR]
factory verify   <spec.yaml> [--out DIR] [--work DIR]
factory review   <file.py...> [--qodo findings.json] [--scope high|medium|all]
factory approve  <run-id> <spec.yaml>
factory escalate <run-id> [--qodo findings.json]
factory backlog  list [--file backlog.yaml] [--repo owner/name]
factory backlog  spec <issue-id>
factory intake   [--file backlog.yaml] [--repo owner/name] [--specs-dir DIR] [--state FILE]
factory evidence
factory demo
```

`factory intake` is one poll cycle of the Day 4 recurring intake job:
it picks up "Ready to Build" tickets and drafts their specs. Schedule
it, e.g. `*/30 * * * * factory intake`.

## Layout

| Path | What it is |
| --- | --- |
| `src/pipeline_factory/` | the factory itself (spec, generate, verify, review, gate, backlog, intake, evidence, cli) |
| `examples/specs/patient-intake.yaml` | sample spec: synthetic patient intake (demo data only) |
| `examples/specs/lab-results-intake.yaml` | spec drafted by the intake job from ticket PF-3 (Day 4) |
| `examples/backlog.yaml` | sample backlog (PF-1, PF-2, PF-3 — PF-3 labelled "Ready to Build") |
| `examples/generated/` | factory output for the sample specs |
| `evidence/events.jsonl` | append-only evidence log (every generate/verify/review/gate/intake) |
| `evidence/intake-state.json` | intake state: processed issue ids (idempotency) |
| `evidence/day5-first-reviewed-pr/` | Day 5 evidence: full loop run `day5-run-001`, approved |
| `CHALLENGES.md` | the 23 weekday challenges, mapped to evidence |
| `docs/design.md` | design notes + factory standards |

## Design lineage (disclosure)

The factory's governance patterns — de-identification before any other
processing, quarantine instead of silent drops, quality gates on output,
and an append-only audit trail — follow Preet Mehta's HIPAA-oriented
pipeline framework (github.com/ynpreet/hipaa-pipeline-framework,
Apache-2.0). All code in this repo was written during the hackathon
(Nov 12 – Dec 2, 2026); nothing from the framework repo was copied in.

## Status (Nov 12, 2026 — Day 9)

- v0.1 working end to end: `factory demo` passes 7/7 verification checks
  and the gate approves; **24/24 factory tests pass**; generated pipeline
  runs on synthetic data (49 governed / 1 quarantined, no raw PII in
  governed output).
- **Day 4 intake built:** `factory intake` polls the backlog for
  "Ready to Build" tickets, drafts their specs (PF-3 →
  `examples/specs/lab-results-intake.yaml`, validated and verified 7/7),
  is idempotent via `evidence/intake-state.json`, and logs every run.
  Schedule it with cron (`*/30 * * * * factory intake`).
- **Day 5 first reviewed PR:** full loop run Nov 12 (run `day5-run-001`),
  approved — artifacts in `evidence/day5-first-reviewed-pr/`.
- Bug found and fixed while exercising the intake-drafted spec:
  `verify.py` ran pytest with cwd set to the test file's directory while
  passing a relative path, so `factory verify --out <relative>` failed
  the "generated tests" check even though the tests pass. Fixed by
  resolving both dirs to absolute paths, with a regression test
  (`test_verify_works_with_relative_dirs`). The failed run and the fix
  are both in the evidence log.
- Registration confirmed Nov 12 (email from info@qodo.ai, 17:41 ET);
  no daily challenge emails had arrived as of Nov 12, so the challenge
  log is built from the public roadmap + public posts and will be
  reconciled against the daily emails as they arrive (first one
  expected Nov 13).
- **Not done yet (needs Preet's tap):** create the public GitHub repo,
  push the code, and submit via the GitHub Discussion thread linked in
  the daily emails. A repo or social post alone does not count as an
  entry — the Discussion submission is the entry.

## Submission checklist

- [x] Working factory, tests green, evidence log
- [x] Demo run end to end (backlog → approve)
- [ ] Public GitHub repo created + code pushed (needs Preet's tap)
- [ ] Qodo account + free licence confirmed (registration in progress)
- [ ] Daily challenge evidence reconciled as emails arrive
- [ ] Final submission via GitHub Discussion thread (needs Preet's tap)
- [ ] Demo video / screenshots for the submission
