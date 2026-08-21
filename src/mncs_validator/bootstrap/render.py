"""Human-readable bootstrap output. JSON remains the machine API."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from .constants import BOOTSTRAP_DISCLAIMER
from .models import BootstrapPlan, FamilyRegistry, HostObservation


def render_family(family: FamilyRegistry) -> str:
    lines = [
        family.name,
        family.description,
        "",
        "Authority: this map is discovery/bootstrap only.",
        BOOTSTRAP_DISCLAIMER,
        "",
        "Components:",
    ]
    for component in family.components.values():
        flag = "normative" if component.normative else "non-normative"
        lines.append(
            f"  {component.id:24} {component.display_name} [{flag}] {component.authority_class}"
        )
    lines.append("")
    lines.append("Profiles:")
    for profile in family.profiles.values():
        lines.append(f"  {profile.id:12} {profile.display_name}: {', '.join(profile.components)}")
    return "\n".join(lines)


def render_host(host: HostObservation) -> str:
    lines = [
        f"Host: {host.os_name or host.os} {host.architecture}",
        f"Support: {host.support}",
    ]
    if host.support_note:
        lines.append(host.support_note)
    lines.append("")
    lines.append("Tools:")
    for name, fact in host.tools.items():
        mark = "available" if fact.available else "missing"
        extra = f" ({fact.version})" if fact.version else ""
        lines.append(f"  {name:12} {mark}{extra}")
    if host.components:
        lines.append("")
        lines.append("MNCS components:")
        for component_state in host.components.values():
            lines.append(f"  {component_state.id:24} {component_state.state}")
    if host.mcp:
        lines.append("")
        lines.append("MCP:")
        for mcp_state in host.mcp.values():
            lines.append(f"  {mcp_state.id:24} {mcp_state.state}")
    if host.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in host.warnings:
            lines.append(f"  - {warning}")
    return "\n".join(lines)


def render_plan(plan: BootstrapPlan) -> str:
    summary = plan.summary()
    lines = [
        BOOTSTRAP_DISCLAIMER,
        "",
        f"Profile: {plan.profile or '(components)'}",
        f"Workspace: {plan.workspace}",
        f"Outcome: {plan.outcome}",
        "",
        "Plan:",
        f"  {summary['healthy']} already present",
        f"  {summary['install']} install actions",
        f"  {summary['configure']} configuration/operator actions",
        f"  {summary['blocked']} blocked",
        "",
        "Actions:",
    ]
    for action in plan.actions:
        lines.append(f"  [{action.status}] {action.kind:16} {action.component}: {action.summary}")
    if plan.blocked:
        lines.append("")
        lines.append("Blocked:")
        for item in plan.blocked:
            lines.append(f"  {item.component}: {item.reason}")
    return "\n".join(lines)


def render_receipt(payload: dict[str, Any]) -> str:
    lines = [
        str(payload.get("disclaimer") or BOOTSTRAP_DISCLAIMER),
        "",
        f"Outcome: {payload.get('outcome')}",
        f"Profile: {(payload.get('requested') or {}).get('profile')}",
        "",
        "Actions:",
    ]
    for action in payload.get("actions") or []:
        if not isinstance(action, dict):
            continue
        lines.append(
            "  [{result}] {kind} {component}: {detail}".format(
                result=action.get("result"),
                kind=action.get("kind"),
                component=action.get("component"),
                detail=action.get("detail"),
            )
        )
    failures = payload.get("failures") or []
    if failures:
        lines.append("")
        lines.append("Failures:")
        for item in failures:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def render_describe(payload: dict[str, Any]) -> str:
    mncs = payload.get("mncs") or {}
    lines = [
        str(mncs.get("name") or "MNCS"),
        str(mncs.get("purpose") or ""),
        "",
        BOOTSTRAP_DISCLAIMER,
        "",
        "Operations: " + ", ".join(payload.get("operations") or []),
        "Documentation: " + ", ".join((payload.get("documentation") or {}).values()),
    ]
    return "\n".join(lines)
