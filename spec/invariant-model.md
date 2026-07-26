# Invariant model

An invariant states a semantic requirement, not a tool invocation. Its result MUST
contain:

- invariant ID and requirement;
- certified source hash;
- PASS, FAIL, or UNKNOWN;
- provider and provider version;
- analysis method;
- assumptions and boundedness;
- witness or evidence reference when available;
- source locations;
- elapsed time and output size; and
- limitations.

A tool name never substitutes for these semantics. Absence of a reported path is
insufficient for PASS unless the method and model justify the conclusion. Tool
failure, unsupported syntax, truncated exploration, and frontend ambiguity are
UNKNOWN unless evidence positively establishes a violation.
