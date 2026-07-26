# Normative canonical JSON

MNCS canonical JSON is RFC 8785 JCS. Input MUST be UTF-8 JSON and MUST reject duplicate
object keys, byte-order marks, lone surrogates, NaN, positive/negative infinity, and
values outside the interoperable JCS numeric domain.

Strings are emitted as UTF-8 with JSON escaping required by RFC 8785; Unicode is not
normalized. Object property names are ordered lexicographically by their UTF-16 code
units. Arrays retain order. Numbers use the ECMAScript shortest round-tripping
serialization required by JCS; negative zero emits `0`, exponent spelling is
normalized, and integers beyond the exact binary64 safe range are rejected rather than
silently rounded.

Canonical output has no insignificant whitespace or trailing newline. A canonical
identity is SHA-256 over exactly those bytes and is rendered as 64 lowercase
hexadecimal digits. Existing MNCS evidence references use `sha256:` followed by that
digest.
