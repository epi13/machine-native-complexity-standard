"""Deterministic experimental composed-result aggregation."""
from __future__ import annotations
from typing import Any


def aggregate(results: list[dict[str, Any]], *, allow_review: bool = False) -> str:
    """Aggregate required component and boundary results without erasing uncertainty."""
    required = [result for result in results if result.get("required") is True]
    if not required or any(not result.get("evidence_ref") for result in required):
        return "UNKNOWN"
    statuses = {result.get("status") for result in required}
    if "FAIL" in statuses:
        return "FAIL"
    if "UNKNOWN" in statuses:
        return "REVIEW_REQUIRED" if allow_review else "UNKNOWN"
    return "PASS" if statuses == {"PASS"} else "UNKNOWN"
