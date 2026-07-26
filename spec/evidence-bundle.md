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
