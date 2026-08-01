#!/usr/bin/env python3
"""Validate the static release-gap issue mapping without network access."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs/release-gap-matrix.json"
MAP_PATH = ROOT / "docs/release-gap-issue-map.json"


def validate_mapping() -> list[str]:
    """Return deterministic mapping errors; an empty list is success."""

    errors: list[str] = []
    matrix_bytes = MATRIX_PATH.read_bytes()
    matrix = cast(dict[str, Any], json.loads(matrix_bytes))
    mapping = cast(dict[str, Any], json.loads(MAP_PATH.read_text(encoding="utf-8")))
    digest = hashlib.sha256(matrix_bytes).hexdigest()
    if mapping.get("matrix_version") != matrix.get("matrix_version"):
        errors.append("matrix version does not match")
    if mapping.get("matrix_sha256") != digest:
        errors.append("matrix SHA-256 does not match")

    requirements = {
        str(item["requirement_id"]): item
        for item in cast(list[dict[str, Any]], matrix.get("requirements", []))
    }
    unresolved = {
        requirement_id
        for requirement_id, item in requirements.items()
        if item.get("gap_class") is not None or bool(item.get("blocking_issues"))
    }
    seen_requirements: dict[str, str] = {}
    seen_keys: set[str] = set()
    for index, item in enumerate(cast(list[dict[str, Any]], mapping.get("mappings", []))):
        gap_key = item.get("gap_key")
        requirement_ids = item.get("requirement_ids")
        if not isinstance(gap_key, str) or not gap_key:
            errors.append(f"mapping {index} has no stable gap key")
            continue
        if gap_key in seen_keys:
            errors.append(f"duplicate gap key: {gap_key}")
        seen_keys.add(gap_key)
        if not isinstance(requirement_ids, list) or not requirement_ids:
            errors.append(f"mapping {gap_key} references no matrix requirement")
            continue
        if not isinstance(item.get("issue_number"), int) or item["issue_number"] < 1:
            errors.append(f"mapping {gap_key} has no valid issue number")
        if not isinstance(item.get("issue_url"), str) or not item["issue_url"].endswith(
            f"/issues/{item.get('issue_number')}"
        ):
            errors.append(f"mapping {gap_key} has an inconsistent issue URL")
        for requirement_id in requirement_ids:
            if requirement_id not in requirements:
                errors.append(f"mapping {gap_key} references unknown requirement {requirement_id}")
            if requirement_id in seen_requirements:
                errors.append(
                    f"requirement {requirement_id} maps to both "
                    f"{seen_requirements[requirement_id]} and {gap_key}"
                )
            seen_requirements[str(requirement_id)] = gap_key

    mapped = set(seen_requirements)
    for requirement_id in sorted(unresolved - mapped):
        errors.append(f"unresolved requirement is unmapped: {requirement_id}")
    for requirement_id in sorted(mapped - unresolved):
        errors.append(f"resolved requirement is unexpectedly mapped: {requirement_id}")
    return errors


def main() -> int:
    """Validate and print a concise machine-readable result."""

    errors = validate_mapping()
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "mapping": str(MAP_PATH.relative_to(ROOT)),
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
