"""Bootstrap-specific errors."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ..errors import MncsError


class BootstrapError(MncsError):
    """Expected operational bootstrap failure."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class RegistryError(BootstrapError):
    """Family registry is invalid or unreadable."""


class PlanError(BootstrapError):
    """A plan cannot be produced."""


class ConfirmationRequired(BootstrapError):
    """Mutating action requires --yes or an interactive confirmation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=15)
