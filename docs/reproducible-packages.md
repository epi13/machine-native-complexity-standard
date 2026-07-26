# Reproducible packages

```bash
mncs pack component --output component.mncs
mncs inspect-package component.mncs --json
mncs verify-package component.mncs --json
mncs unpack component.mncs --output extracted
mncs certify-package component.mncs
```

The package uses the deterministic `mncs-zip-0.1` profile and a canonical index. Two
packs of stable identical input produce identical bytes. Verification is bounded,
offline, and non-executing. Unsafe paths, links, special files, duplicates, archive
bombs, and index/hash mismatches are rejected before extraction.
