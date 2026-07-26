# SPDX-License-Identifier: Apache-2.0


def divide(numerator: int, denominator: int) -> int:
    if denominator == 0:
        raise ZeroDivisionError
    return numerator // denominator
