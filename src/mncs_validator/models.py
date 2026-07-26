"""Small typed result models used by the validator and CLI."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass(frozen=True)
class ValidationIssue:
    """One actionable validation finding."""

    code: str
    message: str
    path: str = ""


@dataclass
class GateDecision:
    """One validator-derived gate decision and its evidence lineage."""

    status: Status
    evidence_ids: list[str] = field(default_factory=list)
    excluded_evidence_ids: list[str] = field(default_factory=list)
    conflicting_evidence_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Deterministic validation result."""

    target: str
    valid: bool = True
    declared_status: Status | None = None
    computed_status: Status | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    checked_files: int = 0
    schema_version: str | None = None
    claimed_level_status: Status | None = None
    certification_eligible: bool = False
    legacy_self_asserted_acceptance: bool = False
    legacy_override_used: bool = False
    reduced_assurance: bool = False
    gate_statuses: dict[str, GateDecision] = field(default_factory=dict)
    evidence_graph: dict[str, list[str]] = field(default_factory=dict)
    comparison_context: dict[str, str] = field(default_factory=dict)

    def add(self, code: str, message: str, path: str = "") -> None:
        """Add a finding and mark the report invalid."""

        self.valid = False
        self.issues.append(ValidationIssue(code, message, path))

    def warn(self, code: str, message: str, path: str = "") -> None:
        """Add a non-fatal finding."""

        self.warnings.append(ValidationIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True)
class ComparisonResult:
    """Pareto comparison between two candidate manifests."""

    relation: Literal[
        "A_DOMINATES_B",
        "B_DOMINATES_A",
        "EQUIVALENT",
        "INCOMPARABLE",
        "DIFFERENT_CONTRACT",
        "INCOMPATIBLE_OBJECTIVE",
        "INCOMPATIBLE_UNITS",
        "INCOMPATIBLE_ENVIRONMENT",
        "INVALID_EVIDENCE",
        "UNCERTIFIED_INPUT",
    ]
    explanation: str
    dimensions: dict[str, str]
    evidence_strength: dict[str, str] = field(default_factory=dict)
    warning: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)
