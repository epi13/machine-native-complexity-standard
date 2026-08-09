from __future__ import annotations

import copy
import json
import os
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from test_execution_receipt import _receipt

from mncs_validator.canonical import canonical_sha256
from mncs_validator.cli import main
from mncs_validator.execution_challenge import (
    ReplayStore,
    bind_challenge_to_receipt,
    issue_execution_challenge,
    validate_execution_challenge_value,
    validate_replay_receipt_value,
    verify_replay_receipt,
)
from mncs_validator.execution_receipt import validate_execution_receipt_value
from mncs_validator.schemas import load_schema, schema_errors

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 8, 0, 0, 10, tzinfo=UTC)


def _request(
    receipt: dict[str, object], *, request_id: str = "request.example-v1"
) -> dict[str, object]:
    subject = receipt["subject"]
    bundle = receipt["bundle"]
    policy = receipt["policy"]
    runner = receipt["runner"]
    assert isinstance(subject, dict)
    assert isinstance(bundle, dict)
    assert isinstance(policy, dict)
    assert isinstance(runner, dict)
    return {
        "schema_version": "0.1-experimental",
        "record_type": "mncs-execution-challenge-request",
        "request_id": request_id,
        "issuer_identity": "issuer.local.example-v1",
        "ttl_seconds": 60,
        "scope": {
            "subject_identity": subject["canonical_sha256"],
            "candidate_id": subject["candidate_id"],
            "bundle_identity": bundle["test_bundle_identity"],
            "execution_policy_identity": policy["execution_policy_identity"],
            "runner_identity": runner["runner_identity"],
        },
        "replay_policy": "single-use",
        "claim_boundary": {
            "freshness": "local-replay-scope-only",
            "authority": "not-asserted",
            "isolation": "not-asserted",
            "custody": "not-asserted",
            "independence": "not-asserted",
            "conformance": "not-asserted",
            "promotion": "not-asserted",
        },
        "extensions": {},
    }


def _chain(
    *, now: datetime = NOW, nonce: str = "N" * 43
) -> tuple[dict[str, object], dict[str, object]]:
    receipt = _receipt()
    request = _request(receipt)
    challenge_report = issue_execution_challenge(request, now=now, nonce_factory=lambda: nonce)
    assert challenge_report.valid, challenge_report.as_dict()
    challenge = challenge_report.challenge
    assert challenge is not None
    receipt_challenge = receipt["challenge"]
    assert isinstance(receipt_challenge, dict)
    receipt_challenge.update(
        {
            "nonce": challenge["nonce"],
            "issued_at": challenge["issued_at"],
            "expires_at": challenge["expires_at"],
        }
    )
    receipt["request"]["observed_at"] = challenge["issued_at"]  # type: ignore[index]
    receipt["lifecycle"]["started_at"] = challenge["issued_at"]  # type: ignore[index]
    receipt["lifecycle"]["ended_at"] = (
        (now + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    )  # type: ignore[index]
    receipt["receipt_identity"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_identity"}
    )
    assert validate_execution_receipt_value(receipt).valid
    return challenge, receipt


def test_schemas_are_packaged_and_challenge_identity_is_deterministic() -> None:
    assert (
        load_schema("execution-challenge")["properties"]["record_type"]["const"]
        == "mncs-execution-challenge"
    )
    assert (
        load_schema("execution-challenge-request")["properties"]["record_type"]["const"]
        == "mncs-execution-challenge-request"
    )
    assert (
        load_schema("replay-receipt")["properties"]["record_type"]["const"] == "mncs-replay-receipt"
    )
    challenge, _ = _chain()
    assert validate_execution_challenge_value(challenge).category == "PASS"
    assert (
        validate_execution_challenge_value(copy.deepcopy(challenge)).challenge_identity
        == challenge["challenge_identity"]
    )


def test_reference_request_and_adversarial_corpus_index() -> None:
    request_path = ROOT / "experimental/execution-challenge/fixtures/valid/reference-request.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert schema_errors(request, "execution-challenge-request") == []
    corpus = json.loads(
        (ROOT / "experimental/execution-challenge/fixtures/corpus-index.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(corpus["cases"]) >= 40
    assert {case["expected"] for case in corpus["cases"]} >= {
        "PASS",
        "INVALID",
        "UNSUPPORTED",
    }


def test_issuer_uses_secure_length_nonce_and_rejects_injected_short_nonce() -> None:
    receipt = _receipt()
    report = issue_execution_challenge(_request(receipt), now=NOW)
    assert report.valid and report.challenge is not None
    assert len(report.challenge["nonce"]) >= 43
    short = issue_execution_challenge(_request(receipt), now=NOW, nonce_factory=lambda: "short")
    assert not short.valid
    assert any(issue.code == "nonce-invalid" for issue in short.issues)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("nonce", "X" * 43),
        ("issued_at", "2026-08-08T00:00:11Z"),
        ("expires_at", "2026-08-08T00:02:00Z"),
        ("issuer_identity", "issuer.other-v1"),
    ],
)
def test_challenge_identity_changes_with_material_scope(field: str, value: str) -> None:
    challenge, _ = _chain()
    mutated = copy.deepcopy(challenge)
    mutated[field] = value
    mutated["challenge_identity"] = canonical_sha256(
        {key: child for key, child in mutated.items() if key != "challenge_identity"}
    )
    assert mutated["challenge_identity"] != challenge["challenge_identity"]
    assert validate_execution_challenge_value(mutated).valid


@pytest.mark.parametrize(
    "field",
    [
        "subject",
        "bundle",
        "policy",
        "runner",
    ],
)
def test_receipt_scope_substitution_fails_closed(field: str) -> None:
    challenge, receipt = _chain(now=datetime.now(UTC))
    mutated = copy.deepcopy(receipt)
    if field == "subject":
        mutated["subject"]["canonical_sha256"] = "9" * 64
    elif field == "bundle":
        mutated["bundle"]["test_bundle_identity"] = "9" * 64
    elif field == "policy":
        mutated["policy"]["execution_policy_identity"] = "9" * 64
    else:
        mutated["runner"]["runner_identity"] = "runner.other-v1"
    mutated["receipt_identity"] = canonical_sha256(
        {key: child for key, child in mutated.items() if key != "receipt_identity"}
    )
    report = bind_challenge_to_receipt(challenge, mutated)
    assert not report.valid
    assert any(issue.code == "challenge-scope-mismatch" for issue in report.issues)


def test_challenge_observation_substitution_and_missing_receipt_facts_fail() -> None:
    challenge, receipt = _chain()
    for key in ("nonce", "issued_at", "expires_at"):
        mutated = copy.deepcopy(receipt)
        mutated["challenge"][key] = (
            "Z" * 43
            if key == "nonce"
            else "2026-08-08T00:00:11Z"
            if key == "issued_at"
            else "2026-08-08T00:02:00Z"
        )
        mutated["receipt_identity"] = canonical_sha256(
            {name: child for name, child in mutated.items() if name != "receipt_identity"}
        )
        assert not bind_challenge_to_receipt(challenge, mutated).valid
    bad_challenge = copy.deepcopy(challenge)
    bad_challenge["challenge_identity"] = "0" * 64
    assert not bind_challenge_to_receipt(bad_challenge, receipt).valid


def test_expired_and_not_yet_valid_challenges_are_distinct_failures() -> None:
    challenge, _ = _chain()
    assert not validate_execution_challenge_value(challenge, at=NOW - timedelta(seconds=1)).valid
    assert not validate_execution_challenge_value(challenge, at=NOW + timedelta(seconds=61)).valid


def test_first_consume_is_single_use_and_survives_restart(tmp_path: Path) -> None:
    challenge, receipt = _chain()
    store_path = tmp_path / "replay-store"
    first = ReplayStore(store_path, clock=lambda: NOW + timedelta(seconds=2)).consume(
        challenge, receipt
    )
    assert first.valid and first.replay_receipt is not None
    second = ReplayStore(store_path, clock=lambda: NOW + timedelta(seconds=3)).consume(
        challenge, receipt
    )
    assert not second.valid
    assert any(issue.code == "challenge-replayed" for issue in second.issues)
    verified = verify_replay_receipt(
        first.replay_receipt, challenge, receipt, store=ReplayStore(store_path)
    )
    assert verified.valid, verified.as_dict()
    assert validate_replay_receipt_value(first.replay_receipt).valid


def test_duplicate_nonce_is_rejected_even_when_challenge_identity_differs(tmp_path: Path) -> None:
    first_challenge, first_receipt = _chain(nonce="Q" * 43)
    second_challenge, second_receipt = _chain(nonce="Q" * 43)
    first = ReplayStore(tmp_path / "store", clock=lambda: NOW + timedelta(seconds=2)).consume(
        first_challenge, first_receipt
    )
    assert first.valid
    second = ReplayStore(tmp_path / "store", clock=lambda: NOW + timedelta(seconds=3)).consume(
        second_challenge, second_receipt
    )
    assert not second.valid
    assert any(issue.code == "challenge-replayed" for issue in second.issues)


def test_watermark_prevents_wall_clock_rollback_and_forward_then_rollback(tmp_path: Path) -> None:
    first_challenge, first_receipt = _chain(now=NOW)
    clock = [NOW + timedelta(seconds=2)]
    store = ReplayStore(tmp_path / "store", clock=lambda: clock[0])
    first = store.consume(first_challenge, first_receipt)
    assert first.valid
    second_challenge, second_receipt = _chain(now=NOW + timedelta(seconds=1), nonce="R" * 43)
    clock[0] = NOW - timedelta(seconds=30)
    second = store.consume(second_challenge, second_receipt)
    assert second.valid
    assert second.replay_receipt["time_watermark"] >= first.replay_receipt["time_watermark"]  # type: ignore[index]
    third_challenge, third_receipt = _chain(now=NOW + timedelta(seconds=5), nonce="S" * 43)
    clock[0] = NOW + timedelta(seconds=120)
    expired = store.consume(third_challenge, third_receipt)
    assert not expired.valid
    clock[0] = NOW - timedelta(seconds=60)
    still_expired = store.consume(third_challenge, third_receipt)
    assert not still_expired.valid
    assert any(issue.code == "challenge-expired" for issue in still_expired.issues)


def test_concurrent_consumption_has_one_winner(tmp_path: Path) -> None:
    challenge, receipt = _chain(now=datetime.now(UTC))
    barrier = threading.Barrier(2)
    results: list[bool] = []

    def consume() -> None:
        barrier.wait()
        result = ReplayStore(
            tmp_path / "store", clock=lambda: datetime.now(UTC) + timedelta(seconds=2)
        ).consume(challenge, receipt)
        results.append(result.valid)

    workers = [threading.Thread(target=consume) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert sorted(results) == [False, True]


def test_corruption_truncation_hash_chain_future_and_missing_entry_fail(tmp_path: Path) -> None:
    challenge, receipt = _chain()
    store_path = tmp_path / "store"
    result = ReplayStore(store_path, clock=lambda: NOW + timedelta(seconds=2)).consume(
        challenge, receipt
    )
    assert result.valid and result.replay_receipt is not None
    ledger = store_path / "ledger.jsonl"
    original = ledger.read_bytes()
    ledger.write_bytes(original[:-1])
    corrupt = ReplayStore(store_path, clock=lambda: NOW + timedelta(seconds=3)).consume(
        *_chain(nonce="T" * 43)
    )
    assert not corrupt.valid
    ledger.write_bytes(original)
    entry = json.loads(ledger.read_text().splitlines()[0])
    entry["previous_entry_identity"] = "8" * 64
    ledger.write_text(json.dumps(entry) + "\n")
    assert not verify_replay_receipt(
        result.replay_receipt, challenge, receipt, store=ReplayStore(store_path)
    ).valid
    ledger.write_bytes(original)
    replay = copy.deepcopy(result.replay_receipt)
    replay["store_entry_identity"] = "7" * 64
    replay["replay_identity"] = canonical_sha256(
        {key: child for key, child in replay.items() if key != "replay_identity"}
    )
    assert not verify_replay_receipt(
        replay, challenge, receipt, store=ReplayStore(store_path)
    ).valid


def test_missing_state_stale_lock_and_interrupted_temporary_write_are_bounded(
    tmp_path: Path,
) -> None:
    challenge, receipt = _chain()
    store_path = tmp_path / "store"
    store = ReplayStore(store_path, clock=lambda: NOW + timedelta(seconds=2))
    first = store.consume(challenge, receipt)
    assert first.valid
    state = store_path / "state.json"
    state.unlink()
    assert not verify_replay_receipt(
        first.replay_receipt,
        challenge,
        receipt,
        store=ReplayStore(store_path),  # type: ignore[arg-type]
    ).valid

    second_challenge, second_receipt = _chain(nonce="U" * 43)
    (store_path / ".ledger.999.tmp").write_text("partial", encoding="utf-8")
    blocked = ReplayStore(store_path, clock=lambda: NOW + timedelta(seconds=3)).consume(
        second_challenge, second_receipt
    )
    assert not blocked.valid
    (store_path / ".ledger.999.tmp").unlink()
    state.write_text(
        json.dumps(
            {
                "schema_version": "0.1-experimental",
                "record_type": "mncs-replay-state",
                "time_watermark": "2026-08-08T00:00:12Z",
            }
        ),
        encoding="utf-8",
    )
    lock = store_path / ".lock"
    lock.write_text("stale", encoding="utf-8")
    old = (NOW - timedelta(seconds=120)).timestamp()
    os.utime(lock, (old, old))
    recovered = ReplayStore(
        store_path, clock=lambda: NOW + timedelta(seconds=3), lock_timeout=0.1
    ).consume(second_challenge, second_receipt)
    assert recovered.valid


def test_future_challenge_schema_is_unsupported_and_authority_overclaim_fails() -> None:
    challenge, _ = _chain()
    future = copy.deepcopy(challenge)
    future["schema_version"] = "0.2-experimental"
    assert validate_execution_challenge_value(future).category == "UNSUPPORTED"
    overclaim = copy.deepcopy(challenge)
    overclaim["claim_boundary"]["authority"] = "established"
    overclaim["challenge_identity"] = canonical_sha256(
        {key: child for key, child in overclaim.items() if key != "challenge_identity"}
    )
    assert not validate_execution_challenge_value(overclaim).valid


def test_offline_replay_receipt_does_not_require_mutation_or_external_authority(
    tmp_path: Path,
) -> None:
    challenge, receipt = _chain()
    store = ReplayStore(tmp_path / "store", clock=lambda: NOW + timedelta(seconds=2))
    consumed = store.consume(challenge, receipt)
    assert consumed.valid and consumed.replay_receipt is not None
    offline = verify_replay_receipt(consumed.replay_receipt, challenge, receipt)
    assert offline.valid
    assert "external custody" not in json.dumps(offline.replay_receipt).lower()
    assert any("local store" in limitation for limitation in consumed.replay_receipt["limitations"])
    mutated = copy.deepcopy(consumed.replay_receipt)
    mutated["store_sequence"] = 2
    mutated["replay_identity"] = canonical_sha256(
        {key: child for key, child in mutated.items() if key != "replay_identity"}
    )
    assert not verify_replay_receipt(mutated, challenge, receipt).valid


def test_cli_issue_validate_consume_and_verify(tmp_path: Path, capsys: object) -> None:
    challenge, receipt = _chain(now=datetime.now(UTC))
    request_path = tmp_path / "request.json"
    challenge_path = tmp_path / "challenge.json"
    receipt_path = tmp_path / "receipt.json"
    replay_path = tmp_path / "replay.json"
    request_path.write_text(json.dumps(_request(receipt)), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    # The CLI's secure issuer is checked separately; the fixed chain is used for the
    # deterministic consume/verify portion of this test.
    assert (
        main(["challenge", "issue", str(request_path), "--output", str(challenge_path), "--json"])
        == 0
    )
    assert challenge_path.is_file()
    capsys.readouterr()  # type: ignore[attr-defined]
    challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
    assert main(["challenge", "validate", str(challenge_path), "--json"]) == 0
    capsys.readouterr()  # type: ignore[attr-defined]
    assert (
        main(
            [
                "replay",
                "consume",
                str(challenge_path),
                str(receipt_path),
                "--store",
                str(tmp_path / "store"),
                "--output",
                str(replay_path),
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()  # type: ignore[attr-defined]
    assert (
        main(
            [
                "replay",
                "verify",
                str(replay_path),
                "--challenge",
                str(challenge_path),
                "--receipt",
                str(receipt_path),
                "--json",
            ]
        )
        == 0
    )
