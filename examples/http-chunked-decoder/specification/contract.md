# Bounded chunk decoder contract

Accept one complete ASCII chunk `HEXSIZE\r\nPAYLOAD\r\n0\r\n\r\n`. Reject malformed
framing, non-hex sizes, overflow beyond 64 bits, or length mismatch. Return payload
only after the complete framing is valid. Maximum input is 4096 bytes.
