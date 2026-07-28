"""Validation helpers for non-normative language evidence profiles."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from .schemas import schema_errors

PROFILE_SCHEMA_NAME = "language-evidence-profile"


def load_language_profile(path: Path) -> dict[str, Any]:
    """Load a profile as a JSON object without inferring conformance."""

    value: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("language profile must be a JSON object")
    return cast(dict[str, Any], value)


def validate_language_profile(profile: dict[str, Any]) -> list[str]:
    """Return stable schema errors for one experimental profile."""

    return schema_errors(profile, PROFILE_SCHEMA_NAME)


def validate_language_profile_file(path: Path) -> list[str]:
    """Load and validate one profile file."""

    return validate_language_profile(load_language_profile(path))
