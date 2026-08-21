"""Observe installed MNCS family state without mutating the host."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path

from .host import Probe, SystemProbe
from .models import Component, ComponentState, FamilyRegistry, HostObservation, McpState
from .paths import expand_user_path, layout_for


def _git_remote(probe: Probe, checkout: Path) -> str | None:
    result = probe.run(["git", "-C", str(checkout), "remote", "get-url", "origin"], timeout=5.0)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _git_ref(probe: Probe, checkout: Path) -> str | None:
    result = probe.run(
        ["git", "-C", str(checkout), "rev-parse", "--abbrev-ref", "HEAD"], timeout=5.0
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _checkout_candidates(workspace: Path, component: Component) -> list[Path]:
    names = {component.id, component.repository.name}
    return [workspace / name for name in names]


def _discover_checkout(probe: Probe, workspace: Path, component: Component) -> Path | None:
    for candidate in _checkout_candidates(workspace, component):
        if probe.exists(candidate / ".git"):
            remote = _git_remote(probe, candidate)
            if remote is None or component.repository.name in remote:
                return candidate
        elif probe.exists(candidate / "pyproject.toml") or probe.exists(candidate / "Cargo.toml"):
            return candidate
    return None


def _binary_path(probe: Probe, name: str) -> str | None:
    return probe.which(name)


def _unit_state(probe: Probe, unit: str) -> str:
    result = probe.run(["systemctl", "--user", "is-active", unit], timeout=5.0)
    status = (result.stdout or result.stderr).strip()
    if result.returncode == 0 and status == "active":
        return "healthy"
    if status:
        return status
    return "unknown"


def _config_present(probe: Probe, component: Component) -> bool:
    for location in component.config_locations:
        path = expand_user_path(location.path)
        if probe.exists(path):
            return True
    return False


def observe_component(
    probe: Probe,
    component: Component,
    workspace: Path,
) -> ComponentState:
    checkout = _discover_checkout(probe, workspace, component)
    binary = None
    for item in component.binaries:
        if item.conflict_note and "PATH" in item.conflict_note:
            continue
        binary = _binary_path(probe, item.name)
        if binary:
            break
    config = _config_present(probe, component)
    if checkout is None and binary is None and not config:
        return ComponentState(
            id=component.id, state="not_installed", detail="no checkout, binary, or config observed"
        )
    version = None
    ref = _git_ref(probe, checkout) if checkout else None
    if binary:
        result = probe.run([binary, "--version"], timeout=5.0)
        if result.returncode == 0 and result.stdout.strip():
            version = result.stdout.splitlines()[0].strip()
        elif result.returncode == 0:
            json_result = probe.run([binary, "version", "--json"], timeout=5.0)
            if json_result.returncode == 0:
                try:
                    payload = json.loads(json_result.stdout)
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict):
                    version = str(payload.get("package_version") or payload.get("version") or "")
    state = "checkout_present" if checkout and not binary else "installed"
    if binary or config:
        state = "configured" if config else "installed"
    detail = "observed"
    if checkout:
        detail = f"checkout {checkout}"
    if binary:
        detail = f"{detail}; binary {binary}"
    return ComponentState(
        id=component.id,
        state=state,
        path=str(checkout) if checkout else (str(Path(binary).parent) if binary else None),
        version=version or None,
        ref=ref,
        detail=detail,
    )


def observe_mcp(probe: Probe, component: Component, state: ComponentState) -> list[McpState]:
    results: list[McpState] = []
    for server in component.mcp:
        binary = probe.which(server.command)
        if binary is None and state.state == "not_installed":
            results.append(
                McpState(id=server.id, state="not_installed", detail="command not on PATH")
            )
            continue
        configured = _config_present(probe, component)
        if binary is None:
            results.append(
                McpState(
                    id=server.id,
                    state="installed" if state.path else "not_installed",
                    detail="package checkout present but MCP command is not on PATH",
                )
            )
            continue
        if not configured:
            results.append(McpState(id=server.id, state="installed", detail=f"command {binary}"))
            continue
        unit_health = None
        for service in component.services:
            if service.kind == "systemd-user" and service.unit and "@" not in service.unit:
                unit_health = _unit_state(probe, service.unit)
        if unit_health == "healthy":
            results.append(
                McpState(id=server.id, state="healthy", detail=f"unit active; command {binary}")
            )
        elif unit_health:
            results.append(
                McpState(
                    id=server.id,
                    state="configured" if unit_health in {"inactive", "dead"} else "degraded",
                    detail=f"unit {unit_health}; command {binary}",
                )
            )
        else:
            results.append(
                McpState(
                    id=server.id, state="configured", detail=f"config present; command {binary}"
                )
            )
    return results


def observe_services(probe: Probe, family: FamilyRegistry) -> dict[str, str]:
    observed: dict[str, str] = {}
    if probe.which("systemctl"):
        for component in family.components.values():
            for service in component.services:
                if service.kind == "systemd-user" and service.unit and "@" not in service.unit:
                    observed[service.unit] = _unit_state(probe, service.unit)
    return observed


def observe_family(
    family: FamilyRegistry,
    host: HostObservation,
    probe: Probe | None = None,
    workspace: Path | None = None,
) -> HostObservation:
    active = probe or SystemProbe()
    layout = layout_for(
        Path(workspace) if workspace else (Path(host.workspace) if host.workspace else None)
    )
    components: dict[str, ComponentState] = {}
    mcp: dict[str, McpState] = {}
    binaries: dict[str, str | None] = dict(host.binaries)
    for component in family.components.values():
        state = observe_component(active, component, layout.workspace)
        components[component.id] = state
        for item in component.binaries:
            binaries[item.name] = active.which(item.name)
        for mcp_state in observe_mcp(active, component, state):
            mcp[mcp_state.id] = mcp_state
    host.components = components
    host.mcp = mcp
    host.binaries = binaries
    host.services = observe_services(active, family)
    host.workspace = str(layout.workspace)
    return host
