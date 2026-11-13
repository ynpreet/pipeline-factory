# Day 5 — First reviewed PR (evidence)

**Run:** Nov 12, 2026, ~22:49 UTC · **Run id:** `day5-run-001`
**Ticket:** PF-1 — Governed intake pipeline for synthetic patient records

One full factory loop, ticket → spec → generate → review → verify →
approve, run with the real CLI commands. Every step is in the
append-only evidence log (`evidence/events.jsonl`).

## The loop

| Step | Command | Result | Artifact |
| --- | --- | --- | --- |
| 1. Ticket → spec | `factory backlog spec PF-1` | Spec drafted from the PF-1 issue's embedded YAML block | `spec-patient-intake.yaml` |
| 2. Generate | `factory generate examples/specs/patient-intake.yaml` | Pipeline + tests + docs written | `pipeline_patient-intake.py`, `test_pipeline_patient-intake.py`, `generated-README.md` |
| 3. Review | `factory review examples/generated/patient-intake/pipeline_patient-intake.py` | 4 findings, all lower severity; 0 selected at scope `high`, 4 deferred to the next round | `review-report.txt` |
| 4. Verify | `factory verify examples/specs/patient-intake.yaml` | **PASSED 7/7** — generated tests 6 passed; no hardcoded secrets; all PII de-identified; eval confined to `_derive`; synthetic run 49 governed / 1 quarantined; completeness 1.000; uniqueness 1.000 | `verify-report.txt` |
| 5. Gate | `factory approve day5-run-001 examples/specs/patient-intake.yaml` | **approved** — "all 7 verification checks passed" | `gate-decision.txt` |

## Evidence-log entries (Nov 12, 2026)

- `generate` — spec `patient-intake`, 3 files
- `review` — 4 findings, scope `high`
- `verify` — spec `patient-intake`, passed, 7/7 checks
- `gate_decision` — run `day5-run-001`, decision `approved`,
  approver `preet-mehta`

## Honest note

The log also records a failed verify earlier the same day on the
intake-drafted `lab-results-intake` spec (6/7 — "generated tests"
failed with a file-not-found error). Root cause was a real bug in
`verify.py`: it ran pytest with cwd set to the test file's directory
while passing a relative path, so the path was unresolvable whenever
`--out` was relative. Fixed in `verify.py` (resolve both dirs to
absolute paths) with a regression test
(`test_verify_works_with_relative_dirs`); the re-run then passed 7/7.
The failure and the fix are both on file — the factory's own tests
went from 15 to 24 in the process.
