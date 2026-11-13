"""Pipeline Factory CLI.

  factory validate <spec.yaml>        validate a pipeline spec
  factory generate <spec.yaml> [--out DIR]
  factory verify <spec.yaml> [--out DIR] [--work DIR]
  factory review <file.py...> [--qodo findings.json] [--scope high|medium|all]
  factory approve <run-id> <spec.yaml>
  factory escalate <run-id> [--qodo findings.json]
  factory backlog list [--file backlog.yaml] [--repo owner/name]
  factory backlog spec <issue-id> [--file backlog.yaml]
  factory intake [--file backlog.yaml] [--repo owner/name]
  factory evidence [--log evidence/events.jsonl]
  factory demo                        run the whole factory loop on the sample spec
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .backlog import gh_issues, issue_to_spec_text, load_backlog
from .evidence import EvidenceLog
from .gate import approve, escalate
from .generate import generate
from .intake import run_intake
from .review import import_qodo_findings, local_review, resolve_findings
from .spec import load_spec
from .verify import verify


def _default_dirs() -> tuple[Path, Path, EvidenceLog]:
    root = Path.cwd()
    generated = root / "examples" / "generated"
    work = root / "examples" / "generated" / ".work"
    log = EvidenceLog(root / "evidence" / "events.jsonl")
    return generated, work, log


def _print_report(report) -> None:
    for check in report.checks:
        mark = "PASS" if check.passed else "FAIL"
        print(f"  [{mark}] {check.name} — {check.detail}")
    print(f"  => {'PASSED' if report.passed else 'FAILED'} "
          f"({sum(c.passed for c in report.checks)}/{len(report.checks)} checks)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="factory", description="Pipeline Factory CLI")
    parser.add_argument("--version", action="version", version=f"factory {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate")
    p.add_argument("spec")
    p = sub.add_parser("generate")
    p.add_argument("spec")
    p.add_argument("--out", default=None)
    p = sub.add_parser("verify")
    p.add_argument("spec")
    p.add_argument("--out", default=None)
    p.add_argument("--work", default=None)
    p = sub.add_parser("review")
    p.add_argument("files", nargs="+")
    p.add_argument("--qodo", default=None)
    p.add_argument("--scope", default="high", choices=["high", "medium", "all"])
    p = sub.add_parser("approve")
    p.add_argument("run_id")
    p.add_argument("spec")
    p = sub.add_parser("escalate")
    p.add_argument("run_id")
    p.add_argument("--qodo", default=None)
    p.add_argument("--reason", default="")
    p = sub.add_parser("backlog")
    p.add_argument("action", choices=["list", "spec"])
    p.add_argument("issue_id", nargs="?", default=None)
    p.add_argument("--file", default="examples/backlog.yaml")
    p.add_argument("--repo", default=None)
    p = sub.add_parser("evidence")
    p.add_argument("--log", default="evidence/events.jsonl")
    p = sub.add_parser("intake")
    p.add_argument("--file", default="examples/backlog.yaml")
    p.add_argument("--repo", default=None)
    p.add_argument("--specs-dir", default="examples/specs")
    p.add_argument("--state", default="evidence/intake-state.json")
    sub.add_parser("demo")

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        try:
            spec = load_spec(args.spec)
        except ValueError as exc:
            print(exc)
            return 1
        print(f"spec OK: {spec.name} v{spec.version} "
              f"({len(spec.source.schema)} columns, "
              f"{len(spec.transforms)} transforms, "
              f"{len(spec.quality_gates)} gates)")
        return 0

    if args.cmd == "generate":
        spec = load_spec(args.spec)
        out = Path(args.out) if args.out else Path("examples/generated")
        files = generate(spec, out)
        _, _, log = _default_dirs()
        log.record("generate", {"spec": spec.name, "files": [str(p) for p in files.values()]})
        for key, path in files.items():
            print(f"{key}: {path}")
        return 0

    if args.cmd == "verify":
        spec = load_spec(args.spec)
        generated, work, log = _default_dirs()
        out = Path(args.out) if args.out else generated
        workdir = Path(args.work) if args.work else work
        report = verify(spec, out, workdir)
        _print_report(report)
        log.record("verify", {
            "spec": spec.name,
            "passed": report.passed,
            "checks": [(c.name, c.passed) for c in report.checks],
        })
        return 0 if report.passed else 1

    if args.cmd == "review":
        files = [Path(f) for f in args.files]
        findings = local_review(files)
        if args.qodo:
            findings += import_qodo_findings(args.qodo)
        plan = resolve_findings(findings, scope=args.scope)
        print(plan.summary())
        print(f"  => {len(plan.selected)} selected, {len(plan.deferred)} deferred")
        _, _, log = _default_dirs()
        log.record("review", {
            "files": [str(f) for f in files],
            "findings": len(findings),
            "scope": args.scope,
        })
        return 0

    if args.cmd == "approve":
        spec = load_spec(args.spec)
        generated, work, log = _default_dirs()
        report = verify(spec, generated, work)
        decision = approve(args.run_id, report, log)
        print(f"{decision.decision}: {decision.reason}")
        return 0 if decision.decision == "approved" else 1

    if args.cmd == "escalate":
        findings = import_qodo_findings(args.qodo) if args.qodo else []
        _, _, log = _default_dirs()
        decision = escalate(args.run_id, findings, log, reason=args.reason)
        print(f"{decision.decision}: {decision.reason}")
        return 0

    if args.cmd == "backlog":
        issues = gh_issues(args.repo) if args.repo else load_backlog(args.file)
        if args.action == "list":
            for issue in issues:
                print(f"{issue.id}: {issue.title} [{', '.join(issue.labels)}]")
            return 0
        for issue in issues:
            if str(issue.id) == str(args.issue_id):
                print(issue_to_spec_text(issue))
                return 0
        print(f"issue {args.issue_id} not found")
        return 1

    if args.cmd == "intake":
        issues = gh_issues(args.repo) if args.repo else load_backlog(args.file)
        _, _, log = _default_dirs()
        run = run_intake(issues, args.specs_dir, log, args.state)
        print(run.summary())
        for issue_id, path in run.spec_files.items():
            print(f"  spec drafted: {issue_id} -> {path}")
        return 0

    if args.cmd == "evidence":
        log = EvidenceLog(args.log)
        print(log.render_markdown())
        return 0

    if args.cmd == "demo":
        from .demo import run_demo

        return run_demo()

    return 0


if __name__ == "__main__":
    sys.exit(main())
