"""Installation receipt persistence."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..schemas import schema_errors
from .errors import BootstrapError


def validate_receipt(payload: dict[str, Any]) -> None:
    errors = schema_errors(payload, "bootstrap-receipt-0.1")
    if errors:
        raise BootstrapError("bootstrap receipt invalid: " + "; ".join(errors))


def write_receipt(directory: Path, payload: dict[str, Any]) -> Path:
    validate_receipt(payload)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"receipt-{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest = directory / "latest.json"
    latest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path
