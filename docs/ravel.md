# RAVEL research architecture

RAVEL (Recursive Adaptive Vector Execution Lattice) is an MNCS research architecture that treats routing, retrieval, compression, representation, training state, temporal memory, planning, lifecycle, and computational allocation as one bounded machine-native structure.

The repository contains five cumulative mechanism studies:

- **RAVEL 0.1** demonstrates exact conditional inference over a generated expert lattice. A lower-bound certificate permits reduced computation only when the routed result is provably identical to a full scan.
- **RAVEL-T 0.2** extends the lattice into recursive training. Current experts generate the router; the router creates exact training shards; error-heavy shards compile into child experts; child lineage regenerates the next router.
- **RAVEL-U 0.3** turns the expert into a unified executable memory unit: retrieval key, compressed representation, decoder, classifier, action-conditioned predictor, transition-memory node, planning destination, replay shard, lifecycle object, and compute unit.
- **RAVEL 0.4** hardens evidence: disjoint drift adaptation and holdout data,
  canonical complete-field checkpoints, corruption tests, eight frozen regimes,
  exact-state planning measurements, reconstruction/prediction gates, bounded
  baselines and ablations, negative tests, and ordered source provenance.
- **RAVEL 0.5** corrects the adaptive mechanism and evaluator boundary:
  stratified replay, anchored base experts, optional objective-tested topology,
  normalized residuals, supported ambiguous transitions, alias-aware planning,
  matched comparisons, and independent Python gate derivation over 32 fresh
  final-validation trials.

In the historical RAVEL-U 0.3 synthetic study, the frozen model scored 71.899%
after semantic drift. Recursive adaptation proposed 24 experts and retired
eight low-utility duplicates. The reported 100% adapted score reused the
adaptation set, so it was not an untouched drift-holdout result. The reported
planning target count measured goal-expert equivalence, not exact world-state
success. Its raw-struct checkpoint also did not cover all behavioral fields.
Those historical observations remain present but are not treated as 0.4
assurance.

RAVEL 0.4 evaluates a separately seeded untouched drift holdout and reports all
eight frozen trial failures without seed or threshold selection. Its generated
results page lists the regimes, failed gates, aggregate minimum, median,
maximum, mean, and population standard deviation. The baseline and ablation
results are mixed, so no superiority claim is made.

RAVEL 0.5 preserves the 0.4 record. Its one-shot final validation records
execution integrity `PASS` and development `FAIL`: 24 of 32 trials pass.
Separated-state, overlapping-observation, noisy-observation, and
observation-drift regimes pass all four seeds. Label gain, one
transition-retention case, one combined exact-planning case, and three
ambiguous-regime cases remain failures. The executable emits raw facts; the
external evaluator alone derives gates, trial outcomes, aggregates, and the
global result. Paired baseline and ablation outcomes remain mixed.

`ARCHITECTURE_GAPS.md` in the case-study directory explains the actual blockers to a unified architecture and why modality adapters, use policy, evaluator authority, protected evidence, external effects, deployment, and promotion remain outside the recursive execution plane.

These are repository-visible development observations, not claims of real-data,
language, multimodal, foundation-model, general-AI, or production superiority.
The tasks are synthetic, holdouts are not independently protected,
deterministic reproduction is not cross-organizational reproduction, checkpoint
reproduction is not rollback authorization, formal MNCS and MNCDS status remain
`UNKNOWN`, and promotion is unauthorized.

The complete source, contracts, preregistration, evidence, threat models, and assurance records are maintained in the RAVEL case-study directory in the GitHub repository.
