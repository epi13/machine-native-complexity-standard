# Canonicalization

MNCS 0.2 signs and hashes RFC 8785 canonical JSON bytes. This specifies far more than
sorting keys: duplicate keys and nonfinite values are errors, object ordering follows
UTF-16 code units, numbers follow ECMAScript/JCS serialization, negative zero becomes
`0`, strings are UTF-8 without Unicode normalization, and output contains no optional
whitespace.

Use `mncs canonicalize FILE` to inspect bytes. The interoperability vectors record
input, expected bytes/hex, SHA-256, and both implementation outcomes.
