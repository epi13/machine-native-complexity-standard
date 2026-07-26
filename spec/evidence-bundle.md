# Evidence bundle

The canonical layout is:

```text
component/
  specification/
  reference/
  machine/
  evidence/
  provenance/
  manifest.json
  README.md
```

Every evidence record MUST be content-addressed with lowercase SHA-256 in
`sha256:<hex>` form. Paths MUST be relative, MUST remain inside the bundle, and MUST
resolve without network access. An index record identifies its stable ID, evidence
kind, path, hash, media type, and optional description.

The validator MUST treat a missing file, path traversal, malformed record, duplicate
ID, or hash mismatch as bundle failure. It MUST NOT import or execute evidence.
For schema 0.1.1 the evidence index is the authoritative graph. Every manifest
evidence ID MUST exist exactly once. A record binds ID, kind, relative path,
SHA-256, media type, contract, and candidate source where applicable. One path
under conflicting hashes, duplicate IDs, unindexed required evidence, path escape,
and symlink evidence are invalid.

Gate, invariant, performance, provenance, and identity records MAY refer only to
indexed IDs. Validators MUST report reachable dependencies and MUST warn or reject
unreachable indexed evidence according to policy. Validators MUST NOT execute,
import, or fetch evidence.

Ordinary files are bounded by local validator resource policy. The reference
validator rejects non-regular evidence and files over 10 MiB and caps an index at
2,000 records.
