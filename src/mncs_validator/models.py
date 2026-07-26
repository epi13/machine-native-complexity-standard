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
class ValidationReport:
    """Deterministic validation result."""

    target: str
    valid: bool = True
    declared_status: Status | None = None
    computed_status: Status | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    checked_files: int = 0

    def add(self, code: str, message: str, path: str = "") -> None:
        """Add a finding and mark the report invalid."""

        self.valid = False
        self.issues.append(ValidationIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True)
class ComparisonResult:
    """Pareto comparison between two candidate manifests."""

    relation: Literal[
        "A_DOMINATES_B", "B_DOMINATES_A", "EQUIVALENT", "INCOMPARABLE", "DIFFERENT_CONTRACT"
    ]
    explanation: str
    dimensions: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)
