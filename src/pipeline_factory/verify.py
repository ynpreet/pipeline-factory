"""Verification: prove a generated pipeline is safe to approve.

Three layers, mirroring the Week-4 "Verify -> approve or escalate" theme:
  1. tests — run the generated pipeline's own pytest suite.
  2. policy — static checks on the generated code: no hardcoded secrets,
     every PII field is de-identified before output, eval confined to the
     restricted _derive helper.
  3. quality gates — run the pipeline on synthetic data and measure the
     spec's completeness / uniqueness gates on the governed output.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .generate import generate
from .spec import PipelineSpec

SECRET_RE = re.compile(
    r"(api_key|apikey|password|passwd|secret|token)\s*=\s*[\"'][^\"']+[\"']",
    re.IGNORECASE,
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerificationReport:
    spec_name: str
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


def _run_pytest(test_file: Path, cwd: Path) -> Check:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(test_file)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
    return Check(
        name="generated tests",
        passed=proc.returncode == 0,
        detail=summary,
    )


def _policy_checks(source: str, spec: PipelineSpec) -> list[Check]:
    checks: list[Check] = []
    secrets = SECRET_RE.findall(source)
    checks.append(
        Check(
            name="policy: no hardcoded secrets",
            passed=not secrets,
            detail=f"matched: {sorted(set(secrets))}" if secrets else "clean",
        )
    )
    missing = [
        f for f in spec.pii_fields() if f"_deidentify(row[{f!r}])" not in source
    ]
    checks.append(
        Check(
            name="policy: every PII field is de-identified",
            passed=not missing,
            detail=f"not de-identified: {missing}" if missing else "all covered",
        )
    )
    lines = source.splitlines()
    # Lines inside the restricted _derive helper are allowed to use eval.
    derive_start = next(
        (i for i, line in enumerate(lines) if line.startswith("def _derive")), -1
    )
    derive_end = next(
        (i for i, line in enumerate(lines) if i > derive_start and line.startswith("def ")),
        len(lines),
    )
    eval_lines = [
        i + 1
        for i, line in enumerate(lines)
        if "eval(" in line and not (derive_start <= i < derive_end)
    ]
    checks.append(
        Check(
            name="policy: eval confined to _derive",
            passed=not eval_lines,
            detail=f"eval outside _derive at lines {eval_lines}" if eval_lines else "confined",
        )
    )
    return checks


def _synthetic_rows(spec: PipelineSpec, n: int = 50) -> list[dict[str, str]]:
    """Deterministic synthetic rows from the spec (no real data)."""
    rows: list[dict[str, str]] = []
    for i in range(n):
        row: dict[str, str] = {}
        for c in spec.source.schema:
            if c.type == "integer":
                row[c.name] = str(20 + (i % 60))
            elif c.type == "float":
                row[c.name] = str(60.0 + (i % 40))
            elif c.type == "boolean":
                row[c.name] = "true" if i % 2 == 0 else "false"
            elif c.type == "date":
                row[c.name] = f"2026-11-{(i % 28) + 1:02d}"
            elif c.pii:
                row[c.name] = f"Person {i}"
            else:
                row[c.name] = f"CODE-{i % 5}"
        # One deliberately bad row (out of range) to exercise quarantine.
        if i == 7:
            for t in spec.transforms:
                if t.kind == "validate" and t.rule == "range" and t.max_value is not None:
                    row[t.field] = str(int(t.max_value) + 50)
                    break
        rows.append(row)
    return rows


def _quality_gates(spec: PipelineSpec, governed_path: Path) -> list[Check]:
    checks: list[Check] = []
    with open(governed_path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return [Check(name="quality gates", passed=False, detail="no governed rows")]
    for gate in spec.quality_gates:
        if gate.kind == "completeness":
            total = len(rows) * len(spec.source.schema)
            filled = sum(1 for r in rows for c in spec.source.schema if r.get(c.name))
            ratio = filled / total if total else 0.0
            checks.append(
                Check(
                    name=f"gate: completeness >= {gate.threshold}",
                    passed=ratio >= gate.threshold,
                    detail=f"{ratio:.3f}",
                )
            )
        elif gate.kind == "uniqueness":
            values = [r.get(gate.field, "") for r in rows]
            ratio = len(set(values)) / len(values) if values else 0.0
            checks.append(
                Check(
                    name=f"gate: uniqueness({gate.field}) >= {gate.threshold}",
                    passed=ratio >= gate.threshold,
                    detail=f"{ratio:.3f}",
                )
            )
    return checks


def verify(spec: PipelineSpec, generated_dir: str | Path, work_dir: str | Path) -> VerificationReport:
    """Generate (if needed), test, policy-check and quality-gate a spec.

    generated_dir holds the generated code; work_dir holds run outputs.
    Both are resolved to absolute paths: the generated-test run executes
    pytest with cwd set to the test file's directory, so a relative
    generated_dir would make the relative test path unresolvable.
    """
    generated_dir = Path(generated_dir).resolve()
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    files = generate(spec, generated_dir)
    report = VerificationReport(spec_name=spec.name)

    report.checks.append(_run_pytest(files["tests"], cwd=files["tests"].parent))
    source = files["pipeline"].read_text()
    report.checks.extend(_policy_checks(source, spec))

    # Run the generated pipeline on synthetic data for the quality gates.
    import importlib.util

    input_csv = work_dir / "synthetic_input.csv"
    with open(input_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=spec.column_names())
        writer.writeheader()
        writer.writerows(_synthetic_rows(spec))
    spec_loader = importlib.util.spec_from_file_location(
        f"pipeline_{spec.name}", files["pipeline"]
    )
    mod = importlib.util.module_from_spec(spec_loader)
    spec_loader.loader.exec_module(mod)
    gov = work_dir / "governed.csv"
    quar = work_dir / "quarantined.csv"
    audit = work_dir / "audit.jsonl"
    governed, quarantined = mod.run(input_csv, gov, quar, audit_path=audit)
    report.checks.append(
        Check(
            name="pipeline run on synthetic data",
            passed=governed + quarantined == 50,
            detail=f"governed={governed} quarantined={quarantined}",
        )
    )
    report.checks.extend(_quality_gates(spec, gov))
    return report
