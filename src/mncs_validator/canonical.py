"""RFC 8785 canonical JSON and content identities."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import rfc8785

from .errors import MncsError
from .hashing import read_regular_file


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number {value}")


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _check_numbers(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite JSON numbers are forbidden")
    if isinstance(value, dict):
        for child in value.values():
            _check_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _check_numbers(child)


def parse_json_bytes(content: bytes) -> Any:
    """Parse strict UTF-8 JSON while rejecting duplicate keys and nonfinite numbers."""

    try:
        value: Any = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
        _check_numbers(value)
        return value
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise MncsError(f"invalid canonical JSON input: {exc}") from exc


def canonicalize(value: Any) -> bytes:
    """Return RFC 8785 JCS bytes."""

    try:
        _check_numbers(value)
        return rfc8785.dumps(value)
    except (ValueError, TypeError, rfc8785.CanonicalizationError) as exc:
        raise MncsError(f"cannot canonicalize JSON: {exc}") from exc


def canonicalize_bytes(content: bytes) -> bytes:
    """Parse and canonicalize strict JSON bytes."""

    return canonicalize(parse_json_bytes(content))


def canonicalize_file(path: Path) -> bytes:
    """Read a bounded regular file and return its canonical JSON."""

    return canonicalize_bytes(read_regular_file(path))


def canonical_sha256(value: Any) -> str:
    """Return a lowercase hexadecimal SHA-256 identity for canonical bytes."""

    return hashlib.sha256(canonicalize(value)).hexdigest()


def canonical_sha256_file(path: Path) -> str:
    """Return the canonical identity of one strict JSON file."""

    return hashlib.sha256(canonicalize_file(path)).hexdigest()
