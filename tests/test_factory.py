"""Factory unit tests: spec validation, generation, review, gate, backlog."""

import textwrap
from pathlib import Path

import pytest

from pipeline_factory.backlog import issue_to_spec_text, load_backlog, Issue
from pipeline_factory.evidence import EvidenceLog
from pipeline_factory.gate import approve, escalate
from pipeline_factory.generate import generate
from pipeline_factory.review import local_review, resolve_findings, Finding
from pipeline_factory.spec import load_spec, parse_spec
from pipeline_factory.verify import VerificationReport, Check

ROOT = Path(__file__).parent.parent
SPEC_PATH = ROOT / "examples" / "specs" / "patient-intake.yaml"


@pytest.fixture()
def spec():
    return load_spec(SPEC_PATH)


def test_example_spec_valid(spec):
    assert spec.name == "patient-intake"
    assert spec.pii_fields() == ["patient_id", "name"]
    assert len(spec.transforms) == 3


def test_spec_rejects_unknown_column():
    with pytest.raises(ValueError, match="unknown column"):
        parse_spec({
            "name": "bad", "source": {"path": "x.csv", "schema": [{"name": "a"}]},
            "transforms": [{"kind": "validate", "field": "nope", "rule": "required"}],
            "destination": {"path": "o.csv", "quarantine_path": "q.csv"},
        })


def test_spec_rejects_deidentify_on_non_pii():
    with pytest.raises(ValueError, match="not flagged pii"):
        parse_spec({
            "name": "bad", "source": {"path": "x.csv", "schema": [{"name": "a"}]},
            "transforms": [{"kind": "deidentify", "fields": ["a"]}],
            "destination": {"path": "o.csv", "quarantine_path": "q.csv"},
        })


def test_spec_rejects_bad_threshold():
    with pytest.raises(ValueError, match="threshold"):
        parse_spec({
            "name": "bad", "source": {"path": "x.csv", "schema": [{"name": "a"}]},
            "quality_gates": [{"kind": "completeness", "threshold": 1.5}],
            "destination": {"path": "o.csv", "quarantine_path": "q.csv"},
        })


def test_generate_writes_all_files(spec, tmp_path):
    files = generate(spec, tmp_path)
    assert files["pipeline"].exists()
    assert files["tests"].exists()
    assert files["readme"].exists()
    source = files["pipeline"].read_text()
    assert "_deidentify" in source
    assert "patient-intake" in source


def test_generated_pipeline_runs(spec, tmp_path):
    import csv
    import importlib.util

    files = generate(spec, tmp_path)
    inp = tmp_path / "in.csv"
    with open(inp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["patient_id", "name", "age",
                                           "diagnosis_code", "visit_date"])
        w.writeheader()
        w.writerow({"patient_id": "P1", "name": "Ann", "age": "40",
                    "diagnosis_code": "E11", "visit_date": "2026-11-01"})
        w.writerow({"patient_id": "P2", "name": "Ben", "age": "200",
                    "diagnosis_code": "I10", "visit_date": "2026-11-02"})
    loader = importlib.util.spec_from_file_location("p", files["pipeline"])
    mod = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(mod)
    gov, quar = mod.run(inp, tmp_path / "g.csv", tmp_path / "q.csv")
    assert (gov, quar) == (1, 1)
    gov_text = (tmp_path / "g.csv").read_text()
    assert "Ann" not in gov_text
    assert "age_band" in gov_text.splitlines()[0]
    assert "18-44" in gov_text  # age 40 -> 18-44 band; the age-200 row was quarantined


def test_generated_tests_pass(spec, tmp_path):
    import subprocess
    import sys

    files = generate(spec, tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(files["tests"])],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_local_review_flags_bare_except(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("try:\n    x = 1\nexcept:\n    pass\n")
    findings = local_review([bad])
    assert any("Bare except" in f.message for f in findings)


def test_resolve_findings_scope():
    findings = [
        Finding("high", "security", "a.py", 1, "h"),
        Finding("medium", "correctness", "a.py", 2, "m"),
        Finding("low", "best-practice", "a.py", 3, "l"),
    ]
    plan = resolve_findings(findings, scope="high")
    assert len(plan.selected) == 1 and len(plan.deferred) == 2
    plan = resolve_findings(findings, scope="all")
    assert len(plan.selected) == 3


def test_gate_blocks_failed_verification(tmp_path):
    log = EvidenceLog(tmp_path / "events.jsonl")
    report = VerificationReport("x", [Check("a", True), Check("b", False, "nope")])
    d = approve("r1", report, log)
    assert d.decision == "blocked"
    assert log.events()[0]["decision"] == "blocked"


def test_gate_approves_passing_verification(tmp_path):
    log = EvidenceLog(tmp_path / "events.jsonl")
    report = VerificationReport("x", [Check("a", True)])
    d = approve("r1", report, log)
    assert d.decision == "approved"


def test_escalate_records_findings(tmp_path):
    log = EvidenceLog(tmp_path / "events.jsonl")
    d = escalate("r1", [Finding("high", "security", "a.py", 1, "h")], log)
    assert d.decision == "escalated"
    assert len(log.events()[0]["findings"]) == 1


def test_backlog_spec_from_yaml_block():
    issue = Issue("PF-9", "T", body=textwrap.dedent("""\
        intro
        ```yaml
        name: from-issue
        ```
        outro"""))
    assert "from-issue" in issue_to_spec_text(issue)


def test_backlog_skeleton_when_no_block():
    issue = Issue("PF-9", "New pipeline please", body="no yaml here")
    text = issue_to_spec_text(issue)
    assert "new-pipeline-please" in text


def test_evidence_log_roundtrip(tmp_path):
    log = EvidenceLog(tmp_path / "events.jsonl")
    log.record("generate", {"spec": "patient-intake"})
    assert len(log.events()) == 1
    assert "patient-intake" in log.render_markdown()


def test_verify_works_with_relative_dirs(spec, tmp_path, monkeypatch):
    """Regression: verify() with relative generated/work dirs must pass.

    _run_pytest executes pytest with cwd set to the test file's parent
    directory, so a relative test path was unresolvable and the
    "generated tests" check failed even though the tests themselves pass.
    """
    from pipeline_factory.verify import verify

    monkeypatch.chdir(tmp_path)
    report = verify(spec, "gen", "work")
    assert report.passed, [(c.name, c.detail) for c in report.checks]
    assert (tmp_path / "gen" / "patient-intake").exists()
