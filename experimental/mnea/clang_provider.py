#!/usr/bin/env python3
"""Experimental bounded C structural analyzer using Clang AST JSON.

This provider is intentionally narrow. Unsupported semantics remain UNKNOWN.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mncs_provider_sdk import (
    AnalysisResponse,
    Capabilities,
    ProviderIdentity,
    Witness,
    provider_main,
)

IDENTITY = ProviderIdentity(
    "mncs-clang-structural-experimental",
    "0.1.0",
    "experimental:mnea-clang-0.1",
)
CAPABILITIES = Capabilities(IDENTITY, ["c-structural-invariants"])
DEFAULT_MAX_SOURCE_BYTES = 1_000_000
DEFAULT_MAX_WALL_SECONDS = 10.0
MAX_WALL_SECONDS = 30.0


@dataclass
class Facts:
    """Bounded facts extracted from one translation unit."""

    functions: set[str] = field(default_factory=set)
    calls: dict[str, set[str]] = field(default_factory=dict)
    call_locations: dict[str, list[str]] = field(default_factory=dict)
    unresolved_calls: list[str] = field(default_factory=list)
    mutable_globals: list[str] = field(default_factory=list)
    external_globals: list[str] = field(default_factory=list)
    inline_assembly: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class InvariantResult:
    """One declarative invariant outcome."""

    invariant_id: str
    status: str
    summary: str
    witnesses: list[Witness] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


def _location(node: dict[str, Any]) -> str:
    loc = node.get("loc")
    if not isinstance(loc, dict):
        range_value = node.get("range")
        if isinstance(range_value, dict):
            loc = range_value.get("begin")
    if not isinstance(loc, dict):
        return "unknown"
    file_name = str(loc.get("file", ""))
    line = loc.get("line")
    column = loc.get("col")
    position = ":".join(str(value) for value in (line, column) if value is not None)
    return f"{file_name}:{position}" if file_name else position or "unknown"


def _referenced_function(node: Any) -> str | None:
    if isinstance(node, dict):
        referenced = node.get("referencedDecl")
        if isinstance(referenced, dict) and referenced.get("kind") == "FunctionDecl":
            name = referenced.get("name")
            return str(name) if name else None
        for child in node.get("inner", []):
            result = _referenced_function(child)
            if result:
                return result
    elif isinstance(node, list):
        for child in node:
            result = _referenced_function(child)
            if result:
                return result
    return None


def _belongs_to_source(node: dict[str, Any], source: Path | None) -> bool:
    """Best-effort filter for declarations from the requested translation unit."""

    if source is None:
        return True
    loc = node.get("loc")
    if not isinstance(loc, dict):
        return True
    if "includedFrom" in loc:
        return False
    file_value = loc.get("file")
    if not isinstance(file_value, str) or not file_value:
        return True
    try:
        return Path(file_value).resolve() == source.resolve()
    except OSError:
        return False


def collect_facts(ast: dict[str, Any], source: Path | None = None) -> Facts:
    """Collect only the facts supported by the experimental invariant set."""

    facts = Facts()

    def walk(node: Any, current_function: str | None = None) -> None:
        if not isinstance(node, dict):
            return
        kind = str(node.get("kind", ""))
        active_function = current_function
        if kind == "FunctionDecl" and node.get("name") and _belongs_to_source(node, source):
            active_function = str(node["name"])
            facts.functions.add(active_function)
            facts.calls.setdefault(active_function, set())
        elif kind == "CallExpr" and active_function:
            callee = _referenced_function(node)
            location = _location(node)
            if callee:
                facts.calls.setdefault(active_function, set()).add(callee)
                facts.call_locations.setdefault(callee, []).append(location)
            else:
                facts.unresolved_calls.append(location)
        elif (
            kind == "VarDecl"
            and current_function is None
            and _belongs_to_source(node, source)
        ):
            name = str(node.get("name", "<unnamed>"))
            storage = str(node.get("storageClass", ""))
            type_value = node.get("type")
            qualified = str(type_value.get("qualType", "")) if isinstance(type_value, dict) else ""
            if "const" not in qualified.split():
                target = facts.external_globals if storage == "extern" else facts.mutable_globals
                target.append(f"{name}@{_location(node)}")
        elif kind in {"GCCAsmStmt", "MSAsmStmt"}:
            facts.inline_assembly.append(_location(node))
        for child in node.get("inner", []):
            walk(child, active_function)

    walk(ast)
    return facts


def _cycles(calls: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(function: str) -> None:
        if function in visiting:
            start = visiting.index(function)
            cycle = visiting[start:] + [function]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if function in visited:
            return
        visiting.append(function)
        for callee in sorted(calls.get(function, set())):
            if callee in calls:
                visit(callee)
        visiting.pop()
        visited.add(function)

    for function in sorted(calls):
        visit(function)
    return cycles


def _max_call_depth(calls: dict[str, set[str]]) -> int | None:
    if _cycles(calls):
        return None
    memo: dict[str, int] = {}

    def depth(function: str) -> int:
        if function in memo:
            return memo[function]
        children = [callee for callee in calls.get(function, set()) if callee in calls]
        memo[function] = 1 + max((depth(child) for child in children), default=0)
        return memo[function]

    return max((depth(function) for function in calls), default=0)


def evaluate_invariant(invariant: dict[str, Any], facts: Facts) -> InvariantResult:
    """Evaluate one bounded invariant without treating unsupported facts as PASS."""

    invariant_id = str(invariant.get("id", "unnamed-invariant"))
    kind = str(invariant.get("kind", ""))
    if kind == "forbidden_calls":
        denied = {str(value) for value in invariant.get("calls", [])}
        hits = sorted(denied & {callee for targets in facts.calls.values() for callee in targets})
        if hits:
            witnesses = [
                Witness(
                    "forbidden-call",
                    f"forbidden direct call to {name}",
                    facts.call_locations.get(name, []),
                    {"callee": name},
                )
                for name in hits
            ]
            return InvariantResult(invariant_id, "FAIL", "forbidden direct call found", witnesses)
        if facts.unresolved_calls:
            return InvariantResult(
                invariant_id,
                "UNKNOWN",
                "unresolved calls may include a forbidden target",
                limitations=["Indirect or otherwise unresolved call targets were present."],
            )
        return InvariantResult(invariant_id, "PASS", "no forbidden direct calls found")
    if kind == "required_calls":
        required = {str(value) for value in invariant.get("calls", [])}
        observed = {callee for targets in facts.calls.values() for callee in targets}
        missing = sorted(required - observed)
        if not missing:
            return InvariantResult(invariant_id, "PASS", "all required direct calls found")
        if facts.unresolved_calls:
            return InvariantResult(
                invariant_id,
                "UNKNOWN",
                "unresolved calls prevent proving required-call absence",
                limitations=["Indirect or otherwise unresolved call targets were present."],
            )
        return InvariantResult(
            invariant_id,
            "FAIL",
            "required direct calls were absent",
            [Witness("missing-call", "required direct call absent", data={"calls": missing})],
        )
    if kind == "no_recursion":
        cycles = _cycles(facts.calls)
        if cycles:
            return InvariantResult(
                invariant_id,
                "FAIL",
                "direct recursion cycle found",
                [
                    Witness("recursion", "direct call cycle", data={"cycle": cycle})
                    for cycle in cycles
                ],
            )
        if facts.unresolved_calls:
            return InvariantResult(
                invariant_id,
                "UNKNOWN",
                "unresolved calls prevent excluding recursion",
                limitations=["Indirect or otherwise unresolved call targets were present."],
            )
        return InvariantResult(invariant_id, "PASS", "no direct recursion cycle found")
    if kind == "no_mutable_globals":
        if facts.mutable_globals:
            return InvariantResult(
                invariant_id,
                "FAIL",
                "mutable translation-unit globals found",
                [
                    Witness(
                        "mutable-global",
                        "mutable global declaration",
                        [location],
                    )
                    for location in facts.mutable_globals
                ],
            )
        if facts.external_globals:
            return InvariantResult(
                invariant_id,
                "UNKNOWN",
                "external mutable globals cannot be resolved in one translation unit",
                limitations=["External mutable global declarations were present."],
            )
        return InvariantResult(invariant_id, "PASS", "no mutable globals found")
    if kind == "no_inline_assembly":
        if facts.inline_assembly:
            return InvariantResult(
                invariant_id,
                "FAIL",
                "inline assembly found",
                [Witness("inline-assembly", "inline assembly statement", facts.inline_assembly)],
            )
        return InvariantResult(invariant_id, "PASS", "no inline assembly found")
    if kind == "max_call_depth":
        maximum = invariant.get("maximum")
        if not isinstance(maximum, int) or maximum < 0:
            return InvariantResult(
                invariant_id,
                "UNKNOWN",
                "maximum call depth was not a non-negative integer",
                limitations=["Invalid invariant configuration."],
            )
        depth = _max_call_depth(facts.calls)
        if depth is None:
            return InvariantResult(
                invariant_id,
                "FAIL",
                "recursive direct call graph has no finite call-depth bound",
                [Witness("call-depth", "direct recursion prevents a finite bound")],
            )
        if facts.unresolved_calls:
            return InvariantResult(
                invariant_id,
                "UNKNOWN",
                "unresolved calls prevent bounding call depth",
                limitations=["Indirect or otherwise unresolved call targets were present."],
            )
        if depth > maximum:
            return InvariantResult(
                invariant_id,
                "FAIL",
                f"observed direct call depth {depth} exceeds {maximum}",
                [
                    Witness(
                        "call-depth",
                        "direct call depth exceeded",
                        data={"observed": depth, "maximum": maximum},
                    )
                ],
            )
        return InvariantResult(
            invariant_id, "PASS", f"direct call depth {depth} is within {maximum}"
        )
    return InvariantResult(
        invariant_id,
        "UNKNOWN",
        f"unsupported invariant kind: {kind or '<missing>'}",
        limitations=["The requested invariant kind is not implemented."],
    )


def aggregate(results: list[InvariantResult]) -> str:
    """Apply MNCS status dominance without truthiness shortcuts."""

    statuses = [result.status for result in results]
    if "FAIL" in statuses:
        return "FAIL"
    if "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS" if statuses and all(status == "PASS" for status in statuses) else "UNKNOWN"


def _load_ast(source: Path, timeout: float) -> tuple[dict[str, Any] | None, str | None, float]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["clang", "-std=c11", "-Xclang", "-ast-dump=json", "-fsyntax-only", str(source)],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "Clang was not available.", time.monotonic() - started
    except subprocess.TimeoutExpired:
        return None, "Clang analysis exceeded the wall-time limit.", time.monotonic() - started
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        detail = completed.stderr.strip()[:1000]
        return None, f"Clang could not parse the source: {detail}", elapsed
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return None, f"Clang emitted invalid AST JSON: {exc}", elapsed
    if not isinstance(value, dict):
        return None, "Clang AST root was not an object.", elapsed
    return value, None, elapsed


def handle(request: dict[str, object]) -> dict[str, object]:
    """Handle one explicit Provider Protocol analysis request."""

    request_id = str(request.get("request_id", ""))
    if request.get("analysis") != "c-structural-invariants":
        return AnalysisResponse(
            request_id,
            IDENTITY,
            "UNKNOWN",
            "unsupported analysis request",
            limitations=["Only c-structural-invariants is implemented."],
        ).as_dict()
    component = request.get("component")
    if not isinstance(component, dict):
        return AnalysisResponse(
            request_id,
            IDENTITY,
            "UNKNOWN",
            "component was not an object",
            limitations=["A component object is required."],
        ).as_dict()
    source_value = component.get("source_path")
    if not isinstance(source_value, str) or not source_value:
        return AnalysisResponse(
            request_id,
            IDENTITY,
            "UNKNOWN",
            "source_path was missing",
            limitations=["A single C source path is required."],
        ).as_dict()
    source = Path(source_value)
    limits = request.get("limits")
    limits = limits if isinstance(limits, dict) else {}
    max_bytes_value = limits.get("max_source_bytes", DEFAULT_MAX_SOURCE_BYTES)
    max_bytes = (
        max_bytes_value
        if isinstance(max_bytes_value, int) and max_bytes_value > 0
        else DEFAULT_MAX_SOURCE_BYTES
    )
    timeout_value = limits.get("max_wall_seconds", DEFAULT_MAX_WALL_SECONDS)
    timeout = (
        float(timeout_value)
        if isinstance(timeout_value, (int, float)) and timeout_value > 0
        else DEFAULT_MAX_WALL_SECONDS
    )
    timeout = min(timeout, MAX_WALL_SECONDS)
    if not source.is_file():
        return AnalysisResponse(
            request_id,
            IDENTITY,
            "UNKNOWN",
            "source file was unavailable",
            limitations=[f"Not a readable file: {source}"],
        ).as_dict()
    size = source.stat().st_size
    if size > max_bytes:
        return AnalysisResponse(
            request_id,
            IDENTITY,
            "UNKNOWN",
            "source exceeded the declared byte bound",
            limitations=[f"Input bytes {size} exceeded {max_bytes}."],
        ).as_dict()
    ast, error, elapsed = _load_ast(source, timeout)
    if error or ast is None:
        return AnalysisResponse(
            request_id,
            IDENTITY,
            "UNKNOWN",
            "bounded compiler extraction was inconclusive",
            limitations=[error or "Unknown extraction failure."],
            extensions={
                "mncs.dev:analyzer_result": {
                    "mode": str(component.get("mode", "evaluator")),
                    "contract_id": str(component.get("contract_id", "unknown-contract")),
                    "evidence_partition": str(component.get("evidence_partition", "development")),
                    "wall_seconds": elapsed,
                    "input_bytes": size,
                }
            },
        ).as_dict()
    facts = collect_facts(ast, source)
    invariants_value = component.get("invariants")
    invariants = invariants_value if isinstance(invariants_value, list) else []
    results = [
        evaluate_invariant(invariant, facts)
        for invariant in invariants
        if isinstance(invariant, dict)
    ]
    status = aggregate(results)
    witnesses = [witness for result in results for witness in result.witnesses]
    limitations = [limitation for result in results for limitation in result.limitations]
    if not results:
        limitations.append("No supported invariants were supplied.")
    return AnalysisResponse(
        request_id,
        IDENTITY,
        status,
        f"evaluated {len(results)} bounded C structural invariants",
        witnesses,
        limitations,
        extensions={
            "mncs.dev:analyzer_result": {
                "schema_version": "0.1-experimental",
                "mode": str(component.get("mode", "evaluator")),
                "contract_id": str(component.get("contract_id", "unknown-contract")),
                "evidence_partition": str(component.get("evidence_partition", "development")),
                "required_semantics_complete": status == "PASS" and not facts.unresolved_calls,
                "unsupported_constructs": [
                    f"unresolved-call@{location}" for location in facts.unresolved_calls
                ]
                + [f"external-global@{location}" for location in facts.external_globals],
                "resource_usage": {
                    "wall_seconds": elapsed,
                    "peak_memory_bytes": None,
                    "input_bytes": size,
                },
                "invariants": [
                    {
                        "invariant_id": result.invariant_id,
                        "status": result.status,
                        "summary": result.summary,
                        "limitations": result.limitations,
                    }
                    for result in results
                ],
            }
        },
    ).as_dict()


if __name__ == "__main__":
    raise SystemExit(provider_main(IDENTITY, CAPABILITIES, handle))
