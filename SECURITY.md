# Security policy

MNCS 0.1 and `mncs-validator` 0.1.x receive security fixes. Report validator path
escape, hash confusion, schema bypass, unsafe execution, dependency, or release
integrity issues privately through GitHub's security advisory interface. Do not open
a public exploit issue before coordination.

Include affected version, impact, minimal reproduction, and suggested mitigation.
Maintainers aim to acknowledge within 7 days, assess within 14 days, and coordinate a
fix and disclosure. These are goals, not guarantees.

The validator is designed to operate offline and never execute evidence. A bundle
should still be treated as untrusted input. Conformance is not a security warranty.
Research repository or generated-candidate vulnerabilities belong to their owning
projects unless they expose an MNCS specification or validator defect.
