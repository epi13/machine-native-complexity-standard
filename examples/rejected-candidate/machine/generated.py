# SPDX-License-Identifier: Apache-2.0
# MNCS-GENERATED: DO NOT EDIT
# MNCS-Version: 0.1
# Manifest: ../manifest.json
# Generator: branch-specializer 0.2
# Regenerate: make example-rejected


def clamp(value: int, low: int, high: int) -> int:
    if low > high:
        raise ValueError("invalid bounds")
    if value < low:
        return low
    if value > high:
        return high
    return value
