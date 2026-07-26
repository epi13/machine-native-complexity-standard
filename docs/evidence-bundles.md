# Evidence bundles

An evidence bundle contains `specification/`, `reference/`, `machine/`, `evidence/`,
`provenance/`, `manifest.json`, and `README.md`.

Freeze evidence before hashing. The manifest hashes its index; the index hashes every
record. Direct manifest references also carry hashes. This deliberate redundancy
makes missing, substituted, and stale evidence obvious.

Keep evidence compact and redistributable. Exclude credentials, private absolute
paths, raw paid transcripts, caches, and giant analyzer dumps. Prefer a bounded
witness with exact source identity over a full graph export.
In schema 0.1.1, `evidence/index.json` is an authoritative graph rather than a
decorative inventory. Manifest fields and evidence records refer to stable IDs.
Each index node binds its kind, relative path, SHA-256 identity, media type,
contract, and candidate when applicable.

The validator rejects duplicate IDs, conflicting hashes for one path, missing
references, stale source/contract binding, traversal, symlink evidence, and
non-regular files. It reports unreachable nodes according to the declared warn or
reject policy. Evidence is read and hashed only; it is never executed.
