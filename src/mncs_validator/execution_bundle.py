"""Experimental immutable execution-bundle creation and verification.

An execution bundle freezes bounded test material.  Its logical identity is the
canonical SHA-256 of the manifest without ``bundle_identity``; the archive
identity is the SHA-256 of the exact transport bytes.  Neither identity is an
assurance, conformance, sandbox, custody, or promotion claim.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import stat
import unicodedata
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .canonical import canonical_sha256, canonicalize
from .hashing import CHUNK_SIZE, read_regular_file, sha256_bytes
from .schemas import schema_errors
from .validation import load_json_object

SCHEMA_NAME = "execution-bundle-0.1-experimental"
SOURCE_SCHEMA_NAME = "execution-bundle-source-0.1-experimental"
SCHEMA_VERSION = "0.1-experimental"
BUNDLE_FORMAT = "mncs-execution-bundle-zip-0.1"
MANIFEST_NAME = "manifest.json"
MAX_FILE_COUNT = 2_000
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_PATH_BYTES = 512
MAX_EXPANSION_RATIO = 100
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_ROLES = {
    "test",
    "harness",
    "expected",
    "manifest",
    "fixture",
    "input",
    "runtime-requirement",
    "policy-reference",
    "support",
}


@dataclass(frozen=True)
class ExecutionBundleIssue:
    code: str
    message: str
    path: str = ""


@dataclass
class ExecutionBundleReport:
    """Offline result for bundle construction or archive verification."""

    target: str
    valid: bool = True
    supported: bool = True
    bundle_id: str | None = None
    bundle_identity: str | None = None
    archive_identity: str | None = None
    manifest: dict[str, Any] | None = None
    issues: list[ExecutionBundleIssue] = field(default_factory=list)
    warnings: list[ExecutionBundleIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        return "PASS" if self.valid else "INVALID"

    def invalidate(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.issues.append(ExecutionBundleIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


@dataclass
class ExecutionBundleBindingReport:
    target: str = "<binding>"
    valid: bool = True
    issues: list[ExecutionBundleIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        return "PASS" if self.valid else "INVALID"

    def invalidate(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.issues.append(ExecutionBundleIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


def _sha256_file(path: Path, max_bytes: int = MAX_ARCHIVE_BYTES) -> str:
    return sha256_bytes(read_regular_file(path, max_bytes=max_bytes))


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _parse_json_bytes(content: bytes) -> dict[str, Any]:
    value = json.loads(
        content.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("JSON value must be an object")
    return value


def normalize_bundle_path(value: str) -> str:
    """Return a portable relative path or raise ``ValueError``."""

    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("bundle paths must be non-empty strings without NUL")
    if value != unicodedata.normalize("NFC", value):
        raise ValueError("bundle paths must use NFC Unicode normalization")
    if "\\" in value or value.startswith("/") or value.startswith("//"):
        raise ValueError("bundle paths must use safe relative POSIX syntax")
    if len(value.encode("utf-8")) > MAX_PATH_BYTES:
        raise ValueError("bundle path exceeds the maximum UTF-8 byte length")
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise ValueError("Windows drive-letter paths are forbidden")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("bundle paths cannot contain empty, '.', or '..' components")
    normalized = "/".join(parts)
    if normalized == MANIFEST_NAME:
        raise ValueError("manifest.json is reserved for the generated bundle manifest")
    return normalized


def _path_key(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold()


def _validate_paths(
    paths: list[str], report: ExecutionBundleReport, *, path_limit: int = MAX_PATH_BYTES
) -> bool:
    seen: dict[str, str] = {}
    valid = True
    for path in paths:
        try:
            normalized = normalize_bundle_path(path)
        except ValueError as exc:
            report.invalidate("UNSAFE-PATH", str(exc), path)
            valid = False
            continue
        if len(normalized.encode("utf-8")) > path_limit:
            report.invalidate("PATH-SIZE-LIMIT", "bundle path exceeds declared limit", path)
            valid = False
            continue
        key = _path_key(normalized)
        if key in seen:
            report.invalidate(
                "CASE-COLLISION" if seen[key] != normalized else "DUPLICATE-PATH",
                f"bundle path collides with {seen[key]!r}",
                path,
            )
            valid = False
        else:
            seen[key] = normalized
    return valid


def _limits(value: dict[str, Any]) -> tuple[int, int, int, int, int] | None:
    limits = value.get("limits")
    if not isinstance(limits, dict):
        return None
    names = (
        "max_file_count",
        "max_file_bytes",
        "max_total_bytes",
        "max_path_bytes",
        "max_expansion_ratio",
    )
    values = tuple(limits.get(name) for name in names)
    if not all(
        isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in values
    ):
        return None
    return values  # type: ignore[return-value]


def _check_limits(
    value: dict[str, Any], report: ExecutionBundleReport
) -> tuple[int, int, int, int, int] | None:
    limits = _limits(value)
    if limits is None:
        report.invalidate(
            "LIMITS-INVALID", "bundle limits must contain positive integers", "$/limits"
        )
        return None
    global_limits = (
        MAX_FILE_COUNT,
        MAX_FILE_BYTES,
        MAX_TOTAL_BYTES,
        MAX_PATH_BYTES,
        MAX_EXPANSION_RATIO,
    )
    for name, actual, maximum in zip(
        (
            "max_file_count",
            "max_file_bytes",
            "max_total_bytes",
            "max_path_bytes",
            "max_expansion_ratio",
        ),
        limits,
        global_limits,
        strict=True,
    ):
        if actual > maximum:
            report.invalidate(
                "LIMITS-EXCEED-GLOBAL", f"{name} exceeds the verifier maximum", f"$/limits/{name}"
            )
    return limits


def _entry_identity(entries: list[dict[str, Any]], role: str) -> str | None:
    selected = [
        {"path": entry["path"], "identity": entry["identity"], "mode": entry["mode"]}
        for entry in entries
        if entry["role"] == role
    ]
    if not selected:
        return None
    return canonical_sha256({"role": role, "entries": selected})


def _reference_identity(references: list[dict[str, str]]) -> str | None:
    return canonical_sha256({"references": references}) if references else None


def _entry_map(
    manifest: dict[str, Any], report: ExecutionBundleReport, *, path_limit: int = MAX_PATH_BYTES
) -> dict[str, dict[str, Any]]:
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        report.invalidate("ENTRIES-INVALID", "entries must be an array", "$/entries")
        return {}
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    if len(entries) > MAX_FILE_COUNT:
        report.invalidate("FILE-COUNT-LIMIT", "bundle contains too many entries", "$/entries")
    _validate_paths(
        [path for path in paths if isinstance(path, str)], report, path_limit=path_limit
    )
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            continue
        result[entry["path"]] = entry
    return result


def _build_manifest(source: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    runtime = [
        {
            "path": path,
            "identity": next(item["identity"] for item in entries if item["path"] == path),
        }
        for path in source["runtime_requirements"]
    ]
    policies = [
        {
            "path": path,
            "identity": next(item["identity"] for item in entries if item["path"] == path),
        }
        for path in source["policy_references"]
    ]
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "mncs-execution-bundle",
        "bundle_id": source["bundle_id"],
        "bundle_identity": "0" * 64,
        "bundle_format": BUNDLE_FORMAT,
        "entries": sorted(entries, key=lambda item: item["path"].encode("utf-8")),
        "entrypoints": sorted(source["entrypoints"], key=lambda item: item["path"].encode("utf-8")),
        "runtime_requirements": runtime,
        "policy_references": policies,
        "harness_identity": _entry_identity(entries, "harness"),
        "input_snapshot_identity": _entry_identity(entries, "input"),
        "policy_identity": _reference_identity(policies),
        "limits": source["limits"],
        "extensions": source["extensions"],
    }
    material = {key: value for key, value in manifest.items() if key != "bundle_identity"}
    manifest["bundle_identity"] = canonical_sha256(material)
    return manifest


def _zip_info(name: str, mode: str, size: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | int(mode, 8)) << 16
    info.flag_bits |= 0x800
    info.file_size = size
    info.compress_size = size
    return info


def _write_archive(output: Path, manifest: dict[str, Any], content: dict[str, bytes]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError(f"refusing to overwrite execution bundle: {output}")
    with (
        output.open("xb") as stream,
        zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive,
    ):
        archive.writestr(
            _zip_info(MANIFEST_NAME, "0644", len(canonicalize(manifest))),
            canonicalize(manifest),
        )
        for entry in manifest["entries"]:
            data = content[entry["path"]]
            archive.writestr(_zip_info(entry["path"], entry["mode"], len(data)), data)


def build_execution_bundle(
    source_manifest: Path, source_root: Path, output: Path
) -> ExecutionBundleReport:
    """Build a deterministic ZIP from a strict source manifest."""

    report = ExecutionBundleReport(target=str(output))
    try:
        source = load_json_object(source_manifest)
    except Exception as exc:
        report.invalidate("SOURCE-READ", str(exc), str(source_manifest))
        return report
    if source.get("schema_version") != SCHEMA_VERSION:
        report.supported = False
        report.valid = False
        report.invalidate(
            "UNSUPPORTED-SCHEMA", "unsupported source schema version", "$/schema_version"
        )
        return report
    for error in schema_errors(source, SOURCE_SCHEMA_NAME):
        report.invalidate("SCHEMA", error)
    if not report.valid:
        return report
    limits = _check_limits(source, report)
    if limits is None or not report.valid:
        return report
    root = source_root.resolve()
    source_entries = source["entries"]
    output_paths = [entry["path"] for entry in source_entries]
    _validate_paths(output_paths, report, path_limit=limits[3])
    if len(source_entries) > limits[0]:
        report.invalidate("FILE-COUNT-LIMIT", "source entries exceed max_file_count", "$/entries")
    if not report.valid:
        return report
    content: dict[str, bytes] = {}
    entries: list[dict[str, Any]] = []
    total = 0
    try:
        for source_entry in source_entries:
            output_path = normalize_bundle_path(source_entry["path"])
            source_path = normalize_bundle_path(source_entry["source"])
            candidate = root / source_path
            current = root
            for part in source_path.split("/"):
                current = current / part
                if current.is_symlink():
                    raise ValueError(f"symbolic links are forbidden: {source_path}")
            candidate = candidate.resolve(strict=True)
            candidate.relative_to(root)
            source_stat = os.lstat(candidate)
            if stat.S_ISLNK(source_stat.st_mode):
                raise ValueError(f"symbolic links are forbidden: {source_path}")
            if not stat.S_ISREG(source_stat.st_mode):
                raise ValueError(f"special files are forbidden: {source_path}")
            if source_stat.st_nlink != 1:
                raise ValueError(f"hardlinked files are forbidden: {source_path}")
            data = read_regular_file(candidate, max_bytes=min(limits[1], MAX_FILE_BYTES))
            if len(data) > limits[1]:
                raise ValueError(f"entry exceeds max_file_bytes: {output_path}")
            total += len(data)
            if total > limits[2]:
                raise ValueError("entries exceed max_total_bytes")
            content[output_path] = data
            entries.append(
                {
                    "path": output_path,
                    "identity": sha256_bytes(data).removeprefix("sha256:"),
                    "size_bytes": len(data),
                    "role": source_entry["role"],
                    "mode": source_entry["mode"],
                }
            )
        entry_paths = {entry["path"] for entry in entries}
        for ref in (*source["runtime_requirements"], *source["policy_references"]):
            if ref not in entry_paths:
                raise ValueError(f"referenced bundle path is not an entry: {ref}")
        for ref in source["runtime_requirements"]:
            if (
                next(entry for entry in entries if entry["path"] == ref)["role"]
                != "runtime-requirement"
            ):
                raise ValueError(f"runtime requirement has the wrong entry role: {ref}")
        for ref in source["policy_references"]:
            if (
                next(entry for entry in entries if entry["path"] == ref)["role"]
                != "policy-reference"
            ):
                raise ValueError(f"policy reference has the wrong entry role: {ref}")
        for entrypoint in source["entrypoints"]:
            normalize_bundle_path(entrypoint["path"])
            if entrypoint["path"] not in entry_paths:
                raise ValueError(f"entrypoint is not an entry: {entrypoint['path']}")
        manifest = _build_manifest(source, entries)
        for error in schema_errors(manifest, SCHEMA_NAME):
            report.invalidate("SCHEMA", error)
        if not report.valid:
            return report
        _write_archive(output, manifest, content)
        report.manifest = manifest
        report.bundle_id = manifest["bundle_id"]
        report.bundle_identity = manifest["bundle_identity"]
        report.archive_identity = _sha256_file(output)
        return report
    except (OSError, ValueError, StopIteration) as exc:
        report.invalidate("BUILD-INVALID", str(exc))
        return report


def _read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    data = bytearray()
    with archive.open(info, "r") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            data.extend(chunk)
            if len(data) > limit:
                raise ValueError("member exceeds bounded streamed size")
    if len(data) != info.file_size:
        raise ValueError("member streamed size differs from ZIP metadata")
    return bytes(data)


def verify_execution_bundle_archive(
    archive_path: Path,
    *,
    expected_bundle_identity: str | None = None,
    expected_archive_identity: str | None = None,
) -> ExecutionBundleReport:
    """Verify a ZIP without extracting or executing its contents."""

    report = ExecutionBundleReport(target=str(archive_path))
    try:
        archive_identity = _sha256_file(archive_path)
        report.archive_identity = archive_identity
        if expected_archive_identity is not None and archive_identity != expected_archive_identity:
            report.invalidate(
                "ARCHIVE-IDENTITY-MISMATCH", "archive identity does not match expectation"
            )
        if archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
            report.invalidate("ARCHIVE-SIZE-LIMIT", "archive exceeds bounded transport size")
            return report
        with zipfile.ZipFile(archive_path, "r") as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_FILE_COUNT + 1:
                report.invalidate("FILE-COUNT-LIMIT", "archive member count exceeds bounds")
                return report
            members: dict[str, bytes] = {}
            member_infos: dict[str, zipfile.ZipInfo] = {}
            keys: dict[str, str] = {}
            declared_total = 0
            for info in infos:
                try:
                    name = (
                        normalize_bundle_path(info.filename)
                        if info.filename != MANIFEST_NAME
                        else MANIFEST_NAME
                    )
                except ValueError as exc:
                    report.invalidate("UNSAFE-PATH", str(exc), info.filename)
                    continue
                key = _path_key(name)
                if key in keys:
                    report.invalidate(
                        "CASE-COLLISION" if keys[key] != name else "DUPLICATE-PATH",
                        "duplicate archive member",
                        name,
                    )
                    continue
                keys[key] = name
                mode = (info.external_attr >> 16) & 0o170000
                if mode != stat.S_IFREG:
                    report.invalidate("SPECIAL-FILE", "archive members must be regular files", name)
                    continue
                if info.flag_bits & 1:
                    report.invalidate(
                        "ENCRYPTED-MEMBER", "encrypted ZIP members are unsupported", name
                    )
                    continue
                if info.file_size > MAX_FILE_BYTES:
                    report.invalidate(
                        "FILE-SIZE-LIMIT", "archive member exceeds global size limit", name
                    )
                    continue
                if (info.compress_size == 0 and info.file_size > 0) or (
                    info.compress_size and info.file_size / info.compress_size > MAX_EXPANSION_RATIO
                ):
                    report.invalidate(
                        "EXPANSION-LIMIT", "archive member exceeds expansion ratio", name
                    )
                    continue
                declared_total += info.file_size
                if declared_total > MAX_TOTAL_BYTES:
                    report.invalidate(
                        "TOTAL-SIZE-LIMIT", "archive exceeds global uncompressed size limit"
                    )
                    continue
                members[name] = _read_member(archive, info, MAX_FILE_BYTES)
                member_infos[name] = info
            if not report.valid:
                return report
            if MANIFEST_NAME not in members:
                report.invalidate("MANIFEST-MISSING", "archive does not contain manifest.json")
                return report
            try:
                manifest = _parse_json_bytes(members[MANIFEST_NAME])
            except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                report.invalidate("MANIFEST-INVALID", str(exc), MANIFEST_NAME)
                return report
            if not isinstance(manifest, dict):
                report.invalidate("MANIFEST-INVALID", "manifest must be an object", MANIFEST_NAME)
                return report
            if manifest.get("schema_version") != SCHEMA_VERSION:
                report.supported = False
                report.valid = False
                report.invalidate(
                    "UNSUPPORTED-SCHEMA",
                    "unsupported execution-bundle schema version",
                    "$/schema_version",
                )
                return report
            for error in schema_errors(manifest, SCHEMA_NAME):
                report.invalidate("SCHEMA", error)
            report.manifest = manifest
            report.bundle_id = manifest.get("bundle_id")
            report.bundle_identity = manifest.get("bundle_identity")
            if canonicalize(manifest) != members[MANIFEST_NAME]:
                report.invalidate(
                    "MANIFEST-CANONICAL", "manifest is not canonical JSON", MANIFEST_NAME
                )
            limits = _check_limits(manifest, report)
            if limits is None:
                return report
            entries = _entry_map(manifest, report, path_limit=limits[3])
            if len(entries) > limits[0]:
                report.invalidate(
                    "FILE-COUNT-LIMIT", "manifest exceeds max_file_count", "$/entries"
                )
            expected_names = {MANIFEST_NAME, *entries}
            if set(members) != expected_names:
                report.invalidate(
                    "MANIFEST-ARCHIVE-MISMATCH", "archive members do not match manifest entries"
                )
            actual_total = 0
            for path, entry in entries.items():
                if path not in members:
                    report.invalidate(
                        "ENTRY-MISSING", "manifest entry is missing from archive", path
                    )
                    continue
                data = members[path]
                actual_total += len(data)
                if len(data) > limits[1]:
                    report.invalidate("FILE-SIZE-LIMIT", "entry exceeds max_file_bytes", path)
                info = member_infos[path]
                if (info.compress_size == 0 and info.file_size > 0) or (
                    info.compress_size and info.file_size / info.compress_size > limits[4]
                ):
                    report.invalidate("EXPANSION-LIMIT", "entry exceeds max_expansion_ratio", path)
                if len(data) != entry.get("size_bytes"):
                    report.invalidate("SIZE-MISMATCH", "entry size differs from manifest", path)
                if sha256_bytes(data).removeprefix("sha256:") != entry.get("identity"):
                    report.invalidate(
                        "CONTENT-DIGEST-MISMATCH", "entry digest differs from manifest", path
                    )
                actual_mode = "0755" if ((info.external_attr >> 16) & 0o111) else "0644"
                if actual_mode != entry.get("mode"):
                    report.invalidate("MODE-MISMATCH", "entry mode differs from manifest", path)
            if actual_total > limits[2]:
                report.invalidate("TOTAL-SIZE-LIMIT", "entries exceed max_total_bytes")
            for entrypoint in manifest.get("entrypoints", []):
                if entrypoint.get("path") not in entries:
                    report.invalidate(
                        "ENTRYPOINT-MISSING",
                        "entrypoint is not an entry",
                        entrypoint.get("path", ""),
                    )
            for reference_name, expected_role in (
                ("runtime_requirements", "runtime-requirement"),
                ("policy_references", "policy-reference"),
            ):
                for reference in manifest.get(reference_name, []):
                    reference_entry = entries.get(reference.get("path"))
                    if reference_entry is None:
                        report.invalidate(
                            "REFERENCE-MISSING",
                            "reference path is not an entry",
                            reference.get("path", ""),
                        )
                    elif (
                        reference_entry.get("identity") != reference.get("identity")
                        or reference_entry.get("role") != expected_role
                    ):
                        report.invalidate(
                            "REFERENCE-MISMATCH",
                            "reference does not match entry",
                            reference.get("path", ""),
                        )
            if manifest.get("harness_identity") != _entry_identity(
                list(entries.values()), "harness"
            ):
                report.invalidate(
                    "HARNESS-IDENTITY-MISMATCH",
                    "harness identity is not derived from entries",
                    "$/harness_identity",
                )
            if manifest.get("input_snapshot_identity") != _entry_identity(
                list(entries.values()), "input"
            ):
                report.invalidate(
                    "INPUT-IDENTITY-MISMATCH",
                    "input identity is not derived from entries",
                    "$/input_snapshot_identity",
                )
            if manifest.get("policy_identity") != _reference_identity(
                manifest.get("policy_references", [])
            ):
                report.invalidate(
                    "POLICY-IDENTITY-MISMATCH",
                    "policy identity is not derived from references",
                    "$/policy_identity",
                )
            material = {key: value for key, value in manifest.items() if key != "bundle_identity"}
            if manifest.get("bundle_identity") != canonical_sha256(material):
                report.invalidate(
                    "BUNDLE-IDENTITY-MISMATCH",
                    "bundle identity is not canonical",
                    "$/bundle_identity",
                )
            if (
                expected_bundle_identity is not None
                and manifest.get("bundle_identity") != expected_bundle_identity
            ):
                report.invalidate(
                    "BUNDLE-IDENTITY-MISMATCH",
                    "bundle identity does not match expectation",
                    "$/bundle_identity",
                )
            return report
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        report.invalidate("ARCHIVE-INVALID", str(exc), str(archive_path))
        return report


def validate_execution_bundle(path: Path, **kwargs: Any) -> ExecutionBundleReport:
    """Compatibility name for offline archive validation."""

    return verify_execution_bundle_archive(path, **kwargs)


def bind_receipt_to_bundle(
    receipt: dict[str, Any], bundle: ExecutionBundleReport, *, target: str = "<binding>"
) -> ExecutionBundleBindingReport:
    """Check that receipt bundle facts bind to one verified archive."""

    report = ExecutionBundleBindingReport(target=target)
    if not bundle.valid or bundle.bundle_identity is None or bundle.manifest is None:
        report.invalidate(
            "BUNDLE-INVALID", "receipt cannot bind to an invalid or unresolved bundle"
        )
        return report
    receipt_bundle = receipt.get("bundle")
    if not isinstance(receipt_bundle, dict):
        report.invalidate("RECEIPT-BUNDLE-MISSING", "receipt has no bundle binding", "$/bundle")
        return report
    if receipt_bundle.get("test_bundle_identity") != bundle.bundle_identity:
        report.invalidate(
            "BUNDLE-IDENTITY-MISMATCH",
            "receipt references a different logical bundle identity",
            "$/bundle/test_bundle_identity",
        )
    for receipt_key, manifest_key in (
        ("harness_identity", "harness_identity"),
        ("input_snapshot_identity", "input_snapshot_identity"),
    ):
        expected = bundle.manifest.get(manifest_key)
        actual = receipt_bundle.get(receipt_key)
        if expected is not None and actual != expected:
            report.invalidate(
                "RECEIPT-BUNDLE-MISMATCH",
                f"receipt {receipt_key} differs from bundle",
                f"$/bundle/{receipt_key}",
            )
    policy = receipt.get("policy")
    if bundle.manifest.get("policy_identity") is not None and (
        not isinstance(policy, dict)
        or policy.get("execution_policy_identity") != bundle.manifest["policy_identity"]
    ):
        report.invalidate(
            "RECEIPT-POLICY-MISMATCH",
            "receipt policy differs from bundle policy references",
            "$/policy/execution_policy_identity",
        )
    return report
