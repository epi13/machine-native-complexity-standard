"""Desired-state planner for MNCS family bootstrap."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from .constants import BOOTSTRAP_DISCLAIMER
from .errors import PlanError
from .models import (
    BlockedItem,
    BootstrapPlan,
    Component,
    ComponentState,
    FamilyRegistry,
    HostObservation,
    PlanAction,
)
from .registry import resolve_selection


def _platform_ok(component: Component, host: HostObservation) -> bool:
    if host.os == "macos":
        return "macos" in component.platforms
    if host.os == "windows":
        return "windows" in component.platforms
    if host.os == "linux":
        if host.distro == "raspberry-pi":
            return "linux-arm" in component.platforms or "linux" in component.platforms
        return "linux" in component.platforms
    return False


def _arch_ok(component: Component, host: HostObservation) -> bool:
    arch = host.architecture
    aliases = {arch}
    if arch == "x86_64":
        aliases.add("amd64")
    if arch == "aarch64":
        aliases.add("arm64")
    return bool(aliases.intersection(component.architectures))


def _missing_tools(component: Component, host: HostObservation) -> list[str]:
    missing: list[str] = []
    required = list(component.runtime_requirements) + list(component.build_requirements)
    for item in required:
        name = item.split(">=")[0].split("==")[0]
        if name == "python":
            tool = host.tools.get("python3") or host.tools.get("python")
            if tool is None or not tool.available:
                missing.append(item)
            continue
        if name == "bwrap":
            tool = host.tools.get("bwrap")
            if tool is None or not tool.available:
                missing.append(item)
            continue
        tool = host.tools.get(name)
        if tool is None or not tool.available:
            missing.append(item)
    return missing


def _healthy(state: ComponentState | None) -> bool:
    return state is not None and state.state in {"installed", "configured", "healthy"}


def _present(state: ComponentState | None) -> bool:
    return state is not None and state.state not in {"not_installed", "unknown"}


def plan_bootstrap(
    family: FamilyRegistry,
    host: HostObservation,
    *,
    profile: str | None,
    extras: list[str] | None = None,
    include_optional: bool = True,
    network: bool = True,
    allow_services: bool = False,
    ref: str | None = None,
    workspace: Path | None = None,
) -> BootstrapPlan:
    if host.support in {"unsupported", "deferred"} and profile not in {None, "core"}:
        # Core planning is still useful on deferred hosts: report honestly.
        pass
    selected = resolve_selection(
        family,
        profile,
        extras or (),
        include_optional=include_optional,
    )
    actions: list[PlanAction] = []
    blocked: list[BlockedItem] = []
    warnings = list(host.warnings)
    index = 0

    def next_id(prefix: str) -> str:
        nonlocal index
        index += 1
        return f"{prefix}-{index:03d}"

    if host.support == "deferred":
        warnings.append(host.support_note or "Host platform is deferred.")
    if host.support == "unsupported":
        blocked.append(
            BlockedItem(
                component="host",
                reason=host.support_note or "unsupported host",
                code="unsupported-platform",
            )
        )

    for component_id in selected:
        component = family.component(component_id)
        state = host.components.get(component_id)
        if not _platform_ok(component, host) or not _arch_ok(component, host):
            blocked.append(
                BlockedItem(
                    component_id,
                    reason=(
                        f"{component.display_name} is not supported on "
                        f"{host.os}/{host.architecture}"
                    ),
                    code="unsupported-platform",
                )
            )
            continue
        missing = _missing_tools(component, host)
        if missing and not _healthy(state):
            blocked.append(
                BlockedItem(
                    component_id,
                    reason=f"unresolved requirements: {', '.join(missing)}",
                    code="missing-tool",
                )
            )
            continue
        if _healthy(state) or (_present(state) and component.install_strategy == "git-checkout"):
            actions.append(
                PlanAction(
                    id=next_id("skip"),
                    component=component_id,
                    kind="skip",
                    status="skipped",
                    summary=f"{component.display_name} already present",
                    detail=state.detail if state else "",
                )
            )
            if component.automation == "assisted" and component.services and not allow_services:
                actions.append(
                    PlanAction(
                        id=next_id("op"),
                        component=component_id,
                        kind="operator",
                        status="required_operator",
                        summary=(
                            f"{component.display_name} service/configuration "
                            "remains operator-mediated"
                        ),
                        detail=component.install_notes or "",
                    )
                )
            continue

        if component.install_strategy in {
            "python-source-venv",
            "cargo-source",
            "git-checkout",
            "user-service-script",
        }:
            if not network:
                blocked.append(
                    BlockedItem(
                        component_id,
                        reason="clone/install requires network and --no-network was set",
                        code="network-required",
                    )
                )
                continue
            if not _present(state):
                actions.append(
                    PlanAction(
                        id=next_id("clone"),
                        component=component_id,
                        kind="clone",
                        status="planned",
                        summary=f"Clone {component.repository.name}",
                        detail=component.repository.url,
                        network=True,
                    )
                )
            if component.install_strategy == "python-source-venv":
                actions.append(
                    PlanAction(
                        id=next_id("venv"),
                        component=component_id,
                        kind="create_venv",
                        status="planned",
                        summary=f"Create a user-level virtualenv for {component.display_name}",
                    )
                )
                actions.append(
                    PlanAction(
                        id=next_id("pip"),
                        component=component_id,
                        kind="pip_install",
                        status="planned",
                        summary=(
                            "Install "
                            f"{component.package.name if component.package else component.id} "
                            "from source"
                        ),
                    )
                )
            elif component.install_strategy == "cargo-source":
                actions.append(
                    PlanAction(
                        id=next_id("cargo"),
                        component=component_id,
                        kind="cargo_build",
                        status="planned",
                        summary=(
                            f"Build {component.display_name} with cargo "
                            "(no PATH install for colliding binaries)"
                        ),
                    )
                )
            elif component.install_strategy == "git-checkout":
                actions.append(
                    PlanAction(
                        id=next_id("skip"),
                        component=component_id,
                        kind="skip",
                        status="planned",
                        summary=f"Keep {component.display_name} as a source checkout",
                    )
                )
        if (
            component.install_strategy == "user-service-script"
            or component.automation == "assisted"
        ):
            if allow_services and component.services:
                for service in component.services:
                    if service.privilege == "administrator":
                        blocked.append(
                            BlockedItem(
                                component_id,
                                reason=(
                                    f"{service.id} requires administrator privilege; "
                                    "bootstrap will not auto-elevate"
                                ),
                                code="privilege-required",
                            )
                        )
                        continue
                    if service.kind == "systemd-user" and host.os != "linux":
                        actions.append(
                            PlanAction(
                                id=next_id("op"),
                                component=component_id,
                                kind="operator",
                                status="required_operator",
                                summary=f"{service.id} is Linux user-systemd only",
                                privilege="user",
                            )
                        )
                        continue
                    actions.append(
                        PlanAction(
                            id=next_id("svc"),
                            component=component_id,
                            kind="enable_service",
                            status="planned" if allow_services else "required_operator",
                            summary=f"Enable user service {service.unit or service.id}",
                            detail=service.installer or "",
                            privilege="user",
                        )
                    )
            else:
                actions.append(
                    PlanAction(
                        id=next_id("op"),
                        component=component_id,
                        kind="operator",
                        status="required_operator",
                        summary=f"{component.display_name} needs operator configuration",
                        detail=component.install_notes or BOOTSTRAP_DISCLAIMER,
                    )
                )
        if component.install_strategy == "manual":
            actions.append(
                PlanAction(
                    id=next_id("op"),
                    component=component_id,
                    kind="operator",
                    status="required_operator",
                    summary=f"{component.display_name} cannot be safely automated yet",
                    detail=component.install_notes or "",
                )
            )
        actions.append(
            PlanAction(
                id=next_id("health"),
                component=component_id,
                kind="health_check",
                status="planned",
                summary=f"Re-check {component.display_name} after installation",
            )
        )

    if host.support == "deferred":
        outcome = "unsupported"
    elif blocked and not actions:
        outcome = "blocked"
    elif any(action.status == "planned" for action in actions):
        outcome = "changes_required"
    else:
        outcome = "unchanged"
    if not selected:
        raise PlanError("no components selected")
    return BootstrapPlan(
        profile=profile,
        components=tuple(selected),
        actions=tuple(actions),
        blocked=tuple(blocked),
        warnings=tuple(warnings),
        outcome=outcome,
        workspace=str(workspace) if workspace else host.workspace,
        ref=ref,
        network=network,
        allow_services=allow_services,
    )
