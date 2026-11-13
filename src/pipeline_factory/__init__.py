"""Pipeline Factory — an AI-assisted software factory.

Backlog ticket -> pipeline spec -> generated, tested pipeline code
-> review -> verification -> human approve / escalate gate.

Built for the Qodo Hackathon (Nov 2 – Dec 2, 2026).
Design patterns (de-identification, quality gates, audit trail) follow
Preet Mehta's HIPAA-oriented pipeline framework
(github.com/ynpreet/hipaa-pipeline-framework, Apache-2.0) — disclosed
here per the hackathon rules; all code in this repo was written during
the event.
"""

__version__ = "0.1.0"
