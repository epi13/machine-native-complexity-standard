# Rust interoperability

`epi13/mncs-validator-rs` is an independent Rust validator; it does not invoke or embed
the Python implementation. Both implementations consume a pinned corpus and compare
canonical bytes, signature decisions, trust decisions, package integrity, schema
status, provider results, and PASS/FAIL/UNKNOWN outcomes.

The agreement report is machine-readable. Unsupported features remain explicit and
cannot be normalized into PASS. Both validators operate offline and never execute
evidence binaries.
