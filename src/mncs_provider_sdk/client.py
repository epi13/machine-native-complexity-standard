"""Timeout-safe SDK client for explicit provider execution."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from mncs_validator.provider import run_provider


def request(
    command: list[str], message: dict[str, Any], *, timeout: float = 30.0
) -> dict[str, Any]:
    return run_provider(command, message, timeout=timeout)
