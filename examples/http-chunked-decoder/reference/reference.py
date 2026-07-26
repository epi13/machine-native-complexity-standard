# SPDX-License-Identifier: Apache-2.0


def decode(message: bytes) -> bytes:
    """Readable oracle for the example's deliberately bounded grammar."""

    size_line, rest = message.split(b"\r\n", 1)
    size = int(size_line, 16)
    payload, ending = rest[:size], rest[size:]
    if len(payload) != size or ending != b"\r\n0\r\n\r\n":
        raise ValueError("invalid chunk framing")
    return payload
