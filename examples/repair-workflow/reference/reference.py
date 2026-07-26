# SPDX-License-Identifier: Apache-2.0


def select(items: list[int], index: int) -> int:
    if not 0 <= index < len(items):
        raise IndexError(index)
    return items[index]
