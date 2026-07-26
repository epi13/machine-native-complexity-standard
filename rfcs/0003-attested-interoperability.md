# RFC 0003: Attested Interoperability

- Status: Accepted
- MNCS version: 0.2
- Schema version: 0.2
- Validator version: 0.2.0

## Summary

MNCS 0.2 turns evidence-derived conformance into a portable interoperability system.
Schema 0.1.1 established that a validator, rather than a manifest author, derives
acceptance. That is necessary but insufficient when evidence moves between machines
and organizations: consumers also need byte-stable identities, proof that a key signed
those bytes, an explicit local trust decision, and an archive that reproduces exactly.

This RFC standardizes RFC 8785 canonical JSON, Ed25519 DSSE-compatible envelopes,
deterministic trust policies, reproducible `.mncs` packages, Provider Protocol 0.1,
versioned vectors, and independent Python/Rust validation.

## Security and assurance model

A signature proves only that the holder of a private key signed particular bytes. It
does not prove that the signer is honest, that evidence is correct, that software is
safe, or that a performance claim is reproducible. Cryptographic validity and local
trust are separate reported outcomes. A valid signature from an untrusted, expired,
or revoked key does not certify evidence. A trusted signature bound to another subject,
contract, component, or environment does not count.

Verification is offline and does not execute evidence. Trust roots, revocations, time,
scope, roles, thresholds, and UNKNOWN handling come exclusively from the supplied
policy. Extensions are namespaced and cannot redefine core fields or broaden trust.

## Canonical representation

All signed JSON payloads and identities use RFC 8785 JSON Canonicalization Scheme
semantics: strict UTF-8 JSON, duplicate-key rejection, ECMAScript number serialization,
lexicographic UTF-16 property ordering, minimal required escaping, no Unicode
normalization, and rejection of NaN and infinities. Negative zero serializes as `0`.
Integers outside the interoperable IEEE-754 range and numbers not representable under
the JCS model are rejected. SHA-256 is lowercase hexadecimal; contexts that use the
existing MNCS identity syntax prefix it with `sha256:`.

## Attestations and key lifecycle

An envelope uses the DSSE pre-authentication encoding and binds the payload type to
canonical statement bytes. The statement binds subjects, contract, component,
MNCS/schema versions, environment, predicate type and body, creation time, optional
expiration, and namespaced extensions. Required predicates cover conformance, gates,
evidence indexes, packages, provider results, and release artifacts. Multiple unique
Ed25519 signatures are supported.

Key IDs are `sha256:` plus the digest of the raw 32-byte Ed25519 public key. Rotation
adds a new key record and overlap window; it never changes an old key ID. Revocation is
effective at its recorded time. Expiration applies independently to keys and
attestations. Offline consumers receive all applicable public keys and revocation
records with the policy. Envelopes can later be logged as immutable blobs; a future
transparency profile may add inclusion proofs without changing signed payload bytes.

## Deterministic trust

A policy names one trust domain, trusted public key records, signer roles, predicate,
component, contract and environment scopes, validity windows, revocations, signature
and distinct-signer thresholds, independent evaluator count, optional
generator/evaluator separation, and explicit UNKNOWN behavior. Evaluation is a pure
function of the envelope, policy, expected bindings, and evaluation time. Generator
and evaluator roles must come from different key IDs when separation is required.

## Reproducible packages

`.mncs` is a ZIP archive using stored entries, UTF-8 canonical relative POSIX paths,
bytewise path ordering, fixed 1980-01-01 timestamps, regular-file mode `0644`, no
directory entries, and a canonical `mncs-package-index.json`. The index records each
non-index file's path, size, and SHA-256 and binds `evidence/index.json` when present.
Ownership is absent from ZIP and therefore normalized by omission.

Validators reject absolute paths, `..`, backslashes, duplicate names, links, devices,
FIFOs, excessive nesting, too many files, oversized members, excessive aggregate size,
index/member disagreement, and extraction escapes. Packing reads stable regular files
through no-follow descriptors. Validation never imports or executes archive contents.

## Provider Protocol 0.1

Providers exchange exactly one newline-terminated canonical JSON object on stdin and
stdout. Messages negotiate protocol version and support capabilities, health,
analysis, cancellation, PASS/FAIL/UNKNOWN, compact witnesses, unsupported requests,
and structured errors. Normal MNCS validation never launches a provider.

Explicit provider execution passes an argument vector directly without a shell, uses a
dedicated workspace, bounds runtime/stdout/stderr, rejects nonprotocol stdout, and
terminates the provider process group on timeout. The implementation does not claim
network isolation; callers requiring it must apply an external sandbox.

## Interoperability and migration

The Python implementation and independent Rust implementation consume a pinned,
versioned corpus and compare normalized semantic results. Unsupported behavior is
reported as unsupported, never PASS. Schemas 0.1 and 0.1.1 remain supported.

Migration creates a new 0.2 manifest/evidence graph and optional attestation referencing
historical hashes; it does not edit historical records and does not make legacy
evidence signed retroactively.

## Rejected alternatives

- “Sorted JSON” was rejected because number formatting, UTF-16 ordering, escaping,
  duplicate keys, and negative zero remain ambiguous.
- Embedded self-signed keys were rejected because cryptographic validity is not trust.
- A Python-backed Rust wrapper was rejected because it cannot expose implementation
  disagreement.
- Executing evidence during validation was rejected because it expands the trust
  boundary and violates offline inspection.
- Tar with platform metadata was rejected for 0.2 in favor of a smaller deterministic
  ZIP profile; future formats require a versioned profile.
- Mandatory Sigstore or a transparency service was rejected because baseline offline
  verification must work without a network.

## Residual risks

Compromised trusted keys, dishonest evaluators, weak trust policy, filesystem races
outside stable reads, decompressor/library defects, denial-of-service below configured
limits, unavailable revocation updates during prolonged offline use, and providers
with ambient network access remain possible. MNCS is open, experimental,
community-developed, tool-neutral, non-accredited, and makes no blanket safety claim.
