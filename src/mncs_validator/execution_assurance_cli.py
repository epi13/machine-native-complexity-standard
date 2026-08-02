"""Offline combined test-evidence commands for MNCS and MNCDS."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal, cast

from .assurance import validate_rc_file
from .assurance.status import Status
from .errors import MncsError
from .execution_assurance import (
    ExecutionAssuranceReport,
    SubjectKind,
    parse_evaluation_time,
    validate_execution_assurance_file,
)
from .mncds import MncdsValidationReport, validate_development_record

Family = Literal["MNCS", "MNCDS"]
MNCS_KINDS = ("contract", "assurance", "threat", "measurement")


def _json_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def _common_assurance_arguments(parser: argparse.ArgumentParser, *, mncs: bool) -> None:
    parser.add_argument("assurance", type=Path)
    parser.add_argument("--subject", type=Path)
    if mncs:
        parser.add_argument("--kind", choices=MNCS_KINDS)
    parser.add_argument(
        "--at",
        help="evaluate challenge freshness at an RFC 3339 timestamp; defaults to current time",
    )
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="return exit 3 unless combined test and execution assurance are PASS",
    )
    _json_option(parser)


def build_parser(family: Family) -> argparse.ArgumentParser:
    """Build one family-specific execution-assurance parser."""

    prog = "mncs-test-evidence" if family == "MNCS" else "mncds-test-evidence"
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            f"Offline {family} test-evidence validation with separate execution assurance"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    assurance = subparsers.add_parser(
        "validate-assurance",
        help="validate one companion execution-assurance record",
    )
    _common_assurance_arguments(assurance, mncs=family == "MNCS")

    validate = subparsers.add_parser(
        "validate",
        help=f"validate a {family} subject together with its execution-assurance record",
    )
    if family == "MNCS":
        validate.add_argument("kind", choices=MNCS_KINDS)
    validate.add_argument("subject", type=Path)
    validate.add_argument("assurance", type=Path)
    validate.add_argument(
        "--at",
        help="evaluate record freshness at an RFC 3339 timestamp; defaults to current time",
    )
    validate.add_argument(
        "--require-pass",
        action="store_true",
        help="return exit 3 unless both subject and execution assurance are PASS",
    )
    _json_option(validate)
    return parser


def _category(
    subject: dict[str, Any] | None,
    assurance: ExecutionAssuranceReport,
) -> str:
    if subject is not None and not bool(subject["supported"]):
        return "UNSUPPORTED"
    if not assurance.supported:
        return "UNSUPPORTED"
    if subject is not None and not bool(subject["valid"]):
        return "INVALID"
    if not assurance.valid:
        return "INVALID"
    return assurance.combined_status


def _exit_code(category: str, *, require_pass: bool) -> int:
    if category == "UNSUPPORTED":
        return 4
    if category == "INVALID":
        return 1
    return 3 if require_pass and category != "PASS" else 0


def _emit(value: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(value["category"])


def _validate_assurance_only(args: argparse.Namespace, family: Family) -> int:
    subject = args.subject
    if subject is not None and not subject.is_file():
        raise FileNotFoundError(subject)
    if not args.assurance.is_file():
        raise FileNotFoundError(args.assurance)
    expected_kind: SubjectKind = (
        cast(SubjectKind, args.kind) if family == "MNCS" else "development-record"
    )
    report = validate_execution_assurance_file(
        args.assurance,
        subject_path=subject,
        expected_family=family,
        expected_kind=expected_kind,
        at=parse_evaluation_time(args.at),
    )
    value = report.as_dict()
    _emit(value, as_json=args.json)
    return _exit_code(report.category, require_pass=args.require_pass)


def _mncs_subject(args: argparse.Namespace) -> tuple[dict[str, Any], Status]:
    report = validate_rc_file(
        args.subject,
        args.kind,
        at=parse_evaluation_time(args.at),
    )
    return report.as_dict(), report.computed_status


def _mncds_subject(args: argparse.Namespace) -> tuple[dict[str, Any], Status]:
    report: MncdsValidationReport = validate_development_record(args.subject)
    return report.as_dict(), report.computed_status


def _validate_combined(args: argparse.Namespace, family: Family) -> int:
    if not args.subject.is_file():
        raise FileNotFoundError(args.subject)
    if not args.assurance.is_file():
        raise FileNotFoundError(args.assurance)

    expected_kind: SubjectKind
    if family == "MNCS":
        subject, subject_status = _mncs_subject(args)
        expected_kind = cast(SubjectKind, args.kind)
    else:
        subject, subject_status = _mncds_subject(args)
        expected_kind = "development-record"

    expected_test_status = (
        subject_status if bool(subject["supported"]) and bool(subject["valid"]) else None
    )
    assurance = validate_execution_assurance_file(
        args.assurance,
        subject_path=args.subject,
        expected_family=family,
        expected_kind=expected_kind,
        expected_test_status=expected_test_status,
        at=parse_evaluation_time(args.at),
    )
    category = _category(subject, assurance)
    value = {
        "family": family,
        "subject": subject,
        "execution_assurance": assurance.as_dict(),
        "combined_status": assurance.combined_status,
        "category": category,
    }
    _emit(value, as_json=args.json)
    return _exit_code(category, require_pass=args.require_pass)


def run(args: argparse.Namespace, family: Family) -> int:
    """Dispatch a parsed family-specific test-evidence command."""

    if args.command == "validate-assurance":
        return _validate_assurance_only(args, family)
    if args.command == "validate":
        return _validate_combined(args, family)
    raise AssertionError(f"unhandled command: {args.command}")


def _main(family: Family, argv: list[str] | None = None) -> int:
    try:
        return run(build_parser(family).parse_args(argv), family)
    except (MncsError, FileNotFoundError, PermissionError, ValueError) as exc:
        prog = "mncs-test-evidence" if family == "MNCS" else "mncds-test-evidence"
        print(f"{prog}: error: {exc}", file=sys.stderr)
        return 2


def mncs_main(argv: list[str] | None = None) -> int:
    """Entry point for MNCS companion test-evidence validation."""

    return _main("MNCS", argv)


def mncds_main(argv: list[str] | None = None) -> int:
    """Entry point for MNCDS companion test-evidence validation."""

    return _main("MNCDS", argv)
