# Experimental execution challenges and replay evidence

`mncs-execution-challenge` `0.1-experimental` is the freshness layer around the
runner-produced execution receipt. A verifier issues a cryptographically random,
single-use nonce bound to the subject, candidate, immutable bundle, execution policy,
and optional runner constraint. The runner copies the challenge observations into its
receipt; a local replay store explicitly consumes the challenge once.

This profile is experimental and non-normative. It records freshness within a declared
local replay-store boundary. It does not establish correctness, isolation, host-root
resistance, protected custody, independent operation, attestation authority,
MNCS/MNCDS conformance, certification, governance approval, release authorization, or
promotion.

## Records and identities

The challenge, execution receipt, and replay receipt have separate canonical SHA-256
identities. A challenge identity covers every material challenge field except
`challenge_identity`, including its nonce, validity window, issuer identity, and scope.
`replay_identity` covers the replay receipt except its own identity. The local ledger
stores only a digest of the nonce, not the plaintext nonce.

The challenge scope is compared exactly against receipt facts:

```text
subject + candidate + bundle + execution policy + optional runner constraint
       + nonce + issued_at + expires_at
```

Missing or substituted scope is invalid. A null runner constraint means that the
challenge does not constrain the runner identity; it does not mean that runner identity
is unknown or trusted.

## Explicit operations

Issuance and consumption are separate from non-mutating validation:

```bash
mncs challenge issue request.json --output challenge.json --json
mncs challenge validate challenge.json --json
mncs replay consume challenge.json receipt.json \
  --store .mncs/replay-store --output replay-receipt.json --json
mncs replay verify replay-receipt.json \
  --challenge challenge.json --receipt receipt.json --json
```

`challenge validate`, receipt validation, and replay verification do not mutate a
store. Only the explicit `replay consume` operation writes replay state. An existing
receipt can also be checked with `mncs validate-execution-receipt --challenge ...`
and `--replay-receipt ...`; those optional checks preserve backward compatibility.

## Local replay store boundary

The reference `ReplayStore` uses a bounded append-by-replacement canonical JSON Lines
ledger, a crash-safe state watermark, and an exclusive lock with stale-lock recovery.
Each entry binds its sequence, previous entry identity, challenge digest, receipt
identity, scope, consumption time, and monotonic time watermark. Corrupt, truncated,
future-version, missing-state, duplicate, or broken-chain data fails closed.

The persisted watermark is the maximum observed local verification time. If the wall
clock moves backward after a later time has been observed, effective verification time
does not move backward. A forward clock observation remains persisted even when it
causes a challenge to expire, so rolling the wall clock back cannot revive it.

This is local replay detection, not tamper resistance. A host administrator who can
replace or delete the replay directory remains inside the local trusted computing base.
An offline replay receipt can establish internal consistency and store linkage when the
store is supplied; it cannot establish external custody or witnessing.

## Relationship to other layers

```text
immutable execution bundle
          |
fresh scoped challenge
          |
runner-produced execution receipt
          |
explicit local replay consumption
          |
offline replay receipt
          |
execution assurance interpretation
```

Freshness is independent of the functional test result, placement evidence, execution
isolation, and conformance. A functional `PASS` plus freshness `PASS` can still produce
execution assurance `UNKNOWN` when required isolation, custody, or authority evidence
is absent. The `FAIL > UNKNOWN > PASS` ordering remains applicable when formal status
aggregation is performed.

Forge, MNEL, future Fabric executors, and local runners can consume the challenge and
emit the existing receipt without importing this replay store. Commons may transport
the records but does not become their issuer or replay authority. RAVEL may retain
challenge and replay identities in episodes, but may not rewrite raw records or turn
repeated local freshness into independence. MNCS Language identities may be placed in
the opaque subject or candidate scope without coupling the challenge to a language.

The generic reference request and 40-case adversarial index are under
`experimental/execution-challenge/fixtures/`. The complete local chain is exercised
by the deterministic challenge tests while retaining `UNKNOWN` for assurance claims
that freshness alone cannot establish.
