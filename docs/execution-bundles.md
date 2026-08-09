# Experimental immutable execution bundles

`mncs-execution-bundle` `0.1-experimental` is the EA-NEXT-002 package beneath a
runner-produced execution receipt. It freezes bounded tests, harnesses, expected
material, runtime requirements, policy references, fixtures, and inputs without
making a correctness, sandbox, custody, independence, conformance, or promotion
claim.

## Two identities

The manifest has a logical `bundle_identity`: the lowercase canonical SHA-256 of
the complete manifest with only `bundle_identity` removed. The deterministic ZIP
transport has a separate `archive_identity`, the `sha256:`-prefixed SHA-256 of its
exact bytes. A future transport may preserve the logical identity while changing
the archive identity; a changed material path, role, mode, requirement, policy,
entrypoint, or content must change the logical identity.

The reference builder sorts UTF-8 paths, uses fixed timestamps and regular-file
modes, stores canonical JSON, refuses overwrite, and does not include host-local
paths or ambient metadata.

## Bounded verification

Offline verification does not extract or execute a bundle. It rejects traversal,
absolute, drive-letter, UNC, backslash, NUL, non-NFC, duplicate, case-colliding,
symlink, hardlink, directory, and special-file entries. It also bounds member
count, member and total size, archive size, streamed bytes, and compression
expansion. The manifest, archive member list, file sizes, modes, content hashes,
references, and both identity projections must agree.

```bash
mncs schema execution-bundle --json
mncs bundle create --manifest source.json --source bundle-src --output test-bundle.zip --json
mncs bundle verify test-bundle.zip --json
mncs validate-execution-receipt receipt.json --bundle test-bundle.zip --json
```

The `--bundle` receipt path is optional for backward compatibility. When supplied,
the archive must verify and its logical identity, harness identity, input identity,
and referenced policy identity must match the receipt. A receipt cannot make an
unverified archive valid, and a verified bundle does not prove that a runner used
it; the receipt is the observation that binds execution to the bundle.

## Project-family relationship

Wave Five's deterministic portable-evaluator ZIP informed this profile but remains
historical frozen evidence; it is not retroactively relabeled EA-NEXT-002. Commons
Bundles share bounded canonical identity principles but transport records/knowledge
and are not execution bundles. Forge can later feed a verified bundle to its local
runner, MNEL can bind provider snapshots and placement observations to one, GIMP
Local MCP can bind its worker/input material to one, and a future Fabric executor
can emit a receipt after consuming one. RAVEL may reference bundle identities in
immutable experience records but cannot rewrite them or promote repeated use.

The next layer, EA-NEXT-003, is the isolation runner. Bundle integrity is not
filesystem, network, process, host-root, protected-custody, or independent-operation
assurance.
