"""Content identity helpers."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
DEFAULT_MAX_FILE_BYTES = 10 * 1024 * 1024


def sha256_file(path: Path) -> str:
    """Hash a regular file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def sha256_bytes(content: bytes) -> str:
    """Hash bytes in MNCS identity form."""

    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def read_regular_file(path: Path, *, max_bytes: int = DEFAULT_MAX_FILE_BYTES) -> bytes:
    """Read one regular file through a no-follow descriptor with stability checks."""

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"not a regular file: {path}")
        if before.st_size > max_bytes:
            raise ValueError(f"file exceeds {max_bytes} byte policy: {path}")
        content = bytearray()
        total = 0
        while chunk := os.read(descriptor, CHUNK_SIZE):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"file exceeds {max_bytes} byte policy: {path}")
            content.extend(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError(f"file changed while hashing: {path}")
        return bytes(content)
    finally:
        os.close(descriptor)


def sha256_regular_file(path: Path, *, max_bytes: int = DEFAULT_MAX_FILE_BYTES) -> str:
    """Hash exactly the stable bytes returned by :func:`read_regular_file`."""

    return sha256_bytes(read_regular_file(path, max_bytes=max_bytes))


def tree_hash(path: Path) -> str:
    """Hash a directory from sorted relative paths and file identities."""

    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        relative = item.relative_to(path).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        file_hash = sha256_file(item).encode()
        digest.update(file_hash)
    return f"sha256:{digest.hexdigest()}"


def hash_path(path: Path) -> str:
    """Hash a file or directory."""

    return tree_hash(path)
