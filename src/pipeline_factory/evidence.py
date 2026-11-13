"""Evidence log: every factory event, timestamped, append-only.

The hackathon rules require evidence — code changes, reviews, tests,
standards, automation — not just claims. The evidence log is the
factory's audit trail: each generate / verify / review / gate decision
is recorded as one JSON line, and `render_markdown` turns the log into
a human-readable report for the submission.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class EvidenceLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, payload: dict) -> dict:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **payload,
        }
        with open(self.path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
        return entry

    def events(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text().splitlines()
            if line.strip()
        ]

    def render_markdown(self) -> str:
        events = self.events()
        lines = ["# Factory evidence log", "", f"{len(events)} events recorded.", ""]
        for e in events:
            lines.append(f"- `{e.get('ts', '')}` **{e.get('event', '')}**")
            for key, value in e.items():
                if key in ("ts", "event"):
                    continue
                lines.append(f"  - {key}: {value}")
        return "\n".join(lines) + "\n"
