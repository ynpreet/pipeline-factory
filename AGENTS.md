# AGENTS.md — Pipeline Factory

Instructions for any coding agent working in this repo. Read this
before changing code. (Qodo Hackathon Day 2 — "WRITE. REVIEW. SHARE.")

## Project description

Pipeline Factory is an AI-assisted software factory. A backlog ticket
goes in; a governed, reviewed, verified data pipeline comes out, with
a human approval gate at the end.

```
backlog ticket ──> spec ──> generate ──> review ──> verify ──> approve / escalate
```

It is the machine that builds pipelines, not a single pipeline.
Stdlib-only Python. Licence: Apache-2.0.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -e .[dev]
```

## Verify (run these before claiming anything works)

```bash
.venv/bin/python -m pytest tests/ -q   # factory's own tests (24)
.venv/bin/factory demo                  # full loop on the sample spec (7/7 checks)
```

A claim alone is not evidence. If the tests or the demo fail, the
work is not done — reproduce the failure first (see rule 3), then fix
it, then re-run both commands.

## Project rules (5)

1. **De-identify PII first.** PII is hashed before any other step
   touches a row. Raw PII never reaches governed output.
2. **Quarantine, don't drop.** Invalid rows go to a quarantine file
   with a reason, so nothing is silently lost.
3. **Reproduce the bug, then choose a fix.** Reproduce a failure
   through the actual user path before changing code, verify the same
   path after, and add a regression test for the fix. (This rule
   caught a real bug: `verify.py` failed with relative `--out` dirs;
   fixed by resolving both dirs to absolute paths, with regression
   test `test_verify_works_with_relative_dirs`.)
4. **Audit everything.** Every generate / verify / review / gate
   decision is one JSON line in `evidence/events.jsonl`. If it is not
   in the log, it did not happen.
5. **Synthetic data only; deterministic generation.** The demo uses
   invented patient records — no real PHI, no credentials, no secrets
   anywhere in the repo. The same spec always produces the same
   pipeline; if the output changes, the spec changed, and the diff
   shows it.

## Layout

- `src/pipeline_factory/` — the factory (spec, generate, verify,
  review, gate, backlog, intake, evidence, cli)
- `examples/specs/` — sample specs; `examples/backlog.yaml` — sample
  backlog (PF-1, PF-2, PF-3)
- `examples/generated/` — factory output for the sample specs
- `tests/` — factory tests (24)
- `evidence/` — append-only evidence log + per-day evidence folders
- `docs/` — design notes, definition of done, factory diagram
- `CHALLENGES.md` — the 23 weekday challenges, mapped to evidence
