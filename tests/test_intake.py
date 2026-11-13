"""Intake tests: Ready-to-Build polling, spec drafting, idempotency."""

import textwrap
from pathlib import Path

from pipeline_factory.backlog import Issue
from pipeline_factory.evidence import EvidenceLog
from pipeline_factory.intake import is_ready, poll, run_intake, spec_name


def _issue(issue_id, labels, body=""):
    return Issue(issue_id, f"Ticket {issue_id}", body=body, labels=labels)


def test_is_ready_matches_label_case_insensitively():
    assert is_ready(_issue("A", ["Ready to Build"]))
    assert is_ready(_issue("B", ["ready to build"]))
    assert not is_ready(_issue("C", ["pipeline"]))
    assert not is_ready(_issue("D", []))


def test_poll_picks_only_unseen_ready_issues():
    issues = [
        _issue("A", ["Ready to Build"]),
        _issue("B", ["pipeline"]),
        _issue("C", ["Ready to Build"]),
    ]
    picked = poll(issues, seen={"C"})
    assert [i.id for i in picked] == ["A"]


def test_spec_name_from_draft_text():
    issue = _issue("PF-9", ["Ready to Build"], body="```yaml\nname: from-issue\n```")
    from pipeline_factory.backlog import issue_to_spec_text

    assert spec_name(issue_to_spec_text(issue), issue) == "from-issue"


def test_run_writes_spec_for_ready_issue(tmp_path):
    issue = _issue("PF-9", ["Ready to Build"], body=textwrap.dedent("""\
        intro
        ```yaml
        name: lab-intake
        version: 1
        owner: preet-mehta
        description: Lab intake.
        source:
          type: csv
          path: data/labs.csv
          schema:
            - {name: patient_id, type: string, pii: true, required: true}
        transforms:
          - {kind: deidentify, fields: [patient_id]}
        quality_gates:
          - {kind: completeness, threshold: 0.95}
        destination:
          type: csv
          path: out/governed.csv
          quarantine_path: out/quarantined.csv
        ```
        """))
    log = EvidenceLog(tmp_path / "events.jsonl")
    run = run_intake([issue], tmp_path / "specs", log, tmp_path / "state.json")
    assert run.picked == ["PF-9"]
    spec_file = tmp_path / "specs" / "lab-intake.yaml"
    assert spec_file.exists()
    assert "lab-intake" in spec_file.read_text()
    events = log.events()
    assert any(e["event"] == "intake" and e["valid"] is True for e in events)
    assert any(e["event"] == "intake-run" for e in events)


def test_run_is_idempotent(tmp_path):
    issue = _issue("PF-9", ["Ready to Build"], body="no yaml here")
    log = EvidenceLog(tmp_path / "events.jsonl")
    first = run_intake([issue], tmp_path / "specs", log, tmp_path / "state.json")
    assert first.picked == ["PF-9"]
    spec_file = tmp_path / "specs" / "ticket-pf-9.yaml"
    assert spec_file.exists()
    content = spec_file.read_text()
    second = run_intake([issue], tmp_path / "specs", log, tmp_path / "state.json")
    assert second.picked == []
    assert second.skipped_seen == ["PF-9"]
    assert spec_file.read_text() == content  # never rewritten


def test_run_skips_not_ready_issues(tmp_path):
    issues = [_issue("A", ["pipeline"]), _issue("B", ["ops"])]
    log = EvidenceLog(tmp_path / "events.jsonl")
    run = run_intake(issues, tmp_path / "specs", log, tmp_path / "state.json")
    assert run.picked == []
    assert run.skipped_not_ready == ["A", "B"]
    assert list((tmp_path / "specs").glob("*.yaml")) == []


def test_run_drafts_valid_skeleton_without_yaml_block(tmp_path):
    issue = _issue("PF-9", ["Ready to Build"], body="please build a new pipeline")
    log = EvidenceLog(tmp_path / "events.jsonl")
    run = run_intake([issue], tmp_path / "specs", log, tmp_path / "state.json")
    assert run.picked == ["PF-9"]
    spec_file = tmp_path / "specs" / "ticket-pf-9.yaml"
    assert spec_file.exists()
    assert "Ticket PF-9" in spec_file.read_text()
    intake_event = [e for e in log.events() if e["event"] == "intake"][0]
    assert intake_event["valid"] is True


def test_run_does_not_overwrite_existing_spec(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    existing = specs / "lab-intake.yaml"
    existing.write_text("# hand-written, keep me\n")
    issue = _issue("PF-9", ["Ready to Build"], body="```yaml\nname: lab-intake\n```")
    log = EvidenceLog(tmp_path / "events.jsonl")
    run = run_intake([issue], specs, log, tmp_path / "state.json")
    assert run.picked == []
    assert run.skipped_existing == ["PF-9"]
    assert existing.read_text() == "# hand-written, keep me\n"
