"""Demo: the full factory loop on the sample spec, end to end.

  backlog ticket -> spec -> generate -> verify -> review -> approve gate

Run:  factory demo     (or python -m pipeline_factory demo)
"""

from __future__ import annotations

from pathlib import Path

from .backlog import load_backlog
from .evidence import EvidenceLog
from .gate import approve
from .generate import generate
from .review import local_review, resolve_findings
from .spec import load_spec
from .verify import verify


def run_demo() -> int:
    root = Path.cwd()
    spec_path = root / "examples" / "specs" / "patient-intake.yaml"
    print("== 1. BACKLOG: ticket -> spec ==")
    issues = load_backlog(root / "examples" / "backlog.yaml")
    for issue in issues:
        print(f"   {issue.id}: {issue.title}")
    spec = load_spec(spec_path)
    print(f"   spec: {spec.name} v{spec.version} "
          f"({len(spec.source.schema)} columns, {len(spec.transforms)} transforms)")

    print("== 2. GENERATE: spec -> code + tests + docs ==")
    generated = root / "examples" / "generated"
    log = EvidenceLog(root / "evidence" / "events.jsonl")
    files = generate(spec, generated)
    for key, path in files.items():
        print(f"   {key}: {path}")
    log.record("generate", {"spec": spec.name, "files": [str(p) for p in files.values()]})

    print("== 3. VERIFY: tests + policy + quality gates ==")
    work = generated / ".work"
    report = verify(spec, generated, work)
    for check in report.checks:
        mark = "PASS" if check.passed else "FAIL"
        print(f"   [{mark}] {check.name} — {check.detail}")
    print(f"   => {'PASSED' if report.passed else 'FAILED'}")
    log.record("verify", {
        "spec": spec.name,
        "passed": report.passed,
        "checks": [(c.name, c.passed) for c in report.checks],
    })

    print("== 4. REVIEW: local review + PR Resolver plan ==")
    findings = local_review([files["pipeline"]])
    plan = resolve_findings(findings, scope="high")
    print(plan.summary() or "   no high-severity findings")
    log.record("review", {
        "files": [str(files["pipeline"])],
        "findings": len(findings),
        "scope": "high",
    })

    print("== 5. GATE: approve or escalate ==")
    decision = approve("demo-run-001", report, log)
    print(f"   {decision.decision}: {decision.reason}")
    print(f"   evidence: {log.path}")
    return 0 if decision.decision == "approved" else 1
