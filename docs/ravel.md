# RAVEL research architecture

RAVEL (Recursive Adaptive Vector Execution Lattice) is an MNCS research architecture that treats routing, retrieval, compression, representation, training state, temporal memory, planning, lifecycle, and computational allocation as one bounded machine-native structure.

The repository contains three cumulative mechanism studies:

- **RAVEL 0.1** demonstrates exact conditional inference over a generated expert lattice. A lower-bound certificate permits reduced computation only when the routed result is provably identical to a full scan.
- **RAVEL-T 0.2** extends the lattice into recursive training. Current experts generate the router; the router creates exact training shards; error-heavy shards compile into child experts; child lineage regenerates the next router.
- **RAVEL-U 0.3** turns the expert into a unified executable memory unit: retrieval key, compressed representation, decoder, classifier, action-conditioned predictor, transition-memory node, planning destination, replay shard, lifecycle object, and compute unit.

In the RAVEL-U synthetic study, the frozen model scored 71.899% after semantic drift. Recursive adaptation proposed 24 experts, retired eight low-utility duplicates, restored drift accuracy to 100%, retained 96.704% on the original task, reached 505 of 512 planning targets, preserved exact routed-versus-complete agreement, and reproduced checkpoint identity and evaluation behavior.

`ARCHITECTURE_GAPS.md` in the case-study directory explains the actual blockers to a unified architecture and why modality adapters, use policy, evaluator authority, protected evidence, external effects, deployment, and promotion remain outside the recursive execution plane.

These are repository-visible development observations, not claims of real-data, language, multimodal, foundation-model, or production superiority. The tasks are deliberately favorable, holdouts are not independently protected, formal MNCS and MNCDS status remain `UNKNOWN`, and promotion is unauthorized.

The complete source, contracts, preregistration, evidence, threat models, and assurance records are maintained in the RAVEL case-study directory in the GitHub repository.
