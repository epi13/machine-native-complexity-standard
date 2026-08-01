"""RFC 3339 parsing and bounded freshness decisions.

Freshness uses only supplied record values and caller-provided evaluation time. No
clock, network, revocation service, or evidence process is invoked implicitly.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import cast

from .status import STATUS_ORDER, Status, aggregate_status


def parse_time(value: object) -> datetime | None:
    """Parse an RFC 3339/ISO 8601 timestamp, including declared offsets."""

    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def freshness_status(value: object, at: datetime | None) -> Status:
    """Return the declared status, weakened to UNKNOWN after expiry."""

    if not isinstance(value, dict):
        return "UNKNOWN"
    declared = value.get("status")
    status = declared if isinstance(declared, str) and declared in STATUS_ORDER else "UNKNOWN"
    valid_until = parse_time(value.get("valid_until"))
    if at is not None and valid_until is not None and at > valid_until:
        return aggregate_status([status, "UNKNOWN"])
    return cast(Status, status)
