# Conformance manifest

`manifest.json` is the root of a claim. It identifies the MNCS and schema versions,
claimed level, component and contract, reference and machine identities, generator,
predeclared objective, acceptance policy, environment, evidence index, invariants,
complexity profile, performance results, resource bounds, provenance, limitations,
unsupported environments, regeneration, rollback, and final status.

Core field meanings are fixed by MNCS. Extensions live under `extensions` and MUST
use a namespace-qualified key such as `example.org:energy-model`. Validators MUST
preserve unknown extension namespaces when rewriting documents, but extensions MUST
NOT change core status, gate, hash, or level semantics.
