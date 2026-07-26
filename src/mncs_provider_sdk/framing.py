"""Strict deterministic JSON Lines framing."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Any, TextIO

from mncs_validator.canonical import canonicalize


def read_message(stream: TextIO) -> dict[str, Any]:
    line = stream.readline()
    if not line or not line.endswith("\n"):
        raise ValueError("expected one newline-terminated JSON message")
    value: Any = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("protocol message must be an object")
    return value


def write_message(stream: TextIO, value: dict[str, Any]) -> None:
    stream.buffer.write(canonicalize(value) + b"\n")
    stream.flush()
