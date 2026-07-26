"""Command-line interface for the offline MNCS validator."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import MncsError
from .hashing import hash_path, sha256_bytes
from .reporting import (
    manifest_summary,
    render_comparison,
    render_summary,
    render_validation,
)
from .schemas import SCHEMA_NAMES, load_schema
from .validation import compare_manifests, load_json_object, validate_bundle, validate_manifest


def _json_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def build_parser() -> argparse.ArgumentParser:
    """Build the public argument parser."""

    parser = argparse.ArgumentParser(prog="mncs", description="MNCS offline validator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="initialize an evidence bundle")
    init.add_argument("path", type=Path)
    _json_option(init)

    validate = subparsers.add_parser("validate", help="validate a manifest")
    validate.add_argument("manifest", type=Path)
    _json_option(validate)

    bundle = subparsers.add_parser("validate-bundle", help="validate a bundle")
    bundle.add_argument("directory", type=Path)
    _json_option(bundle)

    summarize = subparsers.add_parser("summarize", help="summarize a manifest")
    summarize.add_argument("manifest", type=Path)
    _json_option(summarize)

    compare = subparsers.add_parser("compare", help="Pareto-compare two manifests")
    compare.add_argument("manifest_a", type=Path)
    compare.add_argument("manifest_b", type=Path)
    _json_option(compare)

    hash_command = subparsers.add_parser("hash", help="hash a file or directory")
    hash_command.add_argument("path", type=Path)
    _json_option(hash_command)

    schema = subparsers.add_parser("schema", help="print a bundled JSON Schema")
    schema.add_argument("name", choices=sorted(SCHEMA_NAMES))
    _json_option(schema)

    version = subparsers.add_parser("version", help="print validator version")
    _json_option(version)
    return parser


def _write_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _initialize(path: Path) -> dict[str, Any]:
    if path.exists() and any(path.iterdir()):
        raise MncsError(f"refusing to initialize non-empty directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    for name in ("specification", "reference", "machine", "evidence", "provenance"):
        (path / name).mkdir(exist_ok=True)
    contract = "# Functional contract\n\nReplace this template with a readable contract.\n"
    reference = (
        "# SPDX-License-Identifier: Apache-2.0\n\n"
        "def transform(value: int) -> int:\n"
        "    return value\n"
    )
    machine = (
        "# SPDX-License-Identifier: Apache-2.0\n"
        "# MNCS-GENERATED: DO NOT EDIT\n"
        "# Generator: replace-me\n"
        "# Regenerate: replace-me\n\n"
        "def transform(value: int) -> int:\n    return value\n"
    )
    (path / "specification" / "contract.md").write_text(contract, encoding="utf-8")
    (path / "reference" / "reference.py").write_text(reference, encoding="utf-8")
    (path / "machine" / "generated.py").write_text(machine, encoding="utf-8")
    (path / "README.md").write_text(
        "# MNCS evidence bundle\n\nComplete the manifest and evidence before validation.\n",
        encoding="utf-8",
    )
    template = {
        "note": "Run `mncs hash PATH` for identities, then replace this file with manifest.json.",
        "machine_sha256": hash_path(path / "machine" / "generated.py"),
        "reference_sha256": hash_path(path / "reference" / "reference.py"),
        "generator_identity_hash": sha256_bytes(b"replace-me generator"),
    }
    (path / "manifest.template.json").write_text(
        json.dumps(template, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"initialized": str(path), "template": str(path / "manifest.template.json")}


def run(args: argparse.Namespace) -> int:
    """Dispatch a parsed command."""

    command = args.command
    if command == "init":
        init_result = _initialize(args.path)
        _write_json(init_result) if args.json else print(f"Initialized {args.path}")
        return 0
    if command == "validate":
        report = validate_manifest(args.manifest)
        _write_json(report.as_dict()) if args.json else print(render_validation(report))
        return 0 if report.valid else 1
    if command == "validate-bundle":
        report = validate_bundle(args.directory)
        _write_json(report.as_dict()) if args.json else print(render_validation(report))
        return 0 if report.valid else 1
    if command == "summarize":
        summary = manifest_summary(load_json_object(args.manifest))
        _write_json(summary) if args.json else print(render_summary(summary))
        return 0
    if command == "compare":
        comparison = compare_manifests(
            load_json_object(args.manifest_a),
            load_json_object(args.manifest_b),
        )
        _write_json(comparison.as_dict()) if args.json else print(render_comparison(comparison))
        return 0
    if command == "hash":
        result = {"path": str(args.path), "sha256": hash_path(args.path)}
        _write_json(result) if args.json else print(result["sha256"])
        return 0
    if command == "schema":
        schema = load_schema(args.name)
        _write_json(schema)
        return 0
    if command == "version":
        result = {"package": "mncs-validator", "version": __version__, "mncs_version": "0.1"}
        _write_json(result) if args.json else print(f"mncs-validator {__version__} (MNCS 0.1)")
        return 0
    raise AssertionError(f"unhandled command: {command}")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point with stable errors and exit codes."""

    try:
        return run(build_parser().parse_args(argv))
    except (MncsError, FileNotFoundError, PermissionError) as exc:
        print(f"mncs: error: {exc}", file=sys.stderr)
        return 2
