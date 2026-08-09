"""Command-line interface for the offline MNCS validator."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .assurance import validate_rc_file
from .attestation import (
    attest,
    generate_key,
    inspect_key,
    load_json,
    load_public_record,
    verify_attestation,
    write_json,
)
from .canonical import canonical_sha256_file, canonicalize_file
from .errors import MncsError
from .execution_bundle import build_execution_bundle, verify_execution_bundle_archive
from .execution_receipt import validate_execution_receipt_file
from .hashing import hash_path, sha256_bytes
from .package import inspect_package, pack, unpack, verify_package
from .placement import validate_placement_file
from .provider import inspect_provider, run_descriptor, verify_result
from .rc_corpus import default_corpus_path, run_corpus
from .reporting import (
    manifest_summary,
    render_comparison,
    render_summary,
    render_validation,
)
from .schemas import SCHEMA_NAMES, load_schema
from .trust import evaluate, validate_policy
from .validation import compare_manifests, load_json_object, validate_bundle, validate_manifest

CURRENT_SCHEMA_VERSION = "0.2"
SUPPORTED_SCHEMA_VERSIONS = ("0.1", "0.1.1", "0.2")
NORMATIVE_STANDARD_FAMILY = "MNCS 0.2"
RELEASE_CANDIDATE_FAMILIES = ("MNCS 0.3-rc.1", "MNCDS 0.1-rc.1")


def _parse_evaluation_time(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--at must include an RFC 3339 UTC offset")
    return parsed


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
    certify.add_argument("--trust-policy", type=Path)
    certify.add_argument("--attestation", type=Path)
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
    certify_bundle.add_argument("--trust-policy", type=Path)
    certify_bundle.add_argument("--attestation", type=Path)
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

    canonicalize = subparsers.add_parser("canonicalize", help="emit RFC 8785 JSON")
    canonicalize.add_argument("file", type=Path)

    key = subparsers.add_parser("key", help="manage offline Ed25519 keys")
    key_commands = key.add_subparsers(dest="key_command", required=True)
    key_generate = key_commands.add_parser("generate", help="create a private key")
    key_generate.add_argument("private_path", type=Path)
    key_generate.add_argument("--public", type=Path)
    _json_option(key_generate)
    key_inspect = key_commands.add_parser("inspect", help="inspect a key")
    key_inspect.add_argument("key", type=Path)
    _json_option(key_inspect)

    attest_command = subparsers.add_parser("attest", help="sign a canonical statement")
    attest_command.add_argument("statement", type=Path)
    attest_command.add_argument("--key", required=True, type=Path)
    attest_command.add_argument("--output", required=True, type=Path)
    attest_command.add_argument("--append", action="store_true")
    _json_option(attest_command)

    verify_attestation_command = subparsers.add_parser(
        "verify-attestation",
        help="verify signatures separately from trust",
    )
    verify_attestation_command.add_argument("envelope", type=Path)
    verify_attestation_command.add_argument("--key", action="append", required=True, type=Path)
    verify_attestation_command.add_argument("--subject")
    verify_attestation_command.add_argument("--contract")
    verify_attestation_command.add_argument("--environment")
    _json_option(verify_attestation_command)

    trust = subparsers.add_parser("trust", help="validate or evaluate trust policy")
    trust_commands = trust.add_subparsers(dest="trust_command", required=True)
    validate_policy_command = trust_commands.add_parser(
        "validate-policy",
        help="validate a deterministic trust policy",
    )
    validate_policy_command.add_argument("policy", type=Path)
    _json_option(validate_policy_command)
    evaluate_command = trust_commands.add_parser("evaluate", help="evaluate trust")
    evaluate_command.add_argument("envelope", type=Path)
    evaluate_command.add_argument("policy", type=Path)
    evaluate_command.add_argument("--subject")
    evaluate_command.add_argument("--contract")
    evaluate_command.add_argument("--environment")
    _json_option(evaluate_command)

    pack_command = subparsers.add_parser("pack", help="create a deterministic .mncs package")
    pack_command.add_argument("bundle", type=Path)
    pack_command.add_argument("--output", required=True, type=Path)
    pack_command.add_argument("--attestation", type=Path)
    _json_option(pack_command)
    inspect_package_command = subparsers.add_parser(
        "inspect-package",
        help="inspect package structure and limits",
    )
    inspect_package_command.add_argument("package", type=Path)
    _json_option(inspect_package_command)
    verify_package_command = subparsers.add_parser(
        "verify-package",
        help="verify package integrity",
    )
    verify_package_command.add_argument("package", type=Path)
    _json_option(verify_package_command)
    unpack_command = subparsers.add_parser("unpack", help="securely unpack a verified package")
    unpack_command.add_argument("package", type=Path)
    unpack_command.add_argument("--output", required=True, type=Path)
    _json_option(unpack_command)
    certify_package = subparsers.add_parser(
        "certify-package",
        help="verify package integrity and optional trust",
    )
    certify_package.add_argument("package", type=Path)
    certify_package.add_argument("--trust-policy", type=Path)
    certify_package.add_argument("--attestation", type=Path)
    _json_option(certify_package)

    provider = subparsers.add_parser("provider", help="explicitly run provider protocol")
    provider_commands = provider.add_subparsers(dest="provider_command", required=True)
    provider_inspect = provider_commands.add_parser("inspect", help="request capabilities")
    provider_inspect.add_argument("provider_argv", nargs="+")
    provider_inspect.add_argument("--timeout", type=float, default=30.0)
    _json_option(provider_inspect)
    provider_run = provider_commands.add_parser("run", help="run a descriptor request")
    provider_run.add_argument("descriptor", type=Path)
    provider_run.add_argument("request", type=Path)
    provider_run.add_argument("--timeout", type=float)
    _json_option(provider_run)
    provider_verify = provider_commands.add_parser(
        "verify-result",
        help="validate a provider result without execution",
    )
    provider_verify.add_argument("result", type=Path)
    _json_option(provider_verify)

    schema = subparsers.add_parser("schema", help="print a bundled JSON Schema")
    schema.add_argument("name", choices=sorted(SCHEMA_NAMES))
    _json_option(schema)

    validate_record = subparsers.add_parser(
        "validate-record",
        help="validate an MNCS 0.3 release-candidate record offline",
    )
    validate_record.add_argument(
        "kind",
        choices=("contract", "assurance", "threat", "measurement"),
    )
    validate_record.add_argument("record", type=Path)
    validate_record.add_argument(
        "--at",
        help="evaluate freshness at an RFC 3339 timestamp; defaults to current time",
    )
    validate_record.add_argument("--require-pass", action="store_true")
    _json_option(validate_record)

    validate_placement = subparsers.add_parser(
        "validate-placement",
        help="validate experimental execution-placement evidence without executing it",
    )
    validate_placement.add_argument("record", type=Path)
    validate_placement.add_argument("--require-pass", action="store_true")
    _json_option(validate_placement)

    validate_receipt = subparsers.add_parser(
        "validate-execution-receipt",
        help="validate an experimental runner-produced execution receipt",
    )
    validate_receipt.add_argument("record", type=Path)
    validate_receipt.add_argument("--placement", type=Path)
    validate_receipt.add_argument("--bundle", type=Path)
    validate_receipt.add_argument("--require-pass", action="store_true")
    _json_option(validate_receipt)

    execution_bundle = subparsers.add_parser(
        "bundle", help="create or verify an experimental immutable execution bundle"
    )
    execution_bundle_commands = execution_bundle.add_subparsers(
        dest="execution_bundle_command", required=True
    )
    bundle_create = execution_bundle_commands.add_parser(
        "create", help="create a deterministic execution-bundle ZIP"
    )
    bundle_create.add_argument("--manifest", required=True, type=Path)
    bundle_create.add_argument("--source", required=True, type=Path)
    bundle_create.add_argument("--output", required=True, type=Path)
    _json_option(bundle_create)
    bundle_verify = execution_bundle_commands.add_parser(
        "verify", help="verify an execution-bundle ZIP without extracting it"
    )
    bundle_verify.add_argument("archive", type=Path)
    bundle_verify.add_argument("--expected-bundle-identity")
    bundle_verify.add_argument("--expected-archive-identity")
    _json_option(bundle_verify)

    migration = subparsers.add_parser(
        "migration-inspect",
        help="inspect version dispatch without upgrading or rewriting a record",
    )
    migration.add_argument("record", type=Path)
    _json_option(migration)

    corpus = subparsers.add_parser("corpus", help="run an offline conformance corpus")
    corpus_commands = corpus.add_subparsers(dest="corpus_command", required=True)
    rc_corpus = corpus_commands.add_parser(
        "release-candidate",
        help="run the MNCS 0.3 and MNCDS 0.1 release-candidate corpus",
    )
    rc_corpus.add_argument(
        "--corpus",
        type=Path,
        default=default_corpus_path(),
    )
    _json_option(rc_corpus)

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
            "Schema 0.2 requires indexed gate results and content-addressed identity records. "
            "Run `mncs hash PATH`, then replace this file with manifest.json."
        ),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "mncs_version": "0.2",
        "machine_sha256": hash_path(path / "machine" / "generated.py"),
        "reference_sha256": hash_path(path / "reference" / "reference.py"),
        "example_generator_identity_hash": sha256_bytes(b"replace-me generator identity record"),
    }
    (path / "manifest.template.json").write_text(
        json.dumps(template, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"initialized": str(path), "template": str(path / "manifest.template.json")}


def _trust_result(
    target: Path,
    policy_path: Path,
    attestation_path: Path | None,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    envelope_path = attestation_path or (
        target.parent / "attestation.json" if target.is_file() else target / "attestation.json"
    )
    policy = load_json(policy_path)
    envelope = load_json(envelope_path)
    subject = hash_path(target)
    contract = None
    environment = None
    if manifest is not None:
        component = manifest.get("component", {})
        env = manifest.get("environment", {})
        if isinstance(component, dict):
            contract_value = component.get("contract_id")
            contract = contract_value if isinstance(contract_value, str) else None
        if isinstance(env, dict):
            environment_value = env.get("fingerprint")
            environment = environment_value if isinstance(environment_value, str) else None
    return evaluate(
        envelope,
        policy,
        expected_subject=subject,
        expected_contract=contract,
        expected_environment=environment,
    ).as_dict()


def run(args: argparse.Namespace) -> int:
    """Dispatch a parsed command."""

    command = args.command
    result: Any
    report: Any
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
        output = report.as_dict()
        if args.trust_policy is not None and report.certification_eligible:
            output["trust"] = _trust_result(
                args.manifest,
                args.trust_policy,
                args.attestation,
                load_json_object(args.manifest),
            )
            report.certification_eligible = bool(output["trust"]["certified"])
        _write_json(output) if args.json else print(render_validation(report))
        if not report.valid:
            return 1
        return 0 if report.certification_eligible else 3
    if command == "certify-bundle":
        _require_directory(args.directory)
        report = validate_bundle(args.directory, allow_legacy=args.allow_legacy)
        output = report.as_dict()
        if args.trust_policy is not None and report.certification_eligible:
            output["trust"] = _trust_result(
                args.directory,
                args.trust_policy,
                args.attestation,
                load_json_object(args.directory / "manifest.json"),
            )
            report.certification_eligible = bool(output["trust"]["certified"])
        _write_json(output) if args.json else print(render_validation(report))
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
    if command == "canonicalize":
        sys.stdout.buffer.write(canonicalize_file(args.file) + b"\n")
        return 0
    if command == "key":
        if args.key_command == "generate":
            result = generate_key(args.private_path, args.public)
        else:
            result = inspect_key(args.key)
        _write_json(result) if args.json else print(json.dumps(result, sort_keys=True))
        return 0
    if command == "attest":
        statement = load_json(args.statement)
        existing = load_json(args.output) if args.append else None
        if args.output.exists() and not args.append:
            raise MncsError(f"refusing to overwrite attestation: {args.output}")
        envelope = attest(statement, args.key, existing)
        write_json(args.output, envelope)
        result = {
            "output": str(args.output),
            "signatures": len(envelope["signatures"]),
            "payload_sha256": canonical_sha256_file(args.statement),
        }
        _write_json(result) if args.json else print(str(args.output))
        return 0
    if command == "verify-attestation":
        result = verify_attestation(
            load_json(args.envelope),
            [load_public_record(path) for path in args.key],
            expected_subject=args.subject,
            expected_contract=args.contract,
            expected_environment=args.environment,
        )
        _write_json(result.as_dict()) if args.json else print(
            "VALID" if result.cryptographically_valid and not result.expired else "INVALID"
        )
        return 0 if result.cryptographically_valid and not result.expired else 1
    if command == "trust":
        policy = load_json(args.policy)
        if args.trust_command == "validate-policy":
            errors = validate_policy(policy)
            result = {"valid": not errors, "errors": errors}
            _write_json(result) if args.json else print(
                "VALID" if not errors else "\n".join(errors)
            )
            return 0 if not errors else 1
        result = evaluate(
            load_json(args.envelope),
            policy,
            expected_subject=args.subject,
            expected_contract=args.contract,
            expected_environment=args.environment,
        )
        _write_json(result.as_dict()) if args.json else print(
            "TRUSTED" if result.trusted else "UNTRUSTED"
        )
        return 0 if result.trusted else 3
    if command == "pack":
        result = pack(args.bundle, args.output, detached_attestation=args.attestation)
        _write_json(result) if args.json else print(result["package_sha256"])
        return 0
    if command in {"inspect-package", "verify-package"}:
        result = (
            inspect_package(args.package)
            if command == "inspect-package"
            else verify_package(args.package)
        )
        _write_json(result.as_dict()) if args.json else print(
            "VALID" if result.valid else "INVALID"
        )
        return 0 if result.valid else 1
    if command == "unpack":
        result = unpack(args.package, args.output)
        _write_json(result.as_dict()) if args.json else print(
            f"Unpacked {args.package} to {args.output}" if result.valid else "INVALID"
        )
        return 0 if result.valid else 1
    if command == "certify-package":
        report = verify_package(args.package)
        output = report.as_dict()
        certified = report.valid
        if args.trust_policy is not None and certified:
            output["trust"] = _trust_result(
                args.package,
                args.trust_policy,
                args.attestation,
                None,
            )
            certified = bool(output["trust"]["certified"])
        output["certified"] = certified
        _write_json(output) if args.json else print("CERTIFIED" if certified else "NOT CERTIFIED")
        return 0 if certified else (1 if not report.valid else 3)
    if command == "provider":
        if args.provider_command == "inspect":
            result = inspect_provider(args.provider_argv, timeout=args.timeout)
        elif args.provider_command == "run":
            result = run_descriptor(args.descriptor, load_json(args.request), timeout=args.timeout)
        else:
            result_value = load_json(args.result)
            errors = verify_result(result_value)
            result = {"valid": not errors, "errors": errors, "result": result_value}
            _write_json(result) if args.json else print(
                "VALID" if not errors else "\n".join(errors)
            )
            return 0 if not errors else 1
        _write_json(result) if args.json else print(json.dumps(result, sort_keys=True))
        return 0
    if command == "schema":
        schema = load_schema(args.name)
        _write_json(schema)
        return 0
    if command == "validate-record":
        _require_file(args.record)
        at = _parse_evaluation_time(args.at)
        report = validate_rc_file(args.record, args.kind, at=at)
        _write_json(report.as_dict()) if args.json else print(report.category)
        if not report.supported:
            return 4
        if not report.valid:
            return 1
        return 3 if args.require_pass and report.computed_status != "PASS" else 0
    if command == "validate-placement":
        _require_file(args.record)
        report = validate_placement_file(args.record)
        _write_json(report.as_dict()) if args.json else print(report.category)
        if not report.supported:
            return 4
        if not report.valid:
            return 1
        return 3 if args.require_pass and report.computed_status != "PASS" else 0
    if command == "validate-execution-receipt":
        _require_file(args.record)
        if args.placement is not None:
            _require_file(args.placement)
        if args.bundle is not None:
            _require_file(args.bundle)
        report = validate_execution_receipt_file(
            args.record, placement_path=args.placement, bundle_path=args.bundle
        )
        _write_json(report.as_dict()) if args.json else print(report.category)
        if not report.supported:
            return 4
        if not report.valid:
            return 1
        return 3 if args.require_pass and report.validation_status != "PASS" else 0
    if command == "bundle":
        if args.execution_bundle_command == "create":
            _require_file(args.manifest)
            _require_directory(args.source)
            report = build_execution_bundle(args.manifest, args.source, args.output)
        else:
            _require_file(args.archive)
            report = verify_execution_bundle_archive(
                args.archive,
                expected_bundle_identity=args.expected_bundle_identity,
                expected_archive_identity=args.expected_archive_identity,
            )
        _write_json(report.as_dict()) if args.json else print(report.category)
        return 0 if report.valid else (4 if not report.supported else 1)
    if command == "migration-inspect":
        _require_file(args.record)
        value = load_json_object(args.record)
        schema_version = value.get("schema_version")
        mncs_version = value.get("mncs_version")
        mncds_version = value.get("mncds_version")
        if mncds_version is not None:
            supported = mncds_version in {"0.1-draft", "0.1-rc.1"}
            family = "MNCDS"
            version_value = mncds_version
        else:
            supported = schema_version in {"0.1", "0.1.1", "0.2", "0.3-rc.1"}
            family = "MNCS"
            version_value = mncs_version or schema_version
        result = {
            "family": family,
            "version": version_value,
            "schema_version": schema_version,
            "supported": supported,
            "automatic_upgrade": False,
            "new_identity_required_for_material_change": True,
            "historical_claim_preserved": True,
        }
        _write_json(result) if args.json else print(json.dumps(result, sort_keys=True))
        return 0 if supported else 4
    if command == "corpus":
        if args.corpus_command != "release-candidate":
            raise AssertionError(f"unhandled corpus command: {args.corpus_command}")
        rc_summary, results = run_corpus(args.corpus)
        result = {"summary": rc_summary.as_dict(), "results": results}
        _write_json(result) if args.json else print(
            json.dumps(rc_summary.as_dict(), sort_keys=True)
        )
        return 0 if rc_summary.mismatched == 0 else 1
    if command == "version":
        version_result: dict[str, Any] = {
            "package": "mncs-validator",
            "package_version": __version__,
            "current_schema_version": CURRENT_SCHEMA_VERSION,
            "supported_schema_versions": list(SUPPORTED_SCHEMA_VERSIONS),
            "normative_standard_family": NORMATIVE_STANDARD_FAMILY,
            "release_candidate_families": list(RELEASE_CANDIDATE_FAMILIES),
            "record_schema_versions": ["0.3-rc.1"],
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
    except (MncsError, FileNotFoundError, PermissionError, ValueError) as exc:
        print(f"mncs: error: {exc}", file=sys.stderr)
        return 2
