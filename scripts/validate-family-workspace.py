#!/usr/bin/env python3
"""Validate all repository-local family manifests and resolve local contracts."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

_SPEC = importlib.util.spec_from_file_location(
    "mncs_standard_manifest_validator", Path(__file__).with_name("validate-family-manifest.py")
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("unable to load the Standard manifest validator")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
validate = _MODULE.validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    manifests = sorted(args.workspace.glob("*/.mncs/project.json"))
    reports: list[dict[str, Any]] = []
    by_repository: dict[str, dict[str, Any]] = {}
    for path in manifests:
        repository_root = path.parent.parent
        value = json.loads(path.read_text(encoding="utf-8"))
        report = validate(path, repository_root, value.get("repository"))
        report["path"] = str(path)
        reports.append(report)
        if isinstance(value.get("repository"), str):
            by_repository[value["repository"]] = value
    resolved: list[dict[str, str]] = []
    external: list[dict[str, str]] = []
    errors: list[str] = []
    for report, path in zip(reports, manifests):
        value = json.loads(path.read_text(encoding="utf-8"))
        consumes = value.get("contracts", {}).get("consumes", [])
        for consumed in consumes if isinstance(consumes, list) else []:
            contract = consumed.get("contract") if isinstance(consumed, dict) else None
            if not isinstance(contract, str) or "." not in contract:
                errors.append(f"{path}: malformed consumed contract identity {contract!r}")
                continue
            provider, contract_name = contract.split(".", 1)
            provider_manifest = by_repository.get(provider)
            if provider_manifest is None:
                external.append({"consumer": str(value.get("repository")), "contract": contract})
                continue
            provides = provider_manifest.get("contracts", {}).get("provides", [])
            matches = [item for item in provides if isinstance(item, dict) and item.get("contract") == contract_name]
            if not matches:
                errors.append(f"{path}: local provider {provider} does not provide {contract}")
                continue
            resolved.append({"consumer": str(value.get("repository")), "contract": contract})
    valid = all(item.get("valid") for item in reports) and not errors
    output = {
        "schema_version": "mncs.standard.family-workspace-validation/1",
        "valid": valid,
        "manifest_count": len(reports),
        "manifests": reports,
        "contracts": {"resolved": resolved, "external_or_pinned": external, "errors": errors},
        "participation": {
            "local_manifest": len(reports),
            "central_or_pinned_snapshot": "not represented by a local manifest; consult the Standard family catalog",
        },
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
