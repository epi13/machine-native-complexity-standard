"""Custom validator exceptions."""

# SPDX-License-Identifier: Apache-2.0


class MncsError(Exception):
    """Base class for expected MNCS failures."""


class SchemaNotFoundError(MncsError):
    """Raised when a bundled schema name cannot be resolved."""


class ManifestError(MncsError):
    """Raised when a manifest cannot be loaded safely."""


class HashMismatchError(MncsError):
    """Raised when content does not match its declared identity."""
