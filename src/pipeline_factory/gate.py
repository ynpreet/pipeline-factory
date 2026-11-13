"""Approval gate: verify -> approve or escalate.

A generated pipeline reaches production only through this gate:
  * approve   — allowed only when the verification report passed.
  * escalate  — sends review findings back to the agent with a reason;
                nothing is approved until the findings are resolved and
                verification passes again.

Every decision is written to the evidence log, so the full trail is
auditable (the hackathon rules ask for evidence of reviews and
automation, not just claims).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .evidence import EvidenceLog
from .review import Finding
from .verify import VerificationReport


@dataclass
class GateDecision:
    decision: str  # approved | escalated | blocked
    run_id: str
    reason: str


def approve(
    run_id: str,
    report: VerificationReport,
    log: EvidenceLog,
    approver: str = "preet-mehta",
) -> GateDecision:
    """Approve a verified run. Blocked if verification did not pass."""
    if not report.passed:
        failed = [c.name for c in report.checks if not c.passed]
        decision = GateDecision(
            decision="blocked",
            run_id=run_id,
            reason=f"verification failed: {', '.join(failed)}",
        )
    else:
        decision = GateDecision(
            decision="approved",
            run_id=run_id,
            reason=f"all {len(report.checks)} verification checks passed",
        )
    log.record(
        "gate_decision",
        {
            "run_id": run_id,
            "decision": decision.decision,
            "reason": decision.reason,
            "approver": approver,
        },
    )
    return decision


def escalate(
    run_id: str,
    findings: list[Finding],
    log: EvidenceLog,
    reason: str = "",
) -> GateDecision:
    """Escalate: send findings back to the agent; nothing is approved."""
    decision = GateDecision(
        decision="escalated",
        run_id=run_id,
        reason=reason or f"{len(findings)} unresolved finding(s)",
    )
    log.record(
        "gate_decision",
        {
            "run_id": run_id,
            "decision": decision.decision,
            "reason": decision.reason,
            "findings": [f.to_dict() for f in findings],
        },
    )
    return decision
