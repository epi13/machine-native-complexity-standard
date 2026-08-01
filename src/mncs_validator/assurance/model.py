"""Typed report model for release-candidate validation.

Reports describe one offline implementation decision. They are not certification,
independent evaluation, protected custody, or operational disposition.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .status import Status, aggregate_status

RecordKind = Literal["contract", "assurance", "threat", "measurement"]


@dataclass(frozen=True)
class AssuranceIssue:
    """One normalized release-candidate finding."""

    code: str
    message: str
    path: str = ""


@dataclass
class AssuranceValidationReport:
    """Schema, semantic, and conformance outcome for one RC record."""

    target: str
    kind: str
    valid: bool = True
    supported: bool = True
    computed_status: Status = "PASS"
    record_id: str | None = None
    issues: list[AssuranceIssue] = field(default_factory=list)
    warnings: list[AssuranceIssue] = field(default_factory=list)
    rule_results: dict[str, Status] = field(default_factory=dict)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.computed_status

    def add(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.issues.append(AssuranceIssue(code, message, path))

    def warn(self, code: str, message: str, path: str = "") -> None:
        self.warnings.append(AssuranceIssue(code, message, path))

    def rule(self, code: str, status: Status, message: str = "", path: str = "") -> None:
        self.rule_results[code] = status
        self.computed_status = aggregate_status([self.computed_status, status])
        if status != "PASS" and message:
            self.warn(code, message, path)

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result
