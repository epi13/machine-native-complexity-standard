# Normative `.mncs` package profile

The 0.2 package profile is `mncs-zip-0.1`. It uses ZIP stored entries, UTF-8 relative
POSIX paths sorted by path bytes, fixed 1980-01-01 00:00:00 timestamps, regular-file
mode 0644, no directory entries, and no owner metadata. A canonical
`mncs-package-index.json` records every other member's path, byte size, and SHA-256 and
the embedded evidence-index identity when present.

Readers MUST reject duplicate, absolute, dot, parent, backslash, over-nested, linked,
special, oversized, or unindexed members and total/file-count limit violations.
Extraction MUST occur only after verification and MUST prevent path and symlink escape.
