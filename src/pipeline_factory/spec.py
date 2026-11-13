"""Pipeline spec: load and validate the YAML spec that drives the factory.

A spec describes one governed data pipeline:
  name / version / owner / description
  source:      csv input + column schema (with pii flags)
  transforms:  deidentify / validate / derive steps, in order
  quality_gates: completeness / uniqueness thresholds
  destination: governed + quarantine outputs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

VALID_TYPES = {"string", "integer", "float", "boolean", "date"}
VALID_TRANSFORMS = {"deidentify", "validate", "derive"}
VALID_GATES = {"completeness", "uniqueness"}


@dataclass
class Column:
    name: str
    type: str = "string"
    pii: bool = False
    required: bool = False


@dataclass
class Source:
    type: str = "csv"
    path: str = ""
    schema: list[Column] = field(default_factory=list)


@dataclass
class Transform:
    kind: str
    fields: list[str] = field(default_factory=list)
    field: str = ""
    rule: str = ""
    min_value: float | None = None
    max_value: float | None = None
    expression: str = ""


@dataclass
class QualityGate:
    kind: str
    threshold: float = 1.0
    field: str = ""


@dataclass
class Destination:
    type: str = "csv"
    path: str = ""
    quarantine_path: str = ""


@dataclass
class PipelineSpec:
    name: str
    version: int = 1
    owner: str = ""
    description: str = ""
    source: Source = field(default_factory=Source)
    transforms: list[Transform] = field(default_factory=list)
    quality_gates: list[QualityGate] = field(default_factory=list)
    destination: Destination = field(default_factory=Destination)

    def pii_fields(self) -> list[str]:
        return [c.name for c in self.source.schema if c.pii]

    def column_names(self) -> list[str]:
        return [c.name for c in self.source.schema]

    def column_type(self, name: str) -> str:
        for c in self.source.schema:
            if c.name == name:
                return c.type
        return "string"


def load_spec(path: str | Path) -> PipelineSpec:
    """Load a spec from a YAML file. Raises ValueError with all problems."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: spec must be a YAML mapping")
    return parse_spec(raw, source=str(path))


def parse_spec(raw: dict[str, Any], source: str = "<dict>") -> PipelineSpec:
    """Parse and validate a spec dict. Raises ValueError listing every problem."""
    errors: list[str] = []

    name = raw.get("name", "")
    if not name or not isinstance(name, str):
        errors.append("name: required, non-empty string")

    version = raw.get("version", 1)
    if not isinstance(version, int) or version < 1:
        errors.append("version: must be a positive integer")

    src = raw.get("source") or {}
    if not isinstance(src, dict):
        errors.append("source: must be a mapping")
        src = {}
    schema: list[Column] = []
    for i, col in enumerate(src.get("schema") or []):
        if not isinstance(col, dict) or not col.get("name"):
            errors.append(f"source.schema[{i}]: each column needs a name")
            continue
        ctype = col.get("type", "string")
        if ctype not in VALID_TYPES:
            errors.append(f"source.schema[{i}] {col['name']}: unknown type {ctype!r}")
        schema.append(
            Column(
                name=col["name"],
                type=ctype,
                pii=bool(col.get("pii", False)),
                required=bool(col.get("required", False)),
            )
        )
    if not schema:
        errors.append("source.schema: at least one column is required")
    names = [c.name for c in schema]
    if len(names) != len(set(names)):
        errors.append("source.schema: duplicate column names")
    if not src.get("path"):
        errors.append("source.path: required")

    transforms: list[Transform] = []
    for i, t in enumerate(raw.get("transforms") or []):
        if not isinstance(t, dict):
            errors.append(f"transforms[{i}]: must be a mapping")
            continue
        kind = t.get("kind", "")
        if kind not in VALID_TRANSFORMS:
            errors.append(f"transforms[{i}]: unknown kind {kind!r}")
            continue
        fields = list(t.get("fields") or [])
        if kind == "deidentify" and not fields:
            errors.append(f"transforms[{i}] deidentify: fields required")
        if kind in ("validate", "derive") and not t.get("field"):
            errors.append(f"transforms[{i}] {kind}: field required")
        if kind == "validate":
            for f in fields + ([t["field"]] if t.get("field") else []):
                if f not in names:
                    errors.append(f"transforms[{i}]: unknown column {f!r}")
        if kind == "derive" and t.get("field") in names:
            errors.append(
                f"transforms[{i}] derive: {t['field']!r} already exists in the "
                "schema (derive creates a new column)"
            )
        if kind == "deidentify":
            for f in fields:
                if f not in [c.name for c in schema if c.pii]:
                    errors.append(
                        f"transforms[{i}] deidentify: {f!r} is not flagged pii "
                        "in the schema (deidentify only applies to pii fields)"
                    )
        transforms.append(
            Transform(
                kind=kind,
                fields=fields,
                field=t.get("field", ""),
                rule=t.get("rule", ""),
                min_value=t.get("min"),
                max_value=t.get("max"),
                expression=t.get("expression", ""),
            )
        )

    gates: list[QualityGate] = []
    for i, g in enumerate(raw.get("quality_gates") or []):
        if not isinstance(g, dict):
            errors.append(f"quality_gates[{i}]: must be a mapping")
            continue
        kind = g.get("kind", "")
        if kind not in VALID_GATES:
            errors.append(f"quality_gates[{i}]: unknown kind {kind!r}")
            continue
        threshold = g.get("threshold", 1.0)
        if not isinstance(threshold, (int, float)) or not 0 < threshold <= 1:
            errors.append(f"quality_gates[{i}]: threshold must be in (0, 1]")
        if kind == "uniqueness" and not g.get("field"):
            errors.append(f"quality_gates[{i}] uniqueness: field required")
        if g.get("field") and g["field"] not in names:
            errors.append(f"quality_gates[{i}]: unknown column {g['field']!r}")
        gates.append(
            QualityGate(kind=kind, threshold=float(threshold), field=g.get("field", ""))
        )

    dst = raw.get("destination") or {}
    if not isinstance(dst, dict):
        errors.append("destination: must be a mapping")
        dst = {}
    if not dst.get("path"):
        errors.append("destination.path: required")
    if not dst.get("quarantine_path"):
        errors.append("destination.quarantine_path: required")

    if errors:
        raise ValueError(f"{source}: invalid spec:\n" + "\n".join(f"  - {e}" for e in errors))

    return PipelineSpec(
        name=name,
        version=version,
        owner=raw.get("owner", ""),
        description=raw.get("description", ""),
        source=Source(
            type=src.get("type", "csv"), path=src.get("path", ""), schema=schema
        ),
        transforms=transforms,
        quality_gates=gates,
        destination=Destination(
            type=dst.get("type", "csv"),
            path=dst.get("path", ""),
            quarantine_path=dst.get("quarantine_path", ""),
        ),
    )
