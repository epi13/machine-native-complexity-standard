"""Command-line interface for experimental MNCDS validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import MncsError
from .mncds import validate_development_record

MNCDS_VERSION = "0.1-draft"
MNCDS_SCHEMA_VERSION = "0.1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mncds",
        description="Offline validator for Machine-Native Complexity Development records",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate a development record")
    validate.add_argument("record", type=Path)
    validate.add_argument(
        "--require-pass",
        action="store_true",
        help="return exit 3 for a valid record whose computed status is not PASS",
    )
    validate.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    version = subparsers.add_parser("version", help="print MNCDS validator version")
    version.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.command == "validate":
        if not args.record.is_file():
            raise FileNotFoundError(args.record)
        report = validate_development_record(args.record)
        if args.json:
            print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
        else:
            print(report.computed_status if report.valid else "INVALID")
            for issue in report.issues:
                suffix = f" [{issue.path}]" if issue.path else ""
                print(f"{issue.code}: {issue.message}{suffix}")
            for warning in report.warnings:
                suffix = f" [{warning.path}]" if warning.path else ""
                print(f"warning {warning.code}: {warning.message}{suffix}")
        if not report.valid:
            return 1
        return 3 if args.require_pass and report.computed_status != "PASS" else 0

    if args.command == "version":
        result = {
            "package": "mncs-validator",
            "mncds_version": MNCDS_VERSION,
            "schema_version": MNCDS_SCHEMA_VERSION,
            "status": "experimental",
        }
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(
                f"mncds {MNCDS_VERSION} "
                f"(schema {MNCDS_SCHEMA_VERSION}; experimental)"
            )
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except (MncsError, FileNotFoundError, PermissionError) as exc:
        print(f"mncds: error: {exc}", file=sys.stderr)
        return 2
