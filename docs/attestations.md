# Attestations

Generate a private key only at an explicit path:

```bash
mncs key generate keys/release.pem
mncs key inspect keys/release.pem.pub.json --json
mncs attest statement.json --key keys/release.pem --output attestation.json
mncs verify-attestation attestation.json --key keys/release.pem.pub.json --json
```

Private keys are mode 0600 where supported, are never uploaded, and must not be placed
in bundles. Verification reports canonical payload validity, signature validity, and
expiration. Trust is a separate operation. A signature authenticates bytes; it does not
prove correctness, safety, performance, or truth.
