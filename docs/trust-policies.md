# Trust policies

A policy supplies the entire offline trust context: domain, Ed25519 public keys, roles,
scopes, validity windows, revocations, predicate allowlist, signature and distinct-key
thresholds, independent evaluators, generator/evaluator separation, and UNKNOWN
handling.

```bash
mncs trust validate-policy policy.json
mncs trust evaluate attestation.json policy.json --subject sha256:... --json
mncs certify-bundle component --trust-policy policy.json --attestation attestation.json
```

Cryptographic validity, trust, and certification are reported separately. Unknown
extensions never add keys, roles, scopes, or threshold credit.
