# MNCS repository organization contract

This document defines the family-wide layout vocabulary. It is a convention
for bounded discovery and human navigation, not a requirement to create every
directory in every repository.

The existing `mncs-family.repository-manifest/v0alpha1` contract remains the
only family repository-manifest format. Its optional `organization` object
uses `mncs.repository-layout/1` for the few paths whose role cannot be safely
derived from ordinary repository structure or authoritative family facts.
Manifest declarations should stay small: do not repeat language capabilities,
family ownership, pressure lifecycle, or generated status already owned by
`mncs-language`, Commons, or the owning repository.

## Predictable surfaces

When a repository has the corresponding material, prefer these human-readable
paths:

| Surface | Meaning |
| --- | --- |
| `src/` or the repository's established source root | canonical implementation source |
| `tests/` | executable tests and conformance evidence |
| `docs/` | human-facing architecture and usage explanation |
| `rfcs/` | durable human-readable design proposals and decisions |
| `examples/` | executable probes and teaching programs |
| `fixtures/` | bounded input/output corpora and adversarial cases |
| `generated/` or a clearly marked generated file | deterministic projection; never hand-authored authority |
| `reference/`, `oracle/`, or `mncs-reference-studies` | differential/reference material that must not become canonical |
| `migration/` or `shadow/` | active migration material with an explicit retirement condition |
| `historical/` | retained historical artifacts that are not current authority |

Repositories may use an established language-specific layout such as
`native/mncs/`, `library/`, `crates/`, or `mncs/`. The classification is about
authority and lifecycle, not the spelling of the directory.

## Orthogonal machine dimensions

The legacy `class` field remains accepted for v0alpha1 compatibility, but it
is intentionally not the whole classification. New or audited surfaces may
add `classification` with four independent dimensions:

- `authority`: `canonical`, `compatibility`, `reference`, or `none`;
- `lifecycle`: `active`, `temporary`, `retired`, `generated`, or `historical`;
- `boundary_kind`: `none`, `platform`, `filesystem`, `process`, `protocol`,
  `compiler-bootstrap`, or `external-provider`;
- `semantic_role`: `canonical-semantic`, `canonical-host-semantic`, `host-bootstrap`, `platform-adapter`,
  `temporary-host-semantic`, `migration-shadow`, `differential-oracle`,
  `compatibility-adapter`, `reference`, `generated`, or `historical`.

This lets an agent distinguish a Rust compiler bootstrap from a Python
semantic workaround, even when both are host-language source. A source path
is not a host boundary merely because of the language in which it is written.

## Artifact classes

Every significant non-obvious surface should be classifiable as one of:

- `canonical`: current semantic authority for the repository's capability;
- `host-boundary`: compiler/runtime/bootstrap, platform, filesystem/process/
  network transport, or another explicit external boundary;
- `compatibility`: a protocol or adapter retained for an external consumer;
- `differential-oracle`: an independent comparison implementation or witness;
- `reference`: explanatory or research implementation, not production
  authority;
- `migration-shadow`: native or replacement implementation being compared
  against a current host path;
- `generated`: reproducible output derived from authoritative state;
- `historical`: retained context with no current authority.

`organization.surfaces` is for explicit exceptions and boundaries. Ordinary
`src/`, `tests/`, and `docs/` directories need no manifest entry. A surface
classified as `generated` must also identify a deterministic input through
`organization.generated_regions` or an owning repository contract.

Doctor validates declared generated regions structurally (target existence and
marker order) and, when current language/Commons identities are available,
checks identity-bearing context sections for stale claims. A projection
generator remains responsible for byte-level `--check` comparison; Doctor does
not execute an arbitrary command embedded in a repository manifest.

## Authority boundaries

The organization convention does not transfer semantics:

- `mncs-language` owns language and compiler capability truth;
- MNCS Standard owns this manifest schema and its conformance meaning;
- MNCDS owns development-process obligations and pressure semantics;
- Commons owns family pressure lifecycle and architecture/convergence facts;
- repository owners own their implementations and repository-local contracts;
- Language Service may compose bounded read-only context but does not own
  sibling facts;
- Atlas may render and index family orientation but is non-normative;
- Doctor validates freshness, drift, and conformance without becoming a
  sibling semantic authority.

Doctor and Atlas may report a missing or stale manifest. They must not silently
invent one or treat a central snapshot as fresher than an available local
`.mncs/project.json`. Central snapshots remain valid as explicit
reproducibility/bootstrap inputs.
