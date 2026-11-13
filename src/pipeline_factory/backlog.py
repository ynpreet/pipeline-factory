"""Backlog: turn backlog tickets into pipeline specs.

The factory's front door (Week-3 "Connect" theme): a ticket comes in,
the factory reads it, drafts a spec, and the build starts from there.

Two sources:
  * a local backlog.yaml (always available; used for the demo), and
  * `gh issue list` for a GitHub repo (optional; needs the gh CLI and
    auth — the factory works fine without it).

An issue body may carry a fenced ```yaml spec block; when it does, that
block is the spec. Otherwise the factory drafts a skeleton spec from
the issue title and labels, and a human fills in the schema.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

SPEC_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL)


@dataclass
class Issue:
    id: str
    title: str
    body: str = ""
    labels: list[str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []


def load_backlog(path: str | Path) -> list[Issue]:
    """Load issues from a local backlog.yaml file."""
    data = yaml.safe_load(Path(path).read_text()) or {}
    issues = []
    for item in data.get("issues", []):
        issues.append(
            Issue(
                id=str(item.get("id", "")),
                title=item.get("title", ""),
                body=item.get("body", ""),
                labels=list(item.get("labels", [])),
            )
        )
    return issues


def gh_issues(repo: str, limit: int = 20) -> list[Issue]:
    """List open issues from a GitHub repo via the gh CLI."""
    proc = subprocess.run(
        ["gh", "issue", "list", "--repo", repo, "--limit", str(limit),
         "--json", "number,title,body,labels"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue list failed: {proc.stderr.strip()}")
    issues = []
    for item in __import__("json").loads(proc.stdout or "[]"):
        issues.append(
            Issue(
                id=str(item.get("number", "")),
                title=item.get("title", ""),
                body=item.get("body", ""),
                labels=[l.get("name", "") for l in item.get("labels", [])],
            )
        )
    return issues


def issue_to_spec_text(issue: Issue) -> str:
    """Draft a spec YAML from an issue.

    If the issue body carries a fenced yaml spec block, use it verbatim.
    Otherwise return a skeleton spec the author fills in.
    """
    match = SPEC_BLOCK_RE.search(issue.body or "")
    if match:
        return match.group(1).strip() + "\n"
    slug = re.sub(r"[^a-z0-9]+", "-", issue.title.lower()).strip("-") or "pipeline"
    return f"""# Draft spec from backlog issue {issue.id}: {issue.title}
# Fill in the schema, transforms and gates, then run: factory validate
name: {slug}
version: 1
owner: preet-mehta
description: "{issue.title}"
source:
  type: csv
  path: data/input.csv
  schema:
    - name: record_id
      type: string
      pii: false
      required: true
    - name: value
      type: string
      pii: false
transforms: []
quality_gates:
  - kind: completeness
    threshold: 0.95
destination:
  type: csv
  path: out/governed.csv
  quarantine_path: out/quarantined.csv
"""
