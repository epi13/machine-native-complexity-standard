# Architecture

MNCS requires two layers.

## Human control layer

The human control layer MUST contain a readable:

1. functional contract and public interface;
2. state and error model;
3. input assumptions and resource bounds;
4. reference implementation or executable oracle;
5. declared optimization objective, fixed before generation;
6. safety, security, and portability requirements;
7. acceptance policy;
8. regeneration procedure; and
9. rollback strategy.

The reference need not be fast, but it MUST be independently understandable and
available without the machine implementation.

## Machine execution layer

The machine execution layer MUST identify:

1. the generated or machine-optimized implementation;
2. a generated-file marker;
3. source and artifact hashes;
4. generator and evaluator provenance;
5. a content-addressed evidence bundle;
6. a conformance declaration;
7. unsupported environments; and
8. proof or attestation that no undeclared handwritten changes occurred after
   certification.

The canonical source header is:

```text
MNCS-GENERATED: DO NOT EDIT
MNCS-Version: 0.1
Manifest: <bundle-relative path or content hash>
Generator: <identity and locked version>
Regenerate: <documented command identifier>
```

The language comment prefix MAY be added to every line. A handwritten change
invalidates the certified source hash and MUST trigger regeneration and reevaluation.
