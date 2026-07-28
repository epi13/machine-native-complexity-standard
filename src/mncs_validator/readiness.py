"""Experimental Wave Four evidence-custody and claim-readiness semantics."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

STATUSES = {"PASS", "FAIL", "UNKNOWN"}


def aggregate_status(statuses: Iterable[str]) -> str:
    """Apply FAIL > UNKNOWN > PASS without manufacturing evidence."""

    values = list(statuses)
    if not values or any(value not in STATUSES for value in values):
        return "UNKNOWN"
    if "FAIL" in values:
        return "FAIL"
    if "UNKNOWN" in values:
        return "UNKNOWN"
    return "PASS"


def _sha256_identity(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def custody_findings(record: dict[str, Any]) -> list[str]:
    """Return stable findings for a protected-evidence custody record."""

    findings: list[str] = []
    custodian = record.get("custodian", {})
    evaluator = record.get("evaluator", {})
    developer_id = record.get("developer_id")
    custodian_id = custodian.get("id") if isinstance(custodian, dict) else None
    evaluator_id = evaluator.get("id") if isinstance(evaluator, dict) else None

    if custodian_id in {None, developer_id, evaluator_id}:
        findings.append("custodian must be identified and distinct from developer and evaluator")
    if evaluator_id in {None, developer_id, custodian_id}:
        findings.append("evaluator must be identified and distinct from developer and custodian")

    for field in (
        "preregistration_identity",
        "candidate_freeze_identity",
        "corpus_identity",
        "raw_artifact_identity",
        "normalized_result_identity",
        "attestation_identity",
    ):
        if not _sha256_identity(record.get(field)):
            findings.append(f"{field} must be a sha256 identity")

    timestamps = record.get("timestamps", {})
    if not isinstance(timestamps, dict):
        findings.append("timestamps must be an object")
        return sorted(findings)
    ordered = [
        _parse_time(timestamps.get("preregistered_at")),
        _parse_time(timestamps.get("candidate_frozen_at")),
        _parse_time(timestamps.get("corpus_disclosed_at")),
        _parse_time(timestamps.get("evaluated_at")),
    ]
    if any(value is None for value in ordered):
        findings.append("all custody timestamps must be valid ISO-8601 values")
    else:
        complete_order = [value for value in ordered if value is not None]
        if complete_order != sorted(complete_order):
            findings.append(
                "custody timestamps must follow preregistration, freeze, disclosure, "
                "evaluation order"
            )

    if record.get("corpus_embedded_in_repository") is not False:
        findings.append("protected corpus must not be embedded in the public repository")
    if record.get("development_access_before_disclosure") is not False:
        findings.append("development participants must not access the corpus before disclosure")
    if record.get("result") not in STATUSES:
        findings.append("result must be PASS, FAIL, or UNKNOWN")
    return sorted(findings)


def cross_host_agreement(records: list[dict[str, Any]]) -> tuple[str, list[str], dict[str, Any]]:
    """Reconcile two or more composed evidence epochs by identity and semantic result."""

    findings: list[str] = []
    if len(records) < 2:
        return "UNKNOWN", ["at least two host records are required"], {}

    contract_ids = {record.get("system_contract_id") for record in records}
    epoch_ids = {record.get("epoch_id") for record in records}
    identity_sets = {tuple(sorted(record.get("identities", {}).items())) for record in records}
    platforms = {
        (
            record.get("environment", {}).get("platform"),
            record.get("environment", {}).get("machine"),
        )
        for record in records
    }
    if len(contract_ids) != 1:
        findings.append("system contract identity mismatch")
    if len(epoch_ids) != 1:
        findings.append("epoch identity mismatch")
    if len(identity_sets) != 1:
        findings.append("component or tool identity mismatch")
    if len(platforms) < 2:
        findings.append("records do not represent distinct host environments")

    gate_statuses: list[str] = []
    digests: set[str] = set()
    for record in records:
        build = record.get("build_results", {})
        recovery = record.get("recovery_drill", {})
        mutation = record.get("mutation_campaign", {})
        gate_statuses.extend(
            str(build.get(name, "UNKNOWN"))
            for name in (
                "binding_regeneration",
                "c11_build",
                "go_tests",
                "go_vet",
                "go_race",
                "go_fuzz_smoke",
                "rust_toolchain",
            )
        )
        gate_statuses.extend(
            str(recovery.get(name, "UNKNOWN"))
            for name in (
                "readable_uninterrupted",
                "composed_uninterrupted",
                "recovery",
                "replacement",
                "identity_rejection",
            )
        )
        gate_statuses.append(str(mutation.get("status", "UNKNOWN")))
        for name in (
            "readable_output_digest",
            "composed_output_digest",
            "recovery_output_digest",
            "replacement_output_digest",
        ):
            value = recovery.get(name)
            if isinstance(value, str):
                digests.add(value)

    if len(digests) > 1:
        findings.append("semantic output digest mismatch")
    gate_status = aggregate_status(gate_statuses)
    if gate_status == "FAIL":
        findings.append("one or more required host gates failed")
    elif gate_status == "UNKNOWN":
        findings.append("one or more required host gates are unknown")

    if any("mismatch" in finding or "failed" in finding for finding in findings):
        status = "FAIL"
    elif findings:
        status = "UNKNOWN"
    else:
        status = "PASS"
    summary = {
        "record_count": len(records),
        "host_environments": sorted(
            f"{platform or 'unknown'}:{machine or 'unknown'}"
            for platform, machine in platforms
        ),
        "semantic_output_digests": sorted(digests),
        "required_gate_status": gate_status,
    }
    return status, sorted(findings), summary


def evaluate_claim_readiness(record: dict[str, Any]) -> dict[str, Any]:
    """Evaluate MNCS and MNCDS readiness as separate bounded claims."""

    mncs_inputs = record.get("mncs_inputs", {})
    mncds_inputs = record.get("mncds_inputs", {})
    mncs_status = (
        aggregate_status(str(value) for value in mncs_inputs.values())
        if isinstance(mncs_inputs, dict)
        else "UNKNOWN"
    )
    mncds_status = (
        aggregate_status(str(value) for value in mncds_inputs.values())
        if isinstance(mncds_inputs, dict)
        else "UNKNOWN"
    )

    promotion_authorized = (
        mncs_status == "PASS"
        and mncds_status == "PASS"
        and record.get("release_authorization") == "PASS"
    )
    disposition = "PASS" if promotion_authorized else "REVIEW_REQUIRED"
    if (
        mncs_status == "FAIL"
        or mncds_status == "FAIL"
        or record.get("release_authorization") == "FAIL"
    ):
        disposition = "FAIL"
    return {
        "formal_mncs_status": mncs_status,
        "formal_mncds_status": mncds_status,
        "promotion_authorized": promotion_authorized,
        "disposition": disposition,
    }
