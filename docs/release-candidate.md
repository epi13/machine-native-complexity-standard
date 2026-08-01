# MNCS 0.3 / MNCDS 0.1 release candidate

MNCS 0.3-rc.1 is the controlled-system-assurance proposal. It keeps MNCS 0.2
identities, trust, attestations, packages, and implementation evidence while adding
contract adequacy, claim/dependency composition, correlated failures, freshness,
material change, evidence impact, revalidation, supersession, replacement, rollback,
retirement, and migration.

MNCDS 0.1-rc.1 is the stable-format development-process proposal. Its offline
aggregate binds charter, baseline, environment, roles, authority overlap, partitions,
protected evidence, generator, evaluators, candidate ledger/lineage, selection,
reproducibility, recursive epochs, MNCS result, and D4 lifecycle controls.

The specifications are `spec/MNCS-v0.3-rc.1.md` and
`spec/MNCDS-v0.1-rc.1.md`. RFC 0004 and RFC 0005 remain Draft, so these are neither
Accepted nor Final.

## Discover and validate

```console
mncs version --json
mncs schema contract-profile-0.3
mncs schema assurance-case-0.3
mncs schema threat-record-0.3
mncs schema measurement-profile-0.3
mncs schema mncds-development-record-0.1

mncs validate-record contract examples/release-candidate-0.3/contract-profile.json
mncs validate-record assurance examples/release-candidate-0.3/assurance-case.json
mncs validate-record threat examples/release-candidate-0.3/threat-record.json
mncs validate-record measurement examples/release-candidate-0.3/measurement-profile.json
mncds validate examples/mncds-0.1-rc/development-record.json --json

mncs migration-inspect examples/minimal/manifest.json --json
mncs corpus release-candidate --json
PYTHONPATH=src ./scripts/compare-release-candidate-consumers --json
cargo run --manifest-path independent/rc-consumer/Cargo.toml -- conformance --json
cargo run --manifest-path independent/rc-consumer/Cargo.toml -- \
  validate-record --kind assurance \
  --input examples/release-candidate-0.3/assurance-case.json \
  --at 2026-08-01T00:00:00Z --json
cargo run --manifest-path independent/rc-consumer/Cargo.toml -- \
  validate-package --input bundle.mncs --json
cargo run --manifest-path independent/rc-consumer/Cargo.toml -- \
  validate-attestation --envelope attestation.json --policy trust-policy.json \
  --at 2026-08-01T00:00:00Z --json
make release-candidate-check
```

Exit 4 means a distinct unsupported version. Ordinary validation is offline and
executes no provider, analyzer, generator, candidate, compiler, benchmark, service, or
evidence binary. Provider execution remains an explicit separate command.

## Evidence boundary

The Python and separate Rust consumers retain agreement on the original 72 golden
vectors and agree on two added transitive graph-impact vectors (74/74 total). The Rust
CLI also validates arbitrary bounded contract, assurance, threat, measurement, and
MNCDS records in its declared subset, including RFC 3339 numeric offsets. It also
performs bounded `mncs-zip-0.1` package validation, DSSE PAE and Ed25519 verification,
and deterministic offline trust-policy evaluation. Cross-consumer tests cover valid,
tampered, unsafe-path, symlink, binding, signature, expiration, and revocation cases.
This proves separate source and executable decision paths for the tested subset. It
does not prove independent operation or organizational independence.

The two-epoch study reduces final incorrect PASS from 3 to 0 and false negatives from
2 to 0 without false-positive, crash, or timeout regression. Its final partition was
developer-withheld until tool freeze, not externally protected. Internal selection is
PASS; the MNCS and MNCDS assurance results remain UNKNOWN.

The [gap matrix](release-gap-matrix.md), [security/privacy review](release-candidate-security-privacy-review.md),
[migration model](migration-0.2-to-0.3-mncds-0.1.md), [known limitations](release-candidate-known-limitations.md),
and [evidence index](release-candidate-evidence-index.md) define what remains.
