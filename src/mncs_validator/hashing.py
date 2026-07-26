"""Content identity helpers."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


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
