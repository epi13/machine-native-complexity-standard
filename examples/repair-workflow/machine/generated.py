# SPDX-License-Identifier: Apache-2.0
# MNCS-GENERATED: DO NOT EDIT
# MNCS-Version: 0.1
# Manifest: ../manifest.json
# Generator: bounded-repair-generator 1.1
# Regenerate: make example-repair


def select(items: list[int], index: int) -> int:
    if index < 0 or index >= len(items):
        raise IndexError(index)
    return items[index]
