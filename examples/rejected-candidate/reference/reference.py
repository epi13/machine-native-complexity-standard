# SPDX-License-Identifier: Apache-2.0


def clamp(value: int, low: int, high: int) -> int:
    if low > high:
        raise ValueError("invalid bounds")
    return min(high, max(low, value))
