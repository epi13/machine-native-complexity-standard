# SPDX-License-Identifier: Apache-2.0
# MNCS-GENERATED: DO NOT EDIT
# MNCS-Version: 0.1
# Manifest: ../manifest.json
# Generator: arithmetic-generator 1.0
# Regenerate: make example-provider


def divide(numerator: int, denominator: int) -> int:
    if denominator == 0:
        raise ZeroDivisionError
    return numerator // denominator
