"""Deterministic offline MNCS trust-policy evaluation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from .attestation import AttestationVerification, verify_attestation
from .errors import MncsError


@dataclass(frozen=True)
class TrustEvaluation:
    cryptographically_valid: bool
    trusted: bool
    certified: bool
    trusted_signers: list[str]
    satisfied_roles: list[str]
    reasons: list[str]
    verification: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_policy(policy: dict[str, Any]) -> list[str]:
    """Return stable validation errors for the normative policy subset."""

    errors: list[str] = []
    if policy.get("schema_version") != "0.2":
        errors.append("schema_version must be 0.2")
    if not isinstance(policy.get("trust_domain"), str) or not policy["trust_domain"]:
        errors.append("trust_domain must be a non-empty string")
    keys = policy.get("keys")
    if not isinstance(keys, list) or not keys:
        errors.append("keys must be a non-empty array")
        keys = []
    seen: set[str] = set()
    for index, key in enumerate(keys):
        if not isinstance(key, dict):
            errors.append(f"keys/{index} must be an object")
            continue
        keyid = key.get("keyid")
        if not isinstance(keyid, str) or not keyid:
            errors.append(f"keys/{index}/keyid must be non-empty")
        elif keyid in seen:
            errors.append(f"duplicate keyid: {keyid}")
        else:
            seen.add(keyid)
        roles = key.get("roles")
        if (
            not isinstance(roles, list)
            or not roles
            or not all(isinstance(role, str) for role in roles)
        ):
            errors.append(f"keys/{index}/roles must be a non-empty string array")
    for name in ("minimum_signatures", "distinct_signers"):
        value = policy.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{name} must be an integer >= 1")
    allowed = policy.get("allowed_predicate_types")
    if not isinstance(allowed, list) or not allowed:
        errors.append("allowed_predicate_types must be non-empty")
    required_roles = policy.get("required_roles", [])
    if not isinstance(required_roles, list) or not all(
        isinstance(role, str) for role in required_roles
    ):
        errors.append("required_roles must be a string array")
    if policy.get("unknown_handling") not in {"reject", "manual_review"}:
        errors.append("unknown_handling must be reject or manual_review")
    extensions = policy.get("extensions", {})
    if not isinstance(extensions, dict) or any(":" not in key for key in extensions):
        errors.append("extensions must use namespaced keys")
    return sorted(errors)


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _scope_matches(value: str, scopes: Any) -> bool:
    return isinstance(scopes, list) and ("*" in scopes or value in scopes)


def evaluate(
    envelope: dict[str, Any],
    policy: dict[str, Any],
    *,
    expected_subject: str | None = None,
    expected_contract: str | None = None,
    expected_environment: str | None = None,
    now: datetime | None = None,
) -> TrustEvaluation:
    """Apply trust only after cryptographic and binding verification."""

    errors = validate_policy(policy)
    if errors:
        raise MncsError("invalid trust policy: " + "; ".join(errors))
    key_records = policy["keys"]
    verification: AttestationVerification = verify_attestation(
        envelope,
        key_records,
        expected_subject=expected_subject,
        expected_contract=expected_contract,
        expected_environment=expected_environment,
        now=now,
    )
    reasons: list[str] = []
    statement = verification.statement or {}
    predicate_type = str(statement.get("predicate_type", ""))
    contract_id = str(statement.get("contract_id", ""))
    environment = str(statement.get("environment", ""))
    component = statement.get("component", {})
    component_name = str(component.get("name", "")) if isinstance(component, dict) else ""
    moment = now or datetime.now(UTC)
    revoked = {
        str(item.get("keyid"))
        for item in policy.get("revocations", [])
        if isinstance(item, dict) and (_parse_time(item.get("revoked_at")) or moment) <= moment
    }
    valid_keyids = {item.keyid for item in verification.signatures if item.cryptographically_valid}
    trusted_signers: list[str] = []
    roles: set[str] = set()
    generator_signers: set[str] = set()
    evaluator_signers: set[str] = set()
    for record in key_records:
        keyid = str(record["keyid"])
        if keyid not in valid_keyids:
            continue
        if record.get("trusted", True) is not True:
            reasons.append(f"cryptographically valid but untrusted key: {keyid}")
            continue
        if keyid in revoked:
            reasons.append(f"revoked key: {keyid}")
            continue
        valid_from = _parse_time(record.get("valid_from"))
        valid_until = _parse_time(record.get("valid_until"))
        if valid_from is not None and moment < valid_from:
            reasons.append(f"key is not yet valid: {keyid}")
            continue
        if valid_until is not None and moment >= valid_until:
            reasons.append(f"key expired: {keyid}")
            continue
        if not _scope_matches(predicate_type, record.get("predicate_types", ["*"])):
            reasons.append(f"predicate outside key scope: {keyid}")
            continue
        if not _scope_matches(contract_id, record.get("contracts", ["*"])):
            reasons.append(f"contract outside key scope: {keyid}")
            continue
        if not _scope_matches(component_name, record.get("components", ["*"])):
            reasons.append(f"component outside key scope: {keyid}")
            continue
        if not _scope_matches(environment, record.get("environments", ["*"])):
            reasons.append(f"environment outside key scope: {keyid}")
            continue
        trusted_signers.append(keyid)
        record_roles = {str(role) for role in record["roles"]}
        roles.update(record_roles)
        if "generator" in record_roles:
            generator_signers.add(keyid)
        if "evaluator" in record_roles:
            evaluator_signers.add(keyid)
    trusted_signers.sort()
    if predicate_type not in policy["allowed_predicate_types"]:
        reasons.append("predicate type is not allowed")
    if verification.expired:
        reasons.append("attestation expired")
    predicate = statement.get("predicate", {})
    status = predicate.get("status") if isinstance(predicate, dict) else None
    if status == "UNKNOWN":
        reasons.append(f"UNKNOWN handled as {policy['unknown_handling']}")
    minimum = int(policy["minimum_signatures"])
    distinct = int(policy["distinct_signers"])
    if len(trusted_signers) < minimum:
        reasons.append("insufficient trusted signatures")
    if len(set(trusted_signers)) < distinct:
        reasons.append("insufficient distinct trusted signers")
    missing_roles = sorted(set(policy.get("required_roles", [])) - roles)
    if missing_roles:
        reasons.append("missing required roles: " + ", ".join(missing_roles))
    if policy.get("require_generator_evaluator_separation", False):
        if not generator_signers or not evaluator_signers:
            reasons.append("generator/evaluator roles are incomplete")
        elif generator_signers & evaluator_signers:
            reasons.append("generator/evaluator signer separation failed")
    independent = int(policy.get("minimum_independent_evaluators", 0))
    if len(evaluator_signers) < independent:
        reasons.append("insufficient independent evaluators")
    crypto = verification.cryptographically_valid and not verification.expired
    trusted = crypto and not reasons
    certified = trusted and status == "PASS"
    if status == "UNKNOWN" and policy["unknown_handling"] == "manual_review":
        certified = False
    return TrustEvaluation(
        crypto,
        trusted,
        certified,
        trusted_signers,
        sorted(roles),
        sorted(set(reasons)),
        verification.as_dict(),
    )
