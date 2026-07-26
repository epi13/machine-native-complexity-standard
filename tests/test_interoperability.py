# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mncs_validator.attestation import attest, generate_key, load_public_record, verify_attestation
from mncs_validator.canonical import canonicalize_bytes
from mncs_validator.errors import MncsError
from mncs_validator.package import pack, unpack, verify_package
from mncs_validator.provider import inspect_provider, run_provider
from mncs_validator.trust import evaluate

ROOT = Path(__file__).resolve().parents[1]
PREDICATE = "https://mncs.dev/predicate/conformance-result/v0.2"


def test_canonical_json_rejects_duplicates_and_normalizes_numbers() -> None:
    assert canonicalize_bytes(b'{"z":-0.0,"a":"\xe2\x82\xac","n":1e+30}') == (
        b'{"a":"\xe2\x82\xac","n":1e+30,"z":0}'
    )
    with pytest.raises(MncsError, match="duplicate"):
        canonicalize_bytes(b'{"a":1,"a":2}')
    with pytest.raises(MncsError, match="nonfinite"):
        canonicalize_bytes(b'{"n":NaN}')


def _statement(now: datetime) -> dict[str, object]:
    return {
        "_type": "https://mncs.dev/attestation/v0.2/statement",
        "mncs_version": "0.2",
        "schema_version": "0.2",
        "subject": [{"name": "component", "digest": {"sha256": "a" * 64}}],
        "contract_id": "example.contract",
        "component": {
            "name": "component",
            "version": "1",
            "identity": f"sha256:{'a' * 64}",
        },
        "environment": f"sha256:{'b' * 64}",
        "predicate_type": PREDICATE,
        "predicate": {"status": "PASS"},
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "extensions": {},
    }


def test_signature_and_trust_are_separate_and_bind_subject(tmp_path: Path) -> None:
    private = tmp_path / "signer.pem"
    public = tmp_path / "signer.pub.json"
    generated = generate_key(private, public)
    assert private.stat().st_mode & 0o777 == 0o600
    now = datetime(2026, 1, 1, tzinfo=UTC)
    envelope = attest(_statement(now), private)
    record = load_public_record(public)
    crypto = verify_attestation(envelope, [record], expected_subject=f"sha256:{'a' * 64}", now=now)
    assert crypto.cryptographically_valid
    assert not verify_attestation(
        envelope,
        [record],
        expected_subject=f"sha256:{'c' * 64}",
        now=now,
    ).payload_valid
    policy = {
        "schema_version": "0.2",
        "trust_domain": "example",
        "keys": [
            {
                **record,
                "roles": ["evaluator"],
                "predicate_types": [PREDICATE],
                "components": ["component"],
                "contracts": ["example.contract"],
                "environments": [f"sha256:{'b' * 64}"],
            }
        ],
        "allowed_predicate_types": [PREDICATE],
        "minimum_signatures": 1,
        "distinct_signers": 1,
        "required_roles": ["evaluator"],
        "minimum_independent_evaluators": 1,
        "require_generator_evaluator_separation": False,
        "unknown_handling": "reject",
        "offline": True,
        "revocations": [],
        "extensions": {},
    }
    trusted = evaluate(
        envelope,
        policy,
        expected_subject=f"sha256:{'a' * 64}",
        expected_contract="example.contract",
        expected_environment=f"sha256:{'b' * 64}",
        now=now,
    )
    assert trusted.cryptographically_valid
    assert trusted.trusted
    assert trusted.certified
    policy["revocations"] = [
        {
            "keyid": generated["keyid"],
            "revoked_at": "2025-01-01T00:00:00Z",
            "reason": "test",
            "extensions": {},
        }
    ]
    revoked = evaluate(envelope, policy, now=now)
    assert revoked.cryptographically_valid
    assert not revoked.trusted
    assert any("revoked" in reason for reason in revoked.reasons)


def test_package_is_reproducible_and_safe(tmp_path: Path) -> None:
    first = tmp_path / "first.mncs"
    second = tmp_path / "second.mncs"
    pack(ROOT / "examples/minimal", first)
    pack(ROOT / "examples/minimal", second)
    assert first.read_bytes() == second.read_bytes()
    assert verify_package(first).valid
    extracted = tmp_path / "extracted"
    assert unpack(first, extracted).valid
    assert (extracted / "manifest.json").is_file()

    malicious = tmp_path / "traversal.mncs"
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../escape", b"bad")
    report = verify_package(malicious)
    assert not report.valid
    assert any("unsafe package path" in issue for issue in report.issues)


def test_provider_capabilities_are_explicit_and_bounded() -> None:
    result = inspect_provider(
        [sys.executable, str(ROOT / "examples/providers/pattern_provider.py")],
        timeout=10,
    )
    assert result["type"] == "capabilities"
    assert result["protocol_version"] == "0.1"


def test_provider_timeout_and_output_caps_cleanup() -> None:
    request = {
        "protocol_version": "0.1",
        "type": "health",
        "request_id": "bounded",
        "extensions": {},
    }
    with pytest.raises(MncsError, match="timed out"):
        run_provider(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            request,
            timeout=0.05,
        )
    with pytest.raises(MncsError, match="output exceeded"):
        run_provider(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * 5000000)"],
            request,
            timeout=5,
        )
