"""Load and validate the MNCS family registry."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path
from typing import Any

from ..schemas import schema_errors
from .constants import GITHUB_HOST, SCHEMA_VERSION
from .errors import RegistryError
from .models import Component, FamilyRegistry, Profile


def family_registry_candidates() -> list[Path]:
    env = os.environ.get("MNCS_FAMILY_REGISTRY")
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve()
    repo_family = here.parents[3] / "family" / "mncs-family.v0.1.json"
    candidates.append(repo_family)
    return candidates


def packaged_family_text() -> str:
    resource = files("mncs_validator.resources.family").joinpath("mncs-family.v0.1.json")
    return resource.read_text(encoding="utf-8")


def load_family_mapping(path: Path | None = None) -> dict[str, Any]:
    text: str
    if path is not None:
        text = path.read_text(encoding="utf-8")
    else:
        loaded: str | None = None
        for candidate in family_registry_candidates():
            if candidate.is_file():
                loaded = candidate.read_text(encoding="utf-8")
                break
        text = packaged_family_text() if loaded is None else loaded
    payload: Any = json.loads(text)
    if not isinstance(payload, dict):
        raise RegistryError("family registry is not an object")
    return payload


def _topo_sort(components: dict[str, Component]) -> list[str]:
    pending = {key: list(component.dependencies) for key, component in components.items()}
    resolved: list[str] = []
    remaining = set(pending)
    while remaining:
        ready = [item for item in remaining if all(dep not in remaining for dep in pending[item])]
        if not ready:
            cycle = ", ".join(sorted(remaining))
            raise RegistryError(f"dependency cycle among: {cycle}")
        ready.sort()
        chosen = ready[0]
        remaining.remove(chosen)
        resolved.append(chosen)
    return resolved


def validate_family_mapping(payload: dict[str, Any]) -> list[str]:
    errors = list(schema_errors(payload, "family-registry-0.1"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {payload.get('schema_version')}")
    components = payload.get("components")
    if not isinstance(components, list):
        return errors
    seen: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for item in components:
        if not isinstance(item, dict):
            errors.append("component is not an object")
            continue
        component_id = item.get("id")
        if not isinstance(component_id, str):
            errors.append("component missing id")
            continue
        if component_id in seen:
            errors.append(f"duplicate component id: {component_id}")
        seen.add(component_id)
        by_id[component_id] = item
        repository = item.get("repository")
        if isinstance(repository, dict):
            url = str(repository.get("url") or "")
            name = str(repository.get("name") or "")
            if not url.startswith(GITHUB_HOST):
                errors.append(f"{component_id}: repository url must be under {GITHUB_HOST}")
            if name and not url.rstrip("/").endswith(name):
                errors.append(f"{component_id}: repository url does not end with {name}")
    profiles = payload.get("profiles")
    if isinstance(profiles, dict):
        for profile_id, profile in profiles.items():
            if not isinstance(profile, dict):
                continue
            for field in ("components", "optional_components"):
                for component_id in profile.get(field) or []:
                    if component_id not in by_id:
                        errors.append(
                            f"profile {profile_id} references unknown component {component_id}"
                        )
    typed: dict[str, Component] = {}
    for component_id, item in by_id.items():
        typed[component_id] = Component.from_mapping(item)
        for dep in typed[component_id].dependencies:
            if dep not in by_id:
                errors.append(f"{component_id} depends on unknown component {dep}")
            if dep == component_id:
                errors.append(f"{component_id} depends on itself")
    if not errors:
        try:
            _topo_sort(typed)
        except RegistryError as exc:
            errors.append(str(exc))
    return errors


def load_family(path: Path | None = None) -> FamilyRegistry:
    payload = load_family_mapping(path)
    errors = validate_family_mapping(payload)
    if errors:
        raise RegistryError("family registry invalid: " + "; ".join(errors))
    profiles = {
        key: Profile.from_mapping(key, value)
        for key, value in payload["profiles"].items()
        if isinstance(value, dict)
    }
    components = {
        str(item["id"]): Component.from_mapping(item)
        for item in payload["components"]
        if isinstance(item, dict)
    }
    return FamilyRegistry(
        schema_version=str(payload["schema_version"]),
        registry_id=str(payload["registry_id"]),
        name=str(payload["name"]),
        description=str(payload["description"]),
        authority=dict(payload["authority"]),
        compatibility=dict(payload["compatibility"]),
        profiles=profiles,
        components=components,
        raw=payload,
    )


def resolve_selection(
    family: FamilyRegistry,
    profile_id: str | None,
    extras: Iterable[str] = (),
    include_optional: bool = True,
    supported: bool | None = None,
) -> list[str]:
    selected: list[str] = []
    optional: list[str] = []
    if profile_id:
        if profile_id not in family.profiles:
            raise RegistryError(f"unknown profile: {profile_id}")
        profile = family.profile(profile_id)
        selected.extend(profile.components)
        optional.extend(profile.optional_components)
    for item in extras:
        if item not in family.components:
            raise RegistryError(f"unknown component: {item}")
        selected.append(item)
    if include_optional:
        selected.extend(optional)
    ordered: list[str] = []
    seen: set[str] = set()

    def add(component_id: str) -> None:
        if component_id in seen:
            return
        component = family.component(component_id)
        if supported is False and component.optional:
            return
        for dep in component.dependencies:
            add(dep)
        seen.add(component_id)
        ordered.append(component_id)

    for component_id in selected:
        add(component_id)
    return ordered
