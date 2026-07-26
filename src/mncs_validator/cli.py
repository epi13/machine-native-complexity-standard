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

CURRENT_SCHEMA_VERSION = "0.1.1"
SUPPORTED_SCHEMA_VERSIONS = ("0.1", "0.1.1")
NORMATIVE_STANDARD_FAMILY = "MNCS 0.1"


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
    validate.add_argument(
        "--require-pass",
        action="store_true",
        help="require a certifiable computed PASS",
    )
    validate.add_argument(
        "--allow-legacy",
        action="store_true",
        help="allow reduced-assurance certification of a schema 0.1 PASS",
    )
    _json_option(validate)

    bundle = subparsers.add_parser("validate-bundle", help="validate a bundle")
    bundle.add_argument("directory", type=Path)
    bundle.add_argument("--require-pass", action="store_true", help="require computed PASS")
    bundle.add_argument("--allow-legacy", action="store_true", help="allow legacy PASS override")
    _json_option(bundle)

    certify = subparsers.add_parser("certify", help="require a certifiable manifest PASS")
    certify.add_argument("manifest", type=Path)
    certify.add_argument("--allow-legacy", action="store_true", help="allow legacy PASS override")
    _json_option(certify)

    certify_bundle = subparsers.add_parser(
        "certify-bundle",
        help="require a certifiable bundle PASS",
    )
    certify_bundle.add_argument("directory", type=Path)
    certify_bundle.add_argument(
        "--allow-legacy",
        action="store_true",
        help="allow legacy PASS override",
    )
    _json_option(certify_bundle)

    summarize = subparsers.add_parser("summarize", help="summarize a manifest")
    summarize.add_argument("manifest", type=Path)
    _json_option(summarize)

    compare = subparsers.add_parser("compare", help="Pareto-compare two manifests")
    compare.add_argument("manifest_a", type=Path)
    compare.add_argument("manifest_b", type=Path)
    compare.add_argument(
        "--allow-uncertified",
        action="store_true",
        help="permit descriptive comparison with a prominent warning",
    )
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


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def _require_directory(path: Path) -> None:
    if not path.is_dir():
        raise FileNotFoundError(path)


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
        "note": (
            "Schema 0.1.1 requires indexed gate results and content-addressed identity records. "
            "Run `mncs hash PATH`, then replace this file with manifest.json."
        ),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "mncs_version": "0.1",
        "machine_sha256": hash_path(path / "machine" / "generated.py"),
        "reference_sha256": hash_path(path / "reference" / "reference.py"),
        "example_generator_identity_hash": sha256_bytes(b"replace-me generator identity record"),
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
        _require_file(args.manifest)
        report = validate_manifest(args.manifest, allow_legacy=args.allow_legacy)
        _write_json(report.as_dict()) if args.json else print(render_validation(report))
        if not report.valid:
            return 1
        return 3 if args.require_pass and not report.certification_eligible else 0
    if command == "validate-bundle":
        _require_directory(args.directory)
        report = validate_bundle(args.directory, allow_legacy=args.allow_legacy)
        _write_json(report.as_dict()) if args.json else print(render_validation(report))
        if not report.valid:
            return 1
        return 3 if args.require_pass and not report.certification_eligible else 0
    if command == "certify":
        _require_file(args.manifest)
        report = validate_manifest(args.manifest, allow_legacy=args.allow_legacy)
        _write_json(report.as_dict()) if args.json else print(render_validation(report))
        if not report.valid:
            return 1
        return 0 if report.certification_eligible else 3
    if command == "certify-bundle":
        _require_directory(args.directory)
        report = validate_bundle(args.directory, allow_legacy=args.allow_legacy)
        _write_json(report.as_dict()) if args.json else print(render_validation(report))
        if not report.valid:
            return 1
        return 0 if report.certification_eligible else 3
    if command == "summarize":
        _require_file(args.manifest)
        summary = manifest_summary(load_json_object(args.manifest))
        _write_json(summary) if args.json else print(render_summary(summary))
        return 0
    if command == "compare":
        _require_file(args.manifest_a)
        _require_file(args.manifest_b)
        first_report = validate_manifest(args.manifest_a)
        second_report = validate_manifest(args.manifest_b)
        comparison = compare_manifests(
            load_json_object(args.manifest_a),
            load_json_object(args.manifest_b),
            first_report=first_report,
            second_report=second_report,
            allow_uncertified=args.allow_uncertified,
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
        version_result: dict[str, Any] = {
            "package": "mncs-validator",
            "package_version": __version__,
            "current_schema_version": CURRENT_SCHEMA_VERSION,
            "supported_schema_versions": list(SUPPORTED_SCHEMA_VERSIONS),
            "normative_standard_family": NORMATIVE_STANDARD_FAMILY,
        }
        _write_json(version_result) if args.json else print(
            f"mncs-validator {__version__} "
            f"(schema {CURRENT_SCHEMA_VERSION}; {NORMATIVE_STANDARD_FAMILY})"
        )
        return 0
    raise AssertionError(f"unhandled command: {command}")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point with stable errors and exit codes."""

    try:
        return run(build_parser().parse_args(argv))
    except (MncsError, FileNotFoundError, PermissionError) as exc:
        print(f"mncs: error: {exc}", file=sys.stderr)
        return 2
