"""Typed bootstrap records."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _str_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


@dataclass(frozen=True)
class RepositoryRef:
    owner: str
    name: str
    url: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RepositoryRef:
        return cls(owner=str(value["owner"]), name=str(value["name"]), url=str(value["url"]))


@dataclass(frozen=True)
class Profile:
    id: str
    display_name: str
    description: str
    components: tuple[str, ...]
    optional_components: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, profile_id: str, value: Mapping[str, Any]) -> Profile:
        return cls(
            id=profile_id,
            display_name=str(value["display_name"]),
            description=str(value["description"]),
            components=tuple(_str_list(value.get("components"))),
            optional_components=tuple(_str_list(value.get("optional_components"))),
        )


@dataclass(frozen=True)
class HealthCheck:
    id: str
    kind: str
    binary: str | None = None
    argv: tuple[str, ...] = ()
    path: str | None = None
    unit: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HealthCheck:
        return cls(
            id=str(value["id"]),
            kind=str(value["kind"]),
            binary=str(value["binary"]) if value.get("binary") else None,
            argv=tuple(_str_list(value.get("argv"))),
            path=str(value["path"]) if value.get("path") else None,
            unit=str(value["unit"]) if value.get("unit") else None,
        )


@dataclass(frozen=True)
class McpServer:
    id: str
    transport: str
    command: str
    config_hint: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> McpServer:
        hint = value.get("config_hint")
        return cls(
            id=str(value["id"]),
            transport=str(value["transport"]),
            command=str(value["command"]),
            config_hint=str(hint) if isinstance(hint, str) else None,
        )


@dataclass(frozen=True)
class ServiceDef:
    id: str
    kind: str
    privilege: str
    unit: str | None = None
    installer: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ServiceDef:
        return cls(
            id=str(value["id"]),
            kind=str(value["kind"]),
            privilege=str(value["privilege"]),
            unit=str(value["unit"]) if value.get("unit") else None,
            installer=str(value["installer"]) if value.get("installer") else None,
        )


@dataclass(frozen=True)
class ConfigLocation:
    kind: str
    path: str
    platform: str = "any"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ConfigLocation:
        return cls(
            kind=str(value["kind"]),
            path=str(value["path"]),
            platform=str(value.get("platform") or "any"),
        )


@dataclass(frozen=True)
class Relationship:
    id: str
    kind: str
    note: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Relationship:
        note = value.get("note")
        return cls(
            id=str(value["id"]),
            kind=str(value["kind"]),
            note=str(note) if isinstance(note, str) else None,
        )


@dataclass(frozen=True)
class Binary:
    name: str
    entry: str | None = None
    conflict_note: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Binary:
        return cls(
            name=str(value["name"]),
            entry=str(value["entry"]) if value.get("entry") else None,
            conflict_note=str(value["conflict_note"]) if value.get("conflict_note") else None,
        )


@dataclass(frozen=True)
class PackageSpec:
    ecosystem: str
    name: str
    extras: str | None = None
    published: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> PackageSpec | None:
        if not value:
            return None
        extras = value.get("extras")
        return cls(
            ecosystem=str(value["ecosystem"]),
            name=str(value["name"]),
            extras=str(extras) if isinstance(extras, str) else None,
            published=bool(value.get("published")),
        )


@dataclass(frozen=True)
class Component:
    id: str
    display_name: str
    repository: RepositoryRef
    purpose: str
    category: str
    authority_class: str
    normative: bool
    role: str
    optional: bool
    audiences: tuple[str, ...]
    foundational: bool
    platforms: tuple[str, ...]
    architectures: tuple[str, ...]
    unsupported_platforms: tuple[str, ...]
    dependencies: tuple[str, ...]
    conflicts: tuple[str, ...]
    runtime_requirements: tuple[str, ...]
    build_requirements: tuple[str, ...]
    install_strategy: str
    automation: str
    binaries: tuple[Binary, ...]
    health_checks: tuple[HealthCheck, ...]
    update_strategy: str
    documentation: dict[str, str]
    mcp: tuple[McpServer, ...] = ()
    services: tuple[ServiceDef, ...] = ()
    config_locations: tuple[ConfigLocation, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    source_default_ref: str = "main"
    package: PackageSpec | None = None
    install_notes: str | None = None
    maturity: str = "experimental"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Component:
        source_value = value.get("source")
        source: dict[str, Any] = source_value if isinstance(source_value, dict) else {}
        docs_value = value.get("documentation")
        docs: dict[str, Any] = docs_value if isinstance(docs_value, dict) else {}
        package_value = value.get("package")
        package = package_value if isinstance(package_value, dict) else None
        return cls(
            id=str(value["id"]),
            display_name=str(value["display_name"]),
            repository=RepositoryRef.from_mapping(value["repository"]),
            purpose=str(value["purpose"]),
            category=str(value["category"]),
            authority_class=str(value["authority_class"]),
            normative=bool(value["normative"]),
            role=str(value["role"]),
            optional=bool(value["optional"]),
            audiences=tuple(_str_list(value.get("audiences"))),
            foundational=bool(value["foundational"]),
            platforms=tuple(_str_list(value.get("platforms"))),
            architectures=tuple(_str_list(value.get("architectures"))),
            unsupported_platforms=tuple(_str_list(value.get("unsupported_platforms"))),
            dependencies=tuple(_str_list(value.get("dependencies"))),
            conflicts=tuple(_str_list(value.get("conflicts"))),
            runtime_requirements=tuple(_str_list(value.get("runtime_requirements"))),
            build_requirements=tuple(_str_list(value.get("build_requirements"))),
            install_strategy=str(value["install_strategy"]),
            automation=str(value["automation"]),
            binaries=tuple(
                Binary.from_mapping(item)
                for item in value.get("binaries", [])
                if isinstance(item, dict)
            ),
            health_checks=tuple(
                HealthCheck.from_mapping(item)
                for item in value.get("health_checks", [])
                if isinstance(item, dict)
            ),
            update_strategy=str(value["update_strategy"]),
            documentation=_str_map(docs),
            mcp=tuple(
                McpServer.from_mapping(item)
                for item in value.get("mcp", [])
                if isinstance(item, dict)
            ),
            services=tuple(
                ServiceDef.from_mapping(item)
                for item in value.get("services", [])
                if isinstance(item, dict)
            ),
            config_locations=tuple(
                ConfigLocation.from_mapping(item)
                for item in value.get("config_locations", [])
                if isinstance(item, dict)
            ),
            relationships=tuple(
                Relationship.from_mapping(item)
                for item in value.get("relationships", [])
                if isinstance(item, dict)
            ),
            source_default_ref=str(source.get("default_ref") or "main"),
            package=PackageSpec.from_mapping(package),
            install_notes=str(value["install_notes"]) if value.get("install_notes") else None,
            maturity=str(value.get("maturity") or "experimental"),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "repository": {
                "owner": self.repository.owner,
                "name": self.repository.name,
                "url": self.repository.url,
            },
            "purpose": self.purpose,
            "category": self.category,
            "authority_class": self.authority_class,
            "normative": self.normative,
            "role": self.role,
            "optional": self.optional,
            "audiences": list(self.audiences),
            "foundational": self.foundational,
            "platforms": list(self.platforms),
            "architectures": list(self.architectures),
            "install_strategy": self.install_strategy,
            "automation": self.automation,
            "maturity": self.maturity,
            "documentation": dict(self.documentation),
        }


@dataclass(frozen=True)
class FamilyRegistry:
    schema_version: str
    registry_id: str
    name: str
    description: str
    authority: dict[str, Any]
    compatibility: dict[str, Any]
    profiles: dict[str, Profile]
    components: dict[str, Component]
    raw: dict[str, Any] = field(repr=False, compare=False)

    def component(self, component_id: str) -> Component:
        return self.components[component_id]

    def profile(self, profile_id: str) -> Profile:
        return self.profiles[profile_id]


@dataclass(frozen=True)
class ToolFact:
    name: str
    available: bool
    path: str | None = None
    version: str | None = None
    status: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "path": self.path,
            "version": self.version,
            "status": self.status,
        }


@dataclass(frozen=True)
class ComponentState:
    id: str
    state: str
    path: str | None = None
    version: str | None = None
    ref: str | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state,
            "path": self.path,
            "version": self.version,
            "ref": self.ref,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class McpState:
    id: str
    state: str
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "state": self.state, "detail": self.detail}


@dataclass
class HostObservation:
    os: str
    architecture: str
    support: str
    captured_at: str
    os_name: str = ""
    os_version: str = ""
    distro: str = ""
    support_note: str = ""
    hostname_present: bool = False
    tools: dict[str, ToolFact] = field(default_factory=dict)
    cpu_count: int | None = None
    ram_bytes: int | None = None
    disk_total_bytes: int | None = None
    disk_free_bytes: int | None = None
    gpus: list[dict[str, Any]] = field(default_factory=list)
    services: dict[str, str] = field(default_factory=dict)
    workspace: str | None = None
    components: dict[str, ComponentState] = field(default_factory=dict)
    mcp: dict[str, McpState] = field(default_factory=dict)
    binaries: dict[str, str | None] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "mncs-host-observation.v0.1",
            "captured_at": self.captured_at,
            "os": self.os,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "distro": self.distro,
            "architecture": self.architecture,
            "support": self.support,
            "support_note": self.support_note,
            "hostname_present": self.hostname_present,
            "tools": {name: fact.as_dict() for name, fact in self.tools.items()},
            "resources": {
                "cpu_count": self.cpu_count,
                "ram_bytes": self.ram_bytes,
                "disk_total_bytes": self.disk_total_bytes,
                "disk_free_bytes": self.disk_free_bytes,
                "gpu": self.gpus,
            },
            "services": dict(self.services),
            "mncs": {
                "workspace": self.workspace,
                "components": {key: value.as_dict() for key, value in self.components.items()},
                "mcp": {key: value.as_dict() for key, value in self.mcp.items()},
                "binaries": dict(self.binaries),
            },
            "warnings": list(self.warnings),
        }

    def with_components(self, components: dict[str, ComponentState]) -> HostObservation:
        return replace(self, components=components)


@dataclass(frozen=True)
class PlanAction:
    id: str
    component: str
    kind: str
    status: str
    summary: str
    detail: str = ""
    privilege: str = "none"
    network: bool = False
    destructive: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "component": self.component,
            "kind": self.kind,
            "status": self.status,
            "summary": self.summary,
            "detail": self.detail,
            "privilege": self.privilege,
            "network": self.network,
            "destructive": self.destructive,
        }


@dataclass(frozen=True)
class BlockedItem:
    component: str
    reason: str
    code: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {"component": self.component, "reason": self.reason, "code": self.code}


@dataclass(frozen=True)
class BootstrapPlan:
    profile: str | None
    components: tuple[str, ...]
    actions: tuple[PlanAction, ...]
    blocked: tuple[BlockedItem, ...]
    warnings: tuple[str, ...]
    outcome: str
    workspace: str | None = None
    ref: str | None = None
    network: bool = True
    allow_services: bool = False

    def summary(self) -> dict[str, int]:
        healthy = skip = install = configure = blocked = 0
        for action in self.actions:
            if action.kind == "skip" and action.status == "skipped":
                if "healthy" in action.summary.lower() or "already" in action.summary.lower():
                    healthy += 1
                else:
                    skip += 1
            elif action.kind in {"clone", "create_venv", "pip_install", "cargo_build"}:
                install += 1
            elif action.kind in {"configure", "enable_service", "operator"}:
                configure += 1
            elif action.status == "blocked":
                blocked += 1
        blocked += len(self.blocked)
        return {
            "healthy": healthy,
            "install": install,
            "configure": configure,
            "skip": skip,
            "blocked": blocked,
        }

    def as_dict(self) -> dict[str, Any]:
        from .constants import BOOTSTRAP_DISCLAIMER, PLAN_SCHEMA_VERSION

        return {
            "schema_version": PLAN_SCHEMA_VERSION,
            "disclaimer": BOOTSTRAP_DISCLAIMER,
            "profile": self.profile,
            "workspace": self.workspace,
            "ref": self.ref,
            "network": self.network,
            "allow_services": self.allow_services,
            "components": list(self.components),
            "actions": [action.as_dict() for action in self.actions],
            "blocked": [item.as_dict() for item in self.blocked],
            "warnings": list(self.warnings),
            "summary": self.summary(),
            "outcome": self.outcome,
        }

    def mutating(self) -> bool:
        return any(action.status == "planned" for action in self.actions)
