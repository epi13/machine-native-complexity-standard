"""Typed protocol models and compact witness helpers."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass(frozen=True)
class ProviderIdentity:
    name: str
    version: str
    identity: str


@dataclass(frozen=True)
class Witness:
    kind: str
    summary: str
    locations: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisRequest:
    request_id: str
    analysis: str
    component: dict[str, Any]
    limits: dict[str, Any] = field(default_factory=dict)
    protocol_version: str = "0.1"
    type: str = "analysis_request"
    extensions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisResponse:
    request_id: str
    provider: ProviderIdentity
    status: Status
    summary: str
    witnesses: list[Witness] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    protocol_version: str = "0.1"
    type: str = "analysis_response"
    extensions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Capabilities:
    provider: ProviderIdentity
    analyses: list[str]
    statuses: list[Status] = field(default_factory=lambda: ["PASS", "FAIL", "UNKNOWN"])
    cancellation: bool = True
    health_checks: bool = True
    protocol_version: str = "0.1"
    type: str = "capabilities"
    extensions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderError:
    request_id: str
    provider: ProviderIdentity
    code: str
    message: str
    retryable: bool = False
    protocol_version: str = "0.1"
    type: str = "error"
    extensions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
