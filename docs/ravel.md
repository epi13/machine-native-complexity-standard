# RAVEL research architecture

RAVEL (Recursive Adaptive Vector Execution Lattice) is an MNCS research architecture that treats routing, retrieval, model storage, training state, and computational allocation as one bounded machine-native structure.

The project currently contains two mechanism studies:

- **RAVEL 0.1** demonstrates exact conditional inference over a generated expert lattice. A lower-bound certificate permits reduced computation only when the routed result is provably identical to a full scan.
- **RAVEL-T 0.2** extends the lattice into recursive training. Current experts generate the router; the router creates exact training shards; error-heavy shards compile into child experts; child lineage regenerates the next router.

The initial RAVEL-T synthetic study grew from eight to 64 experts through 56 deterministic births. It matched a flat 64-expert baseline's holdout accuracy while using 4,144,248 training expert evaluations rather than 87,031,808, and its routed holdout results agreed exactly with the full-scan oracle.

These are repository-visible development observations, not claims of real-data or foundation-model superiority. The task is deliberately favorable, the holdout is not independently protected, and formal MNCS and MNCDS status remain `UNKNOWN`.

See the [RAVEL case-study directory](../case-studies/ravel/README.md) for source, contracts, preregistration, evidence, threat model, and assurance record.
