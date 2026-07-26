"""Deterministic and safely inspectable `.mncs` evidence packages."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import stat
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import canonicalize, parse_json_bytes
from .errors import MncsError
from .hashing import read_regular_file, sha256_bytes

INDEX_PATH = "mncs-package-index.json"
MAX_PACKAGE_FILES = 4_000
MAX_NESTING = 24
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class PackageReport:
    valid: bool
    package_sha256: str
    file_count: int
    total_bytes: int
    evidence_index_sha256: str | None
    issues: list[str]
    index: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_name(name: str) -> PurePosixPath:
    if not name or "\\" in name or "\x00" in name:
        raise MncsError(f"unsafe package path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise MncsError(f"unsafe package path: {name!r}")
    if len(path.parts) > MAX_NESTING:
        raise MncsError(f"package path nesting exceeds {MAX_NESTING}: {name}")
    return path


def _entry(name: str, content: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.flag_bits |= 0x800
    return info, content


def _input_files(root: Path) -> list[tuple[str, bytes]]:
    if not root.is_dir():
        raise MncsError(f"bundle directory does not exist: {root}")
    files: list[tuple[str, bytes]] = []
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for directory in directories:
            if (current_path / directory).is_symlink():
                raise MncsError(f"symlinked directory is forbidden: {current_path / directory}")
        for name in names:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            _safe_name(relative)
            if relative == INDEX_PATH:
                raise MncsError(f"bundle reserves package path: {INDEX_PATH}")
            if path.is_symlink():
                raise MncsError(f"symlinked file is forbidden: {path}")
            content = read_regular_file(path, max_bytes=MAX_MEMBER_BYTES)
            files.append((relative, content))
    files.sort(key=lambda item: item[0].encode("utf-8"))
    if len(files) > MAX_PACKAGE_FILES:
        raise MncsError(f"package exceeds {MAX_PACKAGE_FILES} files")
    total = sum(len(content) for _, content in files)
    if total > MAX_TOTAL_BYTES:
        raise MncsError(f"package exceeds {MAX_TOTAL_BYTES} uncompressed bytes")
    return files


def pack(bundle: Path, output: Path, *, detached_attestation: Path | None = None) -> dict[str, Any]:
    """Create a byte-reproducible uncompressed ZIP package."""

    if output.exists():
        raise MncsError(f"refusing to overwrite package: {output}")
    files = _input_files(bundle)
    if detached_attestation is not None:
        files.append(
            (
                "attestations/detached.json",
                read_regular_file(detached_attestation, max_bytes=MAX_MEMBER_BYTES),
            )
        )
        files.sort(key=lambda item: item[0].encode("utf-8"))
    evidence_index = next(
        (sha256_bytes(content) for name, content in files if name == "evidence/index.json"),
        None,
    )
    index: dict[str, Any] = {
        "schema_version": "0.2",
        "mncs_version": "0.2",
        "format": "mncs-zip-0.1",
        "files": [
            {"path": name, "size": len(content), "sha256": sha256_bytes(content)}
            for name, content in files
        ],
        "evidence_index_sha256": evidence_index,
        "extensions": {},
    }
    index_bytes = canonicalize(index)
    entries = [*files, (INDEX_PATH, index_bytes)]
    entries.sort(key=lambda item: item[0].encode("utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(
            output,
            "x",
            compression=zipfile.ZIP_STORED,
            allowZip64=True,
            strict_timestamps=True,
        ) as archive:
            for name, content in entries:
                info, payload = _entry(name, content)
                archive.writestr(info, payload)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    content = read_regular_file(output, max_bytes=MAX_TOTAL_BYTES + 16 * 1024 * 1024)
    return {
        "path": str(output),
        "package_sha256": sha256_bytes(content),
        "file_count": len(entries),
        "evidence_index_sha256": evidence_index,
    }


def _archive_report(path: Path, *, verify_content: bool) -> PackageReport:
    issues: list[str] = []
    package_content = read_regular_file(path, max_bytes=MAX_TOTAL_BYTES + 16 * 1024 * 1024)
    package_digest = sha256_bytes(package_content)
    index: dict[str, Any] | None = None
    total = 0
    count = 0
    evidence_index: str | None = None
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)):
                issues.append("duplicate archive member")
            if names != sorted(names, key=lambda value: value.encode("utf-8")):
                issues.append("members are not bytewise path sorted")
            if len(infos) > MAX_PACKAGE_FILES + 1:
                issues.append("file-count limit exceeded")
            for info in infos:
                count += 1
                try:
                    _safe_name(info.filename)
                except MncsError as exc:
                    issues.append(str(exc))
                mode = info.external_attr >> 16
                if mode and not stat.S_ISREG(mode):
                    issues.append(f"unsafe archive member type: {info.filename}")
                if info.is_dir():
                    issues.append(f"directory entries are forbidden: {info.filename}")
                if info.compress_type != zipfile.ZIP_STORED:
                    issues.append(f"non-deterministic compression is forbidden: {info.filename}")
                if info.file_size > MAX_MEMBER_BYTES:
                    issues.append(f"member size limit exceeded: {info.filename}")
                total += info.file_size
                if total > MAX_TOTAL_BYTES:
                    issues.append("total uncompressed size limit exceeded")
                    break
            if INDEX_PATH not in names:
                issues.append("package index is missing")
            else:
                raw_index = archive.read(INDEX_PATH)
                parsed = parse_json_bytes(raw_index)
                if not isinstance(parsed, dict) or canonicalize(parsed) != raw_index:
                    issues.append("package index is not canonical")
                else:
                    index = parsed
                    evidence_index_value = index.get("evidence_index_sha256")
                    evidence_index = (
                        evidence_index_value if isinstance(evidence_index_value, str) else None
                    )
            if verify_content and index is not None:
                indexed = index.get("files")
                if not isinstance(indexed, list):
                    issues.append("package index files must be an array")
                else:
                    expected_names: list[str] = []
                    for record in indexed:
                        if not isinstance(record, dict):
                            issues.append("malformed package index record")
                            continue
                        name = str(record.get("path", ""))
                        expected_names.append(name)
                        if name not in names:
                            issues.append(f"indexed member is missing: {name}")
                            continue
                        content = archive.read(name)
                        if len(content) != record.get("size"):
                            issues.append(f"size mismatch: {name}")
                        if sha256_bytes(content) != record.get("sha256"):
                            issues.append(f"hash mismatch: {name}")
                    actual = [name for name in names if name != INDEX_PATH]
                    if expected_names != actual:
                        issues.append("package index/member ordering mismatch")
                    if "evidence/index.json" in names:
                        actual_evidence = sha256_bytes(archive.read("evidence/index.json"))
                        if evidence_index != actual_evidence:
                            issues.append("embedded evidence-index identity mismatch")
    except (OSError, ValueError, zipfile.BadZipFile, MncsError) as exc:
        issues.append(f"invalid package: {exc}")
    return PackageReport(
        not issues,
        package_digest,
        count,
        total,
        evidence_index,
        sorted(set(issues)),
        index,
    )


def inspect_package(path: Path) -> PackageReport:
    """Inspect structure and limits without executing or extracting content."""

    return _archive_report(path, verify_content=False)


def verify_package(path: Path) -> PackageReport:
    """Verify structure, canonical index, and every indexed content hash."""

    return _archive_report(path, verify_content=True)


def unpack(path: Path, output: Path) -> PackageReport:
    """Securely extract a verified package to a new or empty directory."""

    report = verify_package(path)
    if not report.valid:
        return report
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise MncsError(f"refusing to extract into non-empty path: {output}")
    output.mkdir(parents=True, exist_ok=True)
    root = output.resolve()
    with zipfile.ZipFile(path, "r") as archive:
        for info in archive.infolist():
            pure = _safe_name(info.filename)
            target = root.joinpath(*pure.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if any(parent.is_symlink() for parent in [target, *target.parents] if parent != root):
                raise MncsError(f"symlink extraction path is forbidden: {info.filename}")
            resolved = target.resolve(strict=False)
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise MncsError(f"archive path escapes output: {info.filename}") from exc
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            try:
                with archive.open(info, "r") as source:
                    while chunk := source.read(1024 * 1024):
                        os.write(descriptor, chunk)
                os.fchmod(descriptor, 0o644)
            finally:
                os.close(descriptor)
    return report
