"""Offline Ed25519 DSSE-compatible attestations."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import canonicalize, parse_json_bytes
from .errors import MncsError
from .hashing import read_regular_file

PAYLOAD_TYPE = "application/vnd.mncs.attestation-statement.v0.2+json"
ALGORITHM = "ed25519"


@dataclass(frozen=True)
class SignatureResult:
    keyid: str
    cryptographically_valid: bool
    reason: str


@dataclass(frozen=True)
class AttestationVerification:
    payload_valid: bool
    expired: bool
    signatures: list[SignatureResult]
    statement: dict[str, Any] | None

    @property
    def cryptographically_valid(self) -> bool:
        return self.payload_valid and any(item.cryptographically_valid for item in self.signatures)

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["cryptographically_valid"] = self.cryptographically_valid
        return value


def _key_id(raw_public_key: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw_public_key).hexdigest()}"


def _public_record(public_key: Ed25519PublicKey) -> dict[str, Any]:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        "schema_version": "0.2",
        "algorithm": ALGORITHM,
        "keyid": _key_id(raw),
        "public_key": base64.b64encode(raw).decode("ascii"),
        "extensions": {},
    }


def generate_key(private_path: Path, public_path: Path | None = None) -> dict[str, Any]:
    """Create a private key only at an explicit new path and write its public record."""

    if private_path.exists():
        raise MncsError(f"refusing to overwrite private key: {private_path}")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(private_path, flags, 0o600)
    try:
        os.write(descriptor, pem)
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)
    record = _public_record(key.public_key())
    output = public_path or private_path.with_suffix(private_path.suffix + ".pub.json")
    if output.exists():
        private_path.unlink()
        raise MncsError(f"refusing to overwrite public key record: {output}")
    output.write_bytes(canonicalize(record) + b"\n")
    return {"private_key": str(private_path), "public_key": str(output), **record}


def load_public_record(path: Path) -> dict[str, Any]:
    value = parse_json_bytes(read_regular_file(path))
    if not isinstance(value, dict):
        raise MncsError("public key record must be an object")
    if value.get("algorithm") != ALGORITHM:
        raise MncsError("unsupported key algorithm")
    raw = base64.b64decode(str(value.get("public_key", "")), validate=True)
    if len(raw) != 32 or value.get("keyid") != _key_id(raw):
        raise MncsError("public key record has an invalid or colliding key ID")
    return value


def inspect_key(path: Path) -> dict[str, Any]:
    """Inspect either a public record or an Ed25519 private key without exposing it."""

    content = read_regular_file(path)
    if content.startswith(b"-----BEGIN PRIVATE KEY-----"):
        key = serialization.load_pem_private_key(content, password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise MncsError("private key is not Ed25519")
        return {"private": True, **_public_record(key.public_key())}
    return {"private": False, **load_public_record(path)}


def _load_private(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(read_regular_file(path), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise MncsError("private key is not Ed25519")
    return key


def _pae(payload_type: str, payload: bytes) -> bytes:
    type_bytes = payload_type.encode("utf-8")
    return (
        b"DSSEv1 "
        + str(len(type_bytes)).encode("ascii")
        + b" "
        + type_bytes
        + b" "
        + str(len(payload)).encode("ascii")
        + b" "
        + payload
    )


def create_statement(
    *,
    subjects: list[dict[str, Any]],
    contract_id: str,
    component: dict[str, Any],
    environment: str,
    predicate_type: str,
    predicate: dict[str, Any],
    created_at: str,
    expires_at: str | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    statement: dict[str, Any] = {
        "_type": "https://mncs.dev/attestation/v0.2/statement",
        "mncs_version": "0.2",
        "schema_version": "0.2",
        "subject": subjects,
        "contract_id": contract_id,
        "component": component,
        "environment": environment,
        "predicate_type": predicate_type,
        "predicate": predicate,
        "created_at": created_at,
        "extensions": extensions or {},
    }
    if expires_at is not None:
        statement["expires_at"] = expires_at
    return statement


def attest(
    statement: dict[str, Any], private_path: Path, envelope: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Sign canonical statement bytes and append a unique signature."""

    key = _load_private(private_path)
    record = _public_record(key.public_key())
    payload = canonicalize(statement)
    encoded_payload = base64.b64encode(payload).decode("ascii")
    result = envelope or {"payloadType": PAYLOAD_TYPE, "payload": encoded_payload, "signatures": []}
    if result.get("payloadType") != PAYLOAD_TYPE or result.get("payload") != encoded_payload:
        raise MncsError("existing envelope payload does not match the statement")
    signatures = result.get("signatures")
    if not isinstance(signatures, list):
        raise MncsError("envelope signatures must be an array")
    if any(isinstance(item, dict) and item.get("keyid") == record["keyid"] for item in signatures):
        raise MncsError(f"duplicate signature from {record['keyid']}")
    signature = key.sign(_pae(PAYLOAD_TYPE, payload))
    signatures.append(
        {
            "keyid": record["keyid"],
            "algorithm": ALGORITHM,
            "sig": base64.b64encode(signature).decode("ascii"),
        }
    )
    return result


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def verify_attestation(
    envelope: dict[str, Any],
    keys: list[dict[str, Any]],
    *,
    expected_subject: str | None = None,
    expected_contract: str | None = None,
    expected_environment: str | None = None,
    now: datetime | None = None,
) -> AttestationVerification:
    """Verify DSSE signatures and bindings without applying trust policy."""

    payload_valid = envelope.get("payloadType") == PAYLOAD_TYPE
    try:
        payload = base64.b64decode(str(envelope.get("payload", "")), validate=True)
        statement_value = parse_json_bytes(payload)
        statement = statement_value if isinstance(statement_value, dict) else None
        payload_valid = (
            payload_valid and statement is not None and canonicalize(statement) == payload
        )
    except (ValueError, MncsError):
        payload = b""
        statement = None
        payload_valid = False
    expired = False
    if statement is not None:
        expires = _parse_time(statement.get("expires_at"))
        expired = expires is not None and (now or datetime.now(UTC)) >= expires
        subjects = statement.get("subject", [])
        subject_hashes = {
            digest
            for item in subjects
            if isinstance(item, dict)
            for digest in [item.get("digest", {}).get("sha256")]
            if isinstance(digest, str)
        }
        if (
            expected_subject is not None
            and expected_subject.removeprefix("sha256:") not in subject_hashes
        ):
            payload_valid = False
        if expected_contract is not None and statement.get("contract_id") != expected_contract:
            payload_valid = False
        if (
            expected_environment is not None
            and statement.get("environment") != expected_environment
        ):
            payload_valid = False
    key_map = {str(item.get("keyid")): item for item in keys}
    seen: set[str] = set()
    results: list[SignatureResult] = []
    signatures = envelope.get("signatures", [])
    if not isinstance(signatures, list):
        signatures = []
        payload_valid = False
    for item in signatures:
        if not isinstance(item, dict):
            results.append(SignatureResult("", False, "malformed signature"))
            continue
        keyid = str(item.get("keyid", ""))
        if keyid in seen:
            results.append(SignatureResult(keyid, False, "duplicate signature"))
            payload_valid = False
            continue
        seen.add(keyid)
        record = key_map.get(keyid)
        if record is None:
            results.append(SignatureResult(keyid, False, "public key unavailable"))
            continue
        try:
            if item.get("algorithm") != ALGORITHM:
                raise ValueError("algorithm confusion")
            raw = base64.b64decode(str(record["public_key"]), validate=True)
            if _key_id(raw) != keyid:
                raise ValueError("key ID mismatch")
            signature = base64.b64decode(str(item["sig"]), validate=True)
            Ed25519PublicKey.from_public_bytes(raw).verify(
                signature,
                _pae(PAYLOAD_TYPE, payload),
            )
        except (InvalidSignature, KeyError, ValueError):
            results.append(SignatureResult(keyid, False, "invalid signature"))
        else:
            results.append(SignatureResult(keyid, True, "valid signature"))
    return AttestationVerification(payload_valid, expired, results, statement)


def load_json(path: Path) -> dict[str, Any]:
    value = parse_json_bytes(read_regular_file(path))
    if not isinstance(value, dict):
        raise MncsError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes(canonicalize(value) + b"\n")
