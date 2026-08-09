"""Experimental verifier-issued execution challenges and local replay evidence.

Challenges bind a fresh, single-use nonce to an execution scope.  The replay
store only detects reuse within its declared local trust boundary; it is not a
custody system, an attestation authority, a sandbox, or a conformance oracle.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import secrets
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic, sleep
from typing import Any, cast

from .canonical import canonical_sha256, canonicalize, parse_json_bytes
from .execution_receipt import validate_execution_receipt_value
from .hashing import read_regular_file, sha256_bytes
from .schemas import schema_errors
from .validation import load_json_object

SCHEMA_NAME = "execution-challenge-0.1-experimental"
REQUEST_SCHEMA_NAME = "execution-challenge-request-0.1-experimental"
REPLAY_SCHEMA_NAME = "replay-receipt-0.1-experimental"
SCHEMA_VERSION = "0.1-experimental"
MAX_LEDGER_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 100_000
DEFAULT_LOCK_TIMEOUT = 30.0
_LIMITATIONS = [
    "Replay detection is limited to the declared local store.",
    "A host administrator can replace or delete the local replay store.",
    "Freshness does not establish correctness, isolation, custody, independence, "
    "conformance, or promotion.",
]


@dataclass(frozen=True)
class ExecutionChallengeIssue:
    code: str
    message: str
    path: str = ""


@dataclass
class ExecutionChallengeReport:
    target: str
    valid: bool = True
    supported: bool = True
    status: str = "PASS"
    challenge_identity: str | None = None
    challenge: dict[str, Any] | None = None
    issues: list[ExecutionChallengeIssue] = field(default_factory=list)
    warnings: list[ExecutionChallengeIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.status

    def invalidate(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.status = "FAIL"
        self.issues.append(ExecutionChallengeIssue(code, message, path))

    def unknown(self, code: str, message: str, path: str = "") -> None:
        if self.status != "FAIL":
            self.status = "UNKNOWN"
        self.warnings.append(ExecutionChallengeIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


@dataclass
class ReplayReport:
    target: str
    valid: bool = True
    supported: bool = True
    status: str = "PASS"
    replay_identity: str | None = None
    replay_receipt: dict[str, Any] | None = None
    issues: list[ExecutionChallengeIssue] = field(default_factory=list)
    warnings: list[ExecutionChallengeIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.status

    def invalidate(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.status = "FAIL"
        self.issues.append(ExecutionChallengeIssue(code, message, path))

    def unknown(self, code: str, message: str, path: str = "") -> None:
        if self.status != "FAIL":
            self.status = "UNKNOWN"
        self.warnings.append(ExecutionChallengeIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include an RFC 3339 UTC offset")
    return parsed.astimezone(UTC)


def _format_time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _identity_without(value: dict[str, Any], key: str) -> str:
    material = deepcopy(value)
    material.pop(key, None)
    return canonical_sha256(material)


def _scope_from_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    subject = cast(dict[str, Any], receipt["subject"])
    bundle = cast(dict[str, Any], receipt["bundle"])
    policy = cast(dict[str, Any], receipt["policy"])
    runner = cast(dict[str, Any], receipt["runner"])
    return {
        "subject_identity": subject["canonical_sha256"],
        "candidate_id": subject["candidate_id"],
        "bundle_identity": bundle["test_bundle_identity"],
        "execution_policy_identity": policy["execution_policy_identity"],
        "runner_identity": runner["runner_identity"],
    }


def _check_schema(
    value: dict[str, Any], schema: str, report: ExecutionChallengeReport | ReplayReport
) -> bool:
    errors = schema_errors(value, schema)
    for error in errors:
        report.invalidate("schema", error)
    return not errors


def _validate_challenge_semantics(
    value: dict[str, Any], report: ExecutionChallengeReport, *, at: datetime | None = None
) -> None:
    if value.get("challenge_identity") != _identity_without(value, "challenge_identity"):
        report.invalidate(
            "challenge-identity-mismatch",
            "challenge_identity is not the canonical SHA-256 of the challenge "
            "without challenge_identity",
            "$/challenge_identity",
        )
    try:
        issued = _time(cast(str, value["issued_at"]))
        expires = _time(cast(str, value["expires_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        report.invalidate("timestamp-invalid", str(exc), "$/challenge")
        return
    if expires <= issued:
        report.invalidate(
            "challenge-window-invalid", "expires_at must be later than issued_at", "$/expires_at"
        )
    if at is not None:
        current = at.astimezone(UTC) if at.tzinfo is not None else at
        if current < issued:
            report.invalidate(
                "challenge-not-yet-valid",
                "verification time precedes challenge issuance",
                "$/issued_at",
            )
        elif current >= expires:
            report.invalidate(
                "challenge-expired", "challenge is expired at verification time", "$/expires_at"
            )


def validate_execution_challenge_value(
    value: dict[str, Any], *, target: str = "<memory>", at: datetime | None = None
) -> ExecutionChallengeReport:
    """Validate one challenge without mutating a replay store."""

    report = ExecutionChallengeReport(target=target)
    if value.get("schema_version") != SCHEMA_VERSION:
        report.supported = False
        report.status = "UNKNOWN"
        report.warnings.append(
            ExecutionChallengeIssue(
                "unsupported-schema-version",
                f"unsupported execution-challenge schema version: {value.get('schema_version')!r}",
                "$/schema_version",
            )
        )
        return report
    if not _check_schema(value, SCHEMA_NAME, report):
        return report
    report.challenge = deepcopy(value)
    report.challenge_identity = cast(str, value["challenge_identity"])
    _validate_challenge_semantics(value, report, at=at)
    return report


def validate_execution_challenge_file(
    path: Path, *, at: datetime | None = None
) -> ExecutionChallengeReport:
    return validate_execution_challenge_value(load_json_object(path), target=str(path), at=at)


def issue_execution_challenge(
    request: dict[str, Any],
    *,
    now: datetime | None = None,
    nonce_factory: Callable[[], str] | None = None,
) -> ExecutionChallengeReport:
    """Issue a fresh challenge from a strictly scoped request.

    Production callers use ``secrets.token_urlsafe``.  ``nonce_factory`` exists
    only for deterministic tests and must still return a schema-valid nonce.
    """

    report = ExecutionChallengeReport(target="<issued>")
    if request.get("schema_version") != SCHEMA_VERSION:
        report.supported = False
        report.status = "UNKNOWN"
        report.warnings.append(
            ExecutionChallengeIssue(
                "unsupported-schema-version",
                "unsupported challenge request version",
                "$/schema_version",
            )
        )
        return report
    if not _check_schema(request, REQUEST_SCHEMA_NAME, report):
        return report
    issued = now or datetime.now(UTC)
    if issued.tzinfo is None or issued.utcoffset() is None:
        report.invalidate("timestamp-invalid", "issuer time must be timezone-aware", "$/issued_at")
        return report
    nonce = (nonce_factory or (lambda: secrets.token_urlsafe(32)))()
    if not isinstance(nonce, str) or len(nonce) < 43 or len(nonce) > 128:
        report.invalidate(
            "nonce-invalid", "nonce must contain at least 256 bits of generated entropy", "$/nonce"
        )
        return report
    challenge: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "mncs-execution-challenge",
        "challenge_id": f"challenge.{canonical_sha256(request)[:24]}.{nonce[:12]}",
        "challenge_identity": "0" * 64,
        "issuer_identity": request["issuer_identity"],
        "issued_at": _format_time(issued),
        "expires_at": _format_time(issued + timedelta(seconds=float(request["ttl_seconds"]))),
        "nonce": nonce,
        "scope": deepcopy(request["scope"]),
        "replay_policy": "single-use",
        "claim_boundary": deepcopy(request["claim_boundary"]),
        "extensions": deepcopy(request["extensions"]),
    }
    challenge["challenge_identity"] = _identity_without(challenge, "challenge_identity")
    issued_report = validate_execution_challenge_value(challenge, target="<issued>")
    if not issued_report.valid:
        return issued_report
    issued_report.challenge = challenge
    issued_report.challenge_identity = challenge["challenge_identity"]
    return issued_report


def _append_issues(target: ReplayReport, source: ExecutionChallengeReport | ReplayReport) -> None:
    for issue in source.issues:
        target.invalidate(issue.code, issue.message, issue.path)
    for warning in source.warnings:
        target.unknown(warning.code, warning.message, warning.path)


def bind_challenge_to_receipt(
    challenge: dict[str, Any], receipt: dict[str, Any], *, target: str = "<binding>"
) -> ReplayReport:
    """Require exact challenge scope and challenge observations in a receipt."""

    report = ReplayReport(target=target)
    challenge_report = validate_execution_challenge_value(challenge, target=f"{target}:challenge")
    if not challenge_report.valid:
        _append_issues(report, challenge_report)
        return report
    receipt_report = validate_execution_receipt_value(receipt, target=f"{target}:receipt")
    if not receipt_report.valid:
        report.invalidate(
            "receipt-invalid", "execution receipt is not structurally valid", "$/receipt"
        )
        return report
    receipt_challenge = cast(dict[str, Any], receipt["challenge"])
    for key in ("nonce", "issued_at", "expires_at"):
        if receipt_challenge.get(key) != challenge.get(key):
            report.invalidate(
                "challenge-receipt-mismatch",
                f"receipt challenge {key} does not match the issued challenge",
                f"$/challenge/{key}",
            )
    actual_scope = _scope_from_receipt(receipt)
    expected_scope = cast(dict[str, Any], challenge["scope"])
    for key, expected in expected_scope.items():
        if key == "runner_identity" and expected is None:
            continue
        if actual_scope.get(key) != expected:
            report.invalidate(
                "challenge-scope-mismatch",
                f"receipt scope {key} does not match the challenge",
                f"$/scope/{key}",
            )
    return report


class _ReplayStoreError(ValueError):
    pass


class ReplayStore:
    """A bounded, crash-safe, append-by-replacement local replay ledger."""

    def __init__(
        self,
        root: Path,
        *,
        clock: Callable[[], datetime] | None = None,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
    ) -> None:
        self.root = root
        self.clock = clock or (lambda: datetime.now(UTC))
        self.lock_timeout = lock_timeout
        self.ledger = root / "ledger.jsonl"
        self.state = root / "state.json"
        self.lockfile = root / ".lock"

    @contextmanager
    def _lock(self) -> Iterator[None]:
        if self.root.exists() and self.root.is_symlink():
            raise _ReplayStoreError("replay store root may not be a symlink")
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise _ReplayStoreError("replay store root is not a directory")
        descriptor: int | None = None
        deadline = monotonic() + self.lock_timeout
        try:
            while descriptor is None:
                try:
                    descriptor = os.open(
                        self.lockfile,
                        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                        0o600,
                    )
                    os.write(descriptor, f"pid={os.getpid()}\n".encode())
                except FileExistsError:
                    try:
                        age = time.time() - self.lockfile.stat().st_mtime
                    except FileNotFoundError:
                        continue
                    if age > self.lock_timeout:
                        self.lockfile.unlink(missing_ok=True)
                        continue
                    if monotonic() >= deadline:
                        raise _ReplayStoreError("timed out waiting for replay store lock") from None
                    sleep(0.01)
            yield
        finally:
            if descriptor is not None:
                os.close(descriptor)
                self.lockfile.unlink(missing_ok=True)

    def _read_entries(self) -> list[dict[str, Any]]:
        state_watermark = self._read_state()
        if not self.ledger.exists():
            return []
        if self.ledger.is_symlink():
            raise _ReplayStoreError("replay ledger may not be a symlink")
        try:
            content = read_regular_file(self.ledger, max_bytes=MAX_LEDGER_BYTES)
        except (OSError, ValueError) as exc:
            raise _ReplayStoreError(f"cannot read replay ledger: {exc}") from exc
        if not content:
            return []
        if not content.endswith(b"\n"):
            raise _ReplayStoreError("replay ledger has a truncated final line")
        entries: list[dict[str, Any]] = []
        previous: str | None = None
        watermark: datetime | None = None
        seen_challenges: set[str] = set()
        seen_nonces: set[str] = set()
        for line_number, line in enumerate(content.splitlines(), start=1):
            try:
                entry = parse_json_bytes(line)
            except ValueError as exc:
                raise _ReplayStoreError(f"corrupt replay ledger line {line_number}: {exc}") from exc
            required = {
                "schema_version",
                "record_type",
                "sequence",
                "entry_identity",
                "challenge_identity",
                "nonce_digest",
                "receipt_identity",
                "scope",
                "consumed_at",
                "previous_entry_identity",
                "time_watermark",
            }
            if set(entry) != required:
                raise _ReplayStoreError(
                    f"corrupt replay ledger line {line_number}: entry fields differ"
                )
            if (
                entry["schema_version"] != SCHEMA_VERSION
                or entry["record_type"] != "mncs-replay-entry"
            ):
                raise _ReplayStoreError(f"unsupported replay ledger entry at line {line_number}")
            if entry["entry_identity"] != _identity_without(entry, "entry_identity"):
                raise _ReplayStoreError(f"replay entry identity mismatch at line {line_number}")
            if entry["sequence"] != line_number or entry["previous_entry_identity"] != previous:
                raise _ReplayStoreError(f"replay sequence chain mismatch at line {line_number}")
            try:
                consumed = _time(cast(str, entry["consumed_at"]))
                entry_watermark = _time(cast(str, entry["time_watermark"]))
            except (TypeError, ValueError) as exc:
                raise _ReplayStoreError(
                    f"invalid replay timestamp at line {line_number}: {exc}"
                ) from exc
            if entry_watermark < consumed or (
                watermark is not None and entry_watermark < watermark
            ):
                raise _ReplayStoreError(f"replay time watermark rolled back at line {line_number}")
            challenge_identity = cast(str, entry["challenge_identity"])
            if challenge_identity in seen_challenges:
                raise _ReplayStoreError("replay ledger contains a duplicate challenge")
            nonce_digest = entry["nonce_digest"]
            if (
                not isinstance(nonce_digest, str)
                or len(nonce_digest) != 64
                or any(character not in "0123456789abcdef" for character in nonce_digest)
            ):
                raise _ReplayStoreError("replay ledger contains an invalid nonce digest")
            if nonce_digest in seen_nonces:
                raise _ReplayStoreError("replay ledger contains a duplicate nonce")
            seen_challenges.add(challenge_identity)
            seen_nonces.add(nonce_digest)
            entries.append(entry)
            previous = cast(str, entry["entry_identity"])
            watermark = entry_watermark
            if len(entries) > MAX_ENTRIES:
                raise _ReplayStoreError("replay ledger exceeds the bounded entry limit")
        if entries and state_watermark is None:
            raise _ReplayStoreError("replay store state is missing")
        if entries and state_watermark < watermark:  # type: ignore[operator]
            raise _ReplayStoreError("replay store state watermark rolled back")
        return entries

    def _read_state(self) -> datetime | None:
        if not self.state.exists():
            return None
        if self.state.is_symlink():
            raise _ReplayStoreError("replay store state may not be a symlink")
        try:
            value = parse_json_bytes(read_regular_file(self.state, max_bytes=4096))
        except (OSError, ValueError) as exc:
            raise _ReplayStoreError(f"cannot read replay store state: {exc}") from exc
        if set(value) != {"schema_version", "record_type", "time_watermark"}:
            raise _ReplayStoreError("replay store state fields differ")
        if value["schema_version"] != SCHEMA_VERSION or value["record_type"] != "mncs-replay-state":
            raise _ReplayStoreError("unsupported replay store state")
        try:
            return _time(cast(str, value["time_watermark"]))
        except (TypeError, ValueError) as exc:
            raise _ReplayStoreError(f"invalid replay store watermark: {exc}") from exc

    def _write_entries(self, entries: list[dict[str, Any]]) -> None:
        temporary = self.root / f".ledger.{os.getpid()}.tmp"
        if temporary.exists() or temporary.is_symlink():
            raise _ReplayStoreError("replay ledger temporary file already exists")
        payload = b"".join(canonicalize(entry) + b"\n" for entry in entries)
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            offset = 0
            while offset < len(payload):
                offset += os.write(descriptor, payload[offset:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, self.ledger)
        try:
            directory = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass

    def _write_state(self, watermark: datetime) -> None:
        temporary = self.root / f".state.{os.getpid()}.tmp"
        if temporary.exists() or temporary.is_symlink():
            raise _ReplayStoreError("replay state temporary file already exists")
        value = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "mncs-replay-state",
            "time_watermark": _format_time(watermark),
        }
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            payload = canonicalize(value) + b"\n"
            offset = 0
            while offset < len(payload):
                offset += os.write(descriptor, payload[offset:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, self.state)

    def consume(
        self,
        challenge: dict[str, Any],
        receipt: dict[str, Any],
        *,
        target: str = "<replay-consume>",
    ) -> ReplayReport:
        """Consume a challenge exactly once and emit portable replay evidence."""

        report = ReplayReport(target=target)
        binding = bind_challenge_to_receipt(challenge, receipt, target=target)
        if not binding.valid:
            report.issues.extend(binding.issues)
            report.status = "FAIL"
            report.valid = False
            return report
        challenge_identity = cast(str, challenge["challenge_identity"])
        try:
            with self._lock():
                entries = self._read_entries()
                previous = entries[-1] if entries else None
                prior_watermark = _time(cast(str, previous["time_watermark"])) if previous else None
                state_watermark = self._read_state()
                if state_watermark is not None and (
                    prior_watermark is None or state_watermark > prior_watermark
                ):
                    prior_watermark = state_watermark
                current = self.clock()
                if current.tzinfo is None or current.utcoffset() is None:
                    raise _ReplayStoreError("replay verification clock must be timezone-aware")
                effective = current.astimezone(UTC)
                if prior_watermark is not None and effective < prior_watermark:
                    effective = prior_watermark
                if prior_watermark is None or effective > prior_watermark:
                    self._write_state(effective)
                issued = _time(cast(str, challenge["issued_at"]))
                expires = _time(cast(str, challenge["expires_at"]))
                if effective < issued:
                    report.invalidate(
                        "challenge-not-yet-valid",
                        "effective store time precedes challenge issuance",
                        "$/issued_at",
                    )
                    return report
                if effective >= expires:
                    report.invalidate(
                        "challenge-expired",
                        "effective store time is at or after challenge expiry",
                        "$/expires_at",
                    )
                    return report
                nonce_digest = sha256_bytes(cast(str, challenge["nonce"]).encode()).removeprefix(
                    "sha256:"
                )
                if any(
                    entry["challenge_identity"] == challenge_identity
                    or entry["nonce_digest"] == nonce_digest
                    for entry in entries
                ):
                    report.invalidate(
                        "challenge-replayed",
                        "challenge has already been consumed in this local store",
                        "$/challenge_identity",
                    )
                    return report
                sequence = len(entries) + 1
                previous_identity = cast(str, previous["entry_identity"]) if previous else None
                entry: dict[str, Any] = {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "mncs-replay-entry",
                    "sequence": sequence,
                    "entry_identity": "0" * 64,
                    "challenge_identity": challenge_identity,
                    "nonce_digest": nonce_digest,
                    "receipt_identity": receipt["receipt_identity"],
                    "scope": deepcopy(challenge["scope"]),
                    "consumed_at": _format_time(effective),
                    "previous_entry_identity": previous_identity,
                    "time_watermark": _format_time(effective),
                }
                entry["entry_identity"] = _identity_without(entry, "entry_identity")
                new_entries = [*entries, entry]
                self._write_entries(new_entries)
                self._write_state(effective)
        except _ReplayStoreError as exc:
            report.invalidate("replay-store-invalid", str(exc), str(self.root))
            return report
        replay: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "mncs-replay-receipt",
            "replay_id": f"replay.{entry['entry_identity'][:32]}",
            "replay_identity": "0" * 64,
            "challenge_identity": challenge_identity,
            "receipt_identity": receipt["receipt_identity"],
            "scope": deepcopy(challenge["scope"]),
            "consumed_at": entry["consumed_at"],
            "store_entry_identity": entry["entry_identity"],
            "previous_entry_identity": entry["previous_entry_identity"],
            "store_head_identity": entry["entry_identity"],
            "time_watermark": entry["time_watermark"],
            "limitations": list(_LIMITATIONS),
            "extensions": {},
        }
        replay["replay_identity"] = _identity_without(replay, "replay_identity")
        report.replay_receipt = replay
        report.replay_identity = replay["replay_identity"]
        return report


def validate_replay_receipt_value(
    value: dict[str, Any], *, target: str = "<memory>"
) -> ReplayReport:
    report = ReplayReport(target=target)
    if value.get("schema_version") != SCHEMA_VERSION:
        report.supported = False
        report.status = "UNKNOWN"
        report.warnings.append(
            ExecutionChallengeIssue(
                "unsupported-schema-version",
                "unsupported replay-receipt schema version",
                "$/schema_version",
            )
        )
        return report
    if not _check_schema(value, REPLAY_SCHEMA_NAME, report):
        return report
    if value["replay_identity"] != _identity_without(value, "replay_identity"):
        report.invalidate(
            "replay-identity-mismatch", "replay_identity is not canonical", "$/replay_identity"
        )
    try:
        consumed = _time(cast(str, value["consumed_at"]))
        watermark = _time(cast(str, value["time_watermark"]))
    except (TypeError, ValueError) as exc:
        report.invalidate("timestamp-invalid", str(exc), "$/consumed_at")
        return report
    if watermark < consumed:
        report.invalidate(
            "watermark-invalid", "time watermark must not precede consumption", "$/time_watermark"
        )
    report.replay_receipt = deepcopy(value)
    report.replay_identity = value["replay_identity"]
    return report


def verify_replay_receipt(
    replay_receipt: dict[str, Any],
    challenge: dict[str, Any],
    receipt: dict[str, Any],
    *,
    store: ReplayStore | None = None,
    target: str = "<replay-verification>",
) -> ReplayReport:
    """Verify portable replay evidence without mutating local state."""

    report = validate_replay_receipt_value(replay_receipt, target=target)
    if not report.valid:
        return report
    binding = bind_challenge_to_receipt(challenge, receipt, target=target)
    if not binding.valid:
        report.issues.extend(binding.issues)
        report.valid = False
        report.status = "FAIL"
        return report
    expected_scope = challenge["scope"]
    for key, expected in cast(dict[str, Any], expected_scope).items():
        if replay_receipt["scope"].get(key) != expected:
            report.invalidate(
                "replay-scope-mismatch",
                f"replay scope {key} does not match challenge",
                f"$/scope/{key}",
            )
    if replay_receipt["challenge_identity"] != challenge["challenge_identity"]:
        report.invalidate(
            "replay-challenge-mismatch",
            "replay receipt references another challenge",
            "$/challenge_identity",
        )
    if replay_receipt["receipt_identity"] != receipt["receipt_identity"]:
        report.invalidate(
            "replay-receipt-mismatch",
            "replay receipt references another execution receipt",
            "$/receipt_identity",
        )
    try:
        consumed = _time(cast(str, replay_receipt["consumed_at"]))
        issued = _time(cast(str, challenge["issued_at"]))
        expires = _time(cast(str, challenge["expires_at"]))
        if consumed < issued or consumed >= expires:
            report.invalidate(
                "replay-outside-challenge-window",
                "replay consumption is outside the challenge window",
                "$/consumed_at",
            )
    except (TypeError, ValueError) as exc:
        report.invalidate("timestamp-invalid", str(exc), "$/consumed_at")
    if replay_receipt["store_head_identity"] != replay_receipt["store_entry_identity"]:
        report.invalidate(
            "replay-head-mismatch",
            "portable replay receipt must identify its consumed entry as the store head",
            "$/store_head_identity",
        )
    if store is not None and report.valid:
        try:
            entries = store._read_entries()
        except _ReplayStoreError as exc:
            report.invalidate("replay-store-invalid", str(exc), str(store.root))
            return report
        matching = [
            entry
            for entry in entries
            if entry["entry_identity"] == replay_receipt["store_entry_identity"]
        ]
        if not matching:
            report.invalidate(
                "replay-entry-missing",
                "replay entry is absent from the supplied store",
                "$/store_entry_identity",
            )
        else:
            entry = matching[0]
            for key in (
                "challenge_identity",
                "receipt_identity",
                "scope",
                "consumed_at",
                "previous_entry_identity",
                "time_watermark",
            ):
                if entry[key] != replay_receipt[key]:
                    report.invalidate(
                        "replay-entry-mismatch",
                        f"store entry {key} differs from replay receipt",
                        f"$/{key}",
                    )
            if (
                not entries
                or entries[-1]["entry_identity"] != replay_receipt["store_head_identity"]
            ):
                report.invalidate(
                    "replay-head-stale",
                    "replay receipt does not identify the current local store head",
                    "$/store_head_identity",
                )
    report.replay_receipt = deepcopy(replay_receipt)
    report.replay_identity = replay_receipt["replay_identity"]
    return report


def validate_replay_receipt_file(path: Path) -> ReplayReport:
    return validate_replay_receipt_value(load_json_object(path), target=str(path))
