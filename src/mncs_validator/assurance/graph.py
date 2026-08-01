"""Claim graph integrity, status propagation, and material-impact closure.

Graph traversal is pure and bounded by the record's schema-bounded in-memory graph.
It does not infer undeclared real-world dependencies. Missing structural evidence
therefore cannot be replaced by source review, grep, or line counts.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import Any

from .common import strings
from .freshness import freshness_status
from .model import AssuranceValidationReport
from .status import Status, aggregate_status


def claim_cycles(
    claim_ids: set[str],
    dependencies: list[dict[str, Any]],
    report: AssuranceValidationReport,
) -> None:
    """Add a stable issue when the declared claim graph is cyclic."""

    graph: dict[str, list[str]] = {claim_id: [] for claim_id in claim_ids}
    for dependency in dependencies:
        source = dependency.get("source_claim_id")
        target = dependency.get("target_claim_id")
        if isinstance(source, str) and isinstance(target, str) and source in graph:
            graph[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(claim_id: str) -> None:
        if claim_id in visited:
            return
        if claim_id in visiting:
            report.add(
                "MNCS-03-DEPENDENCY-CYCLE",
                f"claim dependency cycle includes {claim_id}",
            )
            return
        visiting.add(claim_id)
        for target in sorted(graph.get(claim_id, [])):
            if target in graph:
                visit(target)
        visiting.remove(claim_id)
        visited.add(claim_id)

    for claim_id in sorted(graph):
        visit(claim_id)


def derive_claim_statuses(
    claims: dict[str, dict[str, Any]],
    dependencies: list[dict[str, Any]],
    groups: dict[str, dict[str, Any]],
    at: datetime | None,
) -> dict[str, Status]:
    """Propagate required dependencies and correlation through an acyclic graph."""

    outgoing: dict[str, list[dict[str, Any]]] = {claim_id: [] for claim_id in claims}
    for dependency in dependencies:
        source = dependency.get("source_claim_id")
        if isinstance(source, str) and source in outgoing:
            outgoing[source].append(dependency)
    derived: dict[str, Status] = {}
    visiting: set[str] = set()

    def derive(claim_id: str) -> Status:
        if claim_id in derived:
            return derived[claim_id]
        if claim_id in visiting:
            return "UNKNOWN"
        visiting.add(claim_id)
        claim = claims[claim_id]
        statuses = [
            str(claim.get("base_status", "UNKNOWN")),
            freshness_status(claim.get("freshness"), at),
        ]
        if claim.get("retired") is True:
            statuses.append("FAIL")
        for dependency in outgoing[claim_id]:
            if dependency.get("required") is not True:
                continue
            target = dependency.get("target_claim_id")
            statuses.append(
                derive(target) if isinstance(target, str) and target in claims else "UNKNOWN"
            )
            statuses.append(str(dependency.get("interface_compatibility", "UNKNOWN")))
            statuses.append(str(dependency.get("environment_compatibility", "UNKNOWN")))
            for group_id in strings(dependency.get("correlated_failure_group_ids")):
                group = groups.get(group_id)
                statuses.append(str(group.get("status", "UNKNOWN")) if group else "UNKNOWN")
        visiting.remove(claim_id)
        derived[claim_id] = aggregate_status(statuses)
        return derived[claim_id]

    for claim_id in sorted(claims):
        derive(claim_id)
    return derived


def graph_impact_closure(
    direct_claim_ids: set[str],
    dependencies: list[dict[str, Any]],
) -> set[str]:
    """Return direct claims plus every required upstream dependent.

    For an edge ``source -> target``, source depends on target. A material change to
    target therefore invalidates source and its required upstream dependents.
    Optional edges remain visible elsewhere but do not expand the minimum required
    invalidation closure.
    """

    upstream: dict[str, set[str]] = {}
    for dependency in dependencies:
        if dependency.get("required") is not True:
            continue
        source = dependency.get("source_claim_id")
        target = dependency.get("target_claim_id")
        if isinstance(source, str) and isinstance(target, str):
            upstream.setdefault(target, set()).add(source)
    affected = set(direct_claim_ids)
    frontier = sorted(direct_claim_ids)
    while frontier:
        target = frontier.pop()
        for source in sorted(upstream.get(target, set())):
            if source not in affected:
                affected.add(source)
                frontier.append(source)
    return affected


def material_change_impact(
    changes: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    """Return direct and transitive affected claims for material changes."""

    direct = {
        claim_id
        for change in changes
        if change.get("material") is True
        for claim_id in strings(change.get("affected_claim_ids"))
    }
    return direct, graph_impact_closure(direct, dependencies)
