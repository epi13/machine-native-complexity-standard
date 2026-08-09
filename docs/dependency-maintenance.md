# Dependency maintenance boundary

The repository reconciles dependency updates against the current workflow and
portability contract rather than merging stale Dependabot branches unchanged.

- GitHub Actions now use checkout/setup-python/setup-go major 7, download-artifact
  major 8, and the exact `upload-artifact@v7.0.1` release already used by the
  repository. Keeping the exact upload tag avoids replacing an existing pinned
  `v7.0.1` usage with a less specific `v7` reference.
- Ruff is pinned to 0.16.0 and remains covered by the explicit `E F I B UP SIM RUF`
  lint boundary and formatter checks.
- `cryptography` remains `>=43,<47`. The proposed 49 release removes x86_64 macOS
  and 32-bit Windows support. MNCS still exercises and documents macOS/Windows
  portability, so accepting that update without an architecture policy and an
  installed-package matrix would silently narrow the supported environment.

This is a compatibility decision, not a security exemption. Revisit the bound when
the supported-platform policy and CI matrix can carry the change truthfully.
