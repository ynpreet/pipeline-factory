"""Recurring intake: pick up "Ready to Build" tickets, draft specs.

Day 4 challenge — automate the intake. A recurring job polls the
backlog for tickets labelled "Ready to Build" and runs backlog -> spec
for each one it has not seen before.

One invocation is one poll cycle; schedule it with cron or any
scheduler, e.g. every 30 minutes:

    */30 * * * * factory intake

Idempotent: processed issue ids are stored in a JSON state file, so a
re-run never re-drafts a spec it already wrote, and an existing spec
file is never overwritten. Every pick and every run is written to the
evidence log, so the intake itself is auditable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .backlog import Issue, issue_to_spec_text
from .evidence import EvidenceLog
from .spec import parse_spec

READY_LABEL = "Ready to Build"

_NAME_RE = re.compile(r"^name:\s*([A-Za-z0-9_.-]+)\s*$", re.MULTILINE)


def is_ready(issue: Issue) -> bool:
    """True when the issue carries the Ready to Build label (case-insensitive)."""
    return any(label.lower() == READY_LABEL.lower() for label in issue.labels)


def poll(issues: list[Issue], seen: set[str]) -> list[Issue]:
    """Ready-to-Build issues this run has not processed yet."""
    return [i for i in issues if is_ready(i) and str(i.id) not in seen]


def spec_name(text: str, issue: Issue) -> str:
    """The spec name from a drafted spec text, falling back to the title slug."""
    match = _NAME_RE.search(text)
    if match:
        return match.group(1)
    return re.sub(r"[^a-z0-9]+", "-", issue.title.lower()).strip("-") or "pipeline"


def _load_state(state_path: str | Path) -> dict:
    path = Path(state_path)
    if not path.exists():
        return {"processed": []}
    try:
        return json.loads(path.read_text()) or {"processed": []}
    except (json.JSONDecodeError, OSError):
        return {"processed": []}


def _save_state(state_path: str | Path, processed: set[str]) -> None:
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"processed": sorted(processed)}, indent=2) + "\n")


@dataclass
class IntakeRun:
    picked: list[str] = field(default_factory=list)
    skipped_seen: list[str] = field(default_factory=list)
    skipped_not_ready: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    spec_files: dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"intake: picked {len(self.picked)}, "
            f"already seen {len(self.skipped_seen)}, "
            f"not ready {len(self.skipped_not_ready)}, "
            f"spec already exists {len(self.skipped_existing)}"
        )


def run_intake(
    issues: list[Issue],
    specs_dir: str | Path,
    log: EvidenceLog,
    state_path: str | Path,
) -> IntakeRun:
    """One intake cycle: draft specs for unseen Ready-to-Build issues."""
    specs_dir = Path(specs_dir)
    specs_dir.mkdir(parents=True, exist_ok=True)
    state = _load_state(state_path)
    seen: set[str] = set(state.get("processed", []))
    run = IntakeRun()

    for issue in issues:
        issue_id = str(issue.id)
        if not is_ready(issue):
            run.skipped_not_ready.append(issue_id)
            continue
        if issue_id in seen:
            run.skipped_seen.append(issue_id)
            continue
        text = issue_to_spec_text(issue)
        name = spec_name(text, issue)
        spec_file = specs_dir / f"{name}.yaml"
        if spec_file.exists():
            run.skipped_existing.append(issue_id)
            seen.add(issue_id)
            log.record("intake", {
                "issue": issue_id,
                "spec_file": str(spec_file),
                "outcome": "spec-already-exists",
            })
            continue
        try:
            parse_spec(yaml.safe_load(text))
            valid = True
        except ValueError:
            valid = False
        spec_file.write_text(text)
        run.picked.append(issue_id)
        run.spec_files[issue_id] = str(spec_file)
        seen.add(issue_id)
        log.record("intake", {
            "issue": issue_id,
            "spec_file": str(spec_file),
            "valid": valid,
            "outcome": "spec-drafted",
        })

    _save_state(state_path, seen)
    log.record("intake-run", {
        "picked": run.picked,
        "skipped_seen": run.skipped_seen,
        "skipped_not_ready": run.skipped_not_ready,
        "skipped_existing": run.skipped_existing,
    })
    return run
