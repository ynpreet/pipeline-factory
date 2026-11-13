"""Review: static review of generated code + Qodo findings handling.

Two sources of findings:
  * local review — a small static checker that mirrors the categories a
    Qodo review reports (security, correctness, best practice).
  * Qodo findings — import a JSON export of a real Qodo review
    (list of {severity, category, file, line, message, suggestion}).

Resolution follows the Week-2 "PR Resolver" pattern: read findings,
choose scope (high / medium / custom severity), produce a fix plan.
Applying fixes is a separate, human-approved step.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SEVERITIES = {"high", "medium", "low"}


@dataclass
class Finding:
    severity: str  # high | medium | low
    category: str  # security | correctness | best-practice
    file: str
    line: int
    message: str
    suggestion: str = ""
    source: str = "local"

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "suggestion": self.suggestion,
            "source": self.source,
        }


def local_review(files: list[Path]) -> list[Finding]:
    """Run the local static review over generated files."""
    findings: list[Finding] = []
    for path in files:
        if path.suffix != ".py":
            continue
        lines = path.read_text().splitlines()
        current_def = ""
        for i, line in enumerate(lines, start=1):
            if line.startswith("def "):
                current_def = line.split("(")[0][4:]
            stripped = line.strip()
            if re.search(r"\bexcept\s*:", stripped):
                findings.append(
                    Finding(
                        "medium", "correctness", str(path), i,
                        "Bare except: swallows every error, including KeyboardInterrupt.",
                        "Catch the specific exception you expect.",
                    )
                )
            if "eval(" in line and current_def != "_derive":
                findings.append(
                    Finding(
                        "high", "security", str(path), i,
                        "eval() outside the restricted _derive helper.",
                        "Route dynamic expressions through _derive only.",
                    )
                )
            if re.search(r"(password|api_key|secret)\s*=\s*[\"'][^\"']{4,}", line, re.I):
                findings.append(
                    Finding(
                        "high", "security", str(path), i,
                        "Possible hardcoded credential.",
                        "Move it to a secret store / environment variable.",
                    )
                )
            if "open(" in line and "newline" not in line and "encoding" not in line:
                findings.append(
                    Finding(
                        "low", "best-practice", str(path), i,
                        "open() without explicit newline/encoding for CSV work.",
                        "Pass newline='' (csv) and encoding='utf-8'.",
                    )
                )
        for i, line in enumerate(lines, start=1):
            if line.startswith("def ") and '"""' not in line and '"""' not in (
                lines[i] if i < len(lines) else ""
            ):
                findings.append(
                    Finding(
                        "low", "best-practice", str(path), i,
                        f"Function {line.split('(')[0][4:]} has no docstring.",
                        "Add a one-line docstring.",
                    )
                )
    return findings


def import_qodo_findings(json_path: str | Path) -> list[Finding]:
    """Import findings exported from a Qodo review (JSON list)."""
    data = json.loads(Path(json_path).read_text())
    findings: list[Finding] = []
    for item in data:
        severity = str(item.get("severity", "low")).lower()
        findings.append(
            Finding(
                severity=severity if severity in SEVERITIES else "low",
                category=item.get("category", "best-practice"),
                file=item.get("file", ""),
                line=int(item.get("line", 0)),
                message=item.get("message", ""),
                suggestion=item.get("suggestion", ""),
                source="qodo",
            )
        )
    return findings


@dataclass
class ResolutionPlan:
    scope: str
    selected: list[Finding] = field(default_factory=list)
    deferred: list[Finding] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Resolution plan (scope: {self.scope})"]
        for f in self.selected:
            lines.append(
                f"  [{f.severity}] {f.file}:{f.line} {f.message} -> {f.suggestion or 'fix'}"
            )
        if self.deferred:
            lines.append(f"  Deferred ({len(self.deferred)}): lower severity, next round.")
        return "\n".join(lines)


def resolve_findings(findings: list[Finding], scope: str = "high") -> ResolutionPlan:
    """PR Resolver pattern: read findings, choose scope, plan fixes.

    scope: 'high' | 'medium' (high+medium) | 'all'.
    """
    wanted = {"high"} if scope == "high" else (
        {"high", "medium"} if scope == "medium" else {"high", "medium", "low"}
    )
    selected = [f for f in findings if f.severity in wanted]
    deferred = [f for f in findings if f.severity not in wanted]
    return ResolutionPlan(scope=scope, selected=selected, deferred=deferred)
