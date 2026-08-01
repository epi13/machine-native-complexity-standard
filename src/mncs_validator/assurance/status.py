"""Authoritative MNCS status lattice.

This is the only result aggregation implementation in the RC validator package.
Invalid or missing status inputs remain ``UNKNOWN``.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, cast

Status = Literal["PASS", "FAIL", "UNKNOWN"]
STATUS_ORDER: dict[str, int] = {"PASS": 0, "UNKNOWN": 1, "FAIL": 2}


def aggregate_status(statuses: Sequence[str]) -> Status:
    """Apply ``FAIL > UNKNOWN > PASS`` without promoting absent evidence."""

    if not statuses or any(status not in STATUS_ORDER for status in statuses):
        return "UNKNOWN"
    return cast(Status, max(statuses, key=STATUS_ORDER.__getitem__))
