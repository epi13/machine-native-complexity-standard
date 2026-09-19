#!/usr/bin/env python3
"""Validate one repository-local MNCS family manifest.

This is the Standard-owned bounded validator consumed by sibling services.
It reports schema conformance and local binding checks without making those
consumers reimplement the Standard schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/mncs-family-repository-manifest-v0alpha1.schema.json"
REPORT_SCHEMA = "mncs.standard.repository-manifest-validation/1"


def _identity(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate(manifest_path: Path, repository_root: Path, expected_repository: str | None) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {
            "schema_version": REPORT_SCHEMA,
            "valid": False,
            "manifest_identity": None,
            "errors": [{"code": "invalid-json", "message": str(error)}],
            "fingerprints": [],
        }
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for error in Draft202012Validator(schema).iter_errors(manifest):
        errors.append({"code": "schema", "message": error.message, "path": ".".join(map(str, error.path))})
    if not isinstance(manifest, dict):
        errors.append({"code": "root", "message": "manifest root must be an object"})
        manifest = {}
    repository = manifest.get("repository")
    if expected_repository and repository != expected_repository:
        errors.append({"code": "repository-identity", "message": f"manifest repository {repository!r} does not match {expected_repository!r}"})
    fingerprints: list[dict[str, Any]] = []
    contracts = manifest.get("contracts", {})
    provides = contracts.get("provides", []) if isinstance(contracts, dict) else []
    for index, contract in enumerate(provides if isinstance(provides, list) else []):
        sources = contract.get("fingerprint_sources", []) if isinstance(contract, dict) else []
        for source in sources if isinstance(sources, list) else []:
            if not isinstance(source, str) or not source:
                errors.append({"code": "fingerprint-path", "message": f"provides[{index}] has a non-string fingerprint source"})
                continue
            path = repository_root / source.rstrip("/")
            if not path.exists():
                errors.append({"code": "missing-fingerprint-path", "message": f"fingerprint source does not exist: {source}"})
                continue
            files = sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else [path]
            digest_entries = []
            for item in files:
                digest_entries.append((item.relative_to(repository_root).as_posix(), hashlib.sha256(item.read_bytes()).hexdigest()))
            fingerprints.append({"source": source, "identity": _identity(digest_entries)})
    consumes = contracts.get("consumes", []) if isinstance(contracts, dict) else []
    for index, contract in enumerate(consumes if isinstance(consumes, list) else []):
        evidence = contract.get("evidence_refs", []) if isinstance(contract, dict) else []
        for reference in evidence if isinstance(evidence, list) else []:
            if not isinstance(reference, str) or not reference:
                errors.append({"code": "evidence-path", "message": f"consumes[{index}] has a non-string evidence reference"})
                continue
            path = repository_root / reference.rstrip("/")
            if not path.exists():
                errors.append({"code": "missing-evidence-path", "message": f"consumed-contract evidence does not exist: {reference}"})
    report = {
        "schema_version": REPORT_SCHEMA,
        "valid": not errors,
        "manifest_identity": "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "manifest": {"repository": repository, "revision": manifest.get("revision")},
        "errors": errors,
        "fingerprints": fingerprints,
    }
    report["validation_identity"] = _identity(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--repository")
    args = parser.parse_args()
    result = validate(args.manifest, args.repository_root, args.repository)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
