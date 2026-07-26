# SPDX-License-Identifier: Apache-2.0
# MNCS-GENERATED: DO NOT EDIT
# MNCS-Version: 0.1
# Manifest: ../manifest.json
# Generator: example-table-generator 1.0
# Regenerate: make example-http

_HEX = {**{48 + i: i for i in range(10)}, **{65 + i: i + 10 for i in range(6)}}


def decode(message: bytes) -> bytes:
    line, sep, tail = message.partition(b"\r\n")
    if not sep or not line or len(message) > 4096:
        raise ValueError("invalid")
    size = 0
    for byte in line.upper():
        if byte not in _HEX or size > (2**64 - 1 - _HEX[byte]) // 16:
            raise ValueError("invalid")
        size = size * 16 + _HEX[byte]
    if tail[size:] != b"\r\n0\r\n\r\n":
        raise ValueError("invalid")
    return tail[:size]
