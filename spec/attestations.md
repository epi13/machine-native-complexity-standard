# Normative attestations and trust

The payload type is
`application/vnd.mncs.attestation-statement.v0.2+json`. The payload is base64 of the
canonical statement. Signatures cover DSSE PAE:
`DSSEv1 SP len(type) SP type SP len(payload) SP payload`.

The statement binds subject SHA-256 digests, contract, component identity,
environment, MNCS/schema versions, predicate type/body, creation, optional expiration,
and extensions. Signatures use Ed25519 and stable public-key IDs. Duplicate signatures
from one key are invalid.

Trust evaluation MUST apply key validity, revocation, predicate/component/contract/
environment scope, minimum signatures, distinct signers, required roles, independent
evaluators, generator/evaluator separation, attestation expiration, and explicit
UNKNOWN behavior. It MUST report cryptographic validity independently of trust and
certification.
