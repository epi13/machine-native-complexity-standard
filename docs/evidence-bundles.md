# Evidence bundles

An evidence bundle contains `specification/`, `reference/`, `machine/`, `evidence/`,
`provenance/`, `manifest.json`, and `README.md`.

Freeze evidence before hashing. The manifest hashes its index; the index hashes every
record. Direct manifest references also carry hashes. This deliberate redundancy
makes missing, substituted, and stale evidence obvious.

Keep evidence compact and redistributable. Exclude credentials, private absolute
paths, raw paid transcripts, caches, and giant analyzer dumps. Prefer a bounded
witness with exact source identity over a full graph export.
