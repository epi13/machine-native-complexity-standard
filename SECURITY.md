# Security policy

MNCS 0.2 and `mncs-validator` 0.2.x receive security fixes. Report validator path
escape, hash confusion, schema bypass, unsafe execution, dependency, or release
integrity issues privately through GitHub's security advisory interface. Do not open
a public exploit issue before coordination.

Include affected version, impact, minimal reproduction, and suggested mitigation.
Maintainers aim to acknowledge within 7 days, assess within 14 days, and coordinate a
fix and disclosure. These are goals, not guarantees.

The validator is designed to operate offline and never execute evidence. It rejects
duplicate keys, nonfinite and unsafe JCS numbers, signature/algorithm confusion,
stale bindings, expired/revoked keys, threshold failures, extension shadowing,
unsafe archive paths and types, archive bombs, and provider framing/timeout failures.
A bundle should still be treated as untrusted input. Conformance is not a security
warranty. Provider execution is explicit and bounded but does not claim network
isolation.
Research repository or generated-candidate vulnerabilities belong to their owning
projects unless they expose an MNCS specification or validator defect.
