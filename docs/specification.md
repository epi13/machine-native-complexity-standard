# MNCS 0.2 specification

The normative specification is maintained in
[`spec/MNCS-v0.2.md`](https://github.com/epi13/machine-native-complexity-standard/blob/main/spec/MNCS-v0.2.md)
with its linked modules. The repository
copy, release tag, and manifest schema together identify the experimental 0.2
standard.

Version 0.2 retains evidence-derived gates and adds RFC 8785 identities, Ed25519
DSSE-compatible attestations, deterministic local trust, reproducible `.mncs`
packages, Provider Protocol 0.1, and independent Python/Rust corpus agreement.
Frozen schemas 0.1 and 0.1.1 remain available for legacy validation.

Key requirements remain cumulative levels, content-addressed evidence, three-valued
results, predeclared benefit, provider neutrality, regeneration, and rollback.
Cryptography authenticates bytes and keys, not correctness or truth. The
specification is licensed Apache-2.0.

MNCS remains experimental. A validator PASS is scoped to the declared contract and
environment and is not accredited certification.

MNCS 0.3-rc.1 is a separate release-candidate proposal under Draft RFC 0005. It
does not overwrite this frozen 0.2 specification. A 0.2 claim remains 0.2 unless it is
reevaluated under the 0.3 rules and receives the required new identities.
