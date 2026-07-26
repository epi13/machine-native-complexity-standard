# Machine-Native Complexity Standard 0.2

MNCS 0.2 is an open, experimental, community-developed, tool-neutral, non-accredited
standard for evidence-based acceptance of machine-native implementations. Normative
terms use RFC 2119 meanings as described in `normative-language.md`.

An MNCS 0.2 implementation MUST preserve PASS, FAIL, and UNKNOWN; MUST derive
conformance from bound evidence; MUST support schemas 0.1 and 0.1.1 as legacy inputs;
MUST validate offline without executing evidence; and MUST distinguish validation,
conformance, package integrity, signature validity, trust, and certification.

Canonical JSON MUST follow `canonicalization.md`. Attestations MUST use canonical
statements and DSSE pre-authentication encoding with Ed25519 as the baseline algorithm.
Trust MUST be determined only by an explicit policy and expected subject, contract,
component, and environment bindings. A signature alone MUST NOT imply trust.

Packages MUST follow `reproducible-package.md`. Providers MUST follow Provider Protocol
0.1 and MUST be run only by an explicit provider command. Implementations MUST enforce
documented resource limits and MUST NOT report unsupported operations as PASS.

Independent implementations SHOULD run the versioned interoperability corpus and
publish a normalized agreement report. Extensions MUST use namespaced keys and MUST
NOT shadow or broaden core semantics.

Cryptography authenticates bytes and keys, not correctness or truth. Conformance
remains scoped to the declared contract, environment, evidence, policy, and identities.
