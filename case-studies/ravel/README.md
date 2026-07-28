# RAVEL — Recursive Adaptive Vector Execution Lattice

RAVEL is a machine-native research architecture that treats AI/ML as one combined problem of **routing, retrieval, compression, training state, and bounded computation**.

Its foundational claim is that a model, memory store, router, trainer, and compute scheduler should not be separate systems. A stored unit should simultaneously be:

- a compressed region of behavior;
- a retrieval target;
- an executable expert;
- a routing destination;
- a training shard with sufficient statistics;
- a lineage node that can produce replacement experts; and
- a measured unit of computational cost.

The intended long-term system records successful and failed execution traces, compiles stable trace regions into executable experts, routes future work through those experts, spends additional computation on uncertain inputs, and retires experts that become dominated. Human readability remains in contracts, authorities, evidence, regeneration, and lifecycle controls.

## RAVEL 0.1: exact conditional inference

The first mechanism proof contains 256 generated quantized experts. A query is routed into one of 256 lattice cells. The cell retrieves 24 candidate experts and carries a mathematical lower bound for every excluded expert.

The candidate returns early only when the best routed expert is **strictly closer than any excluded expert could possibly be**. Otherwise it scans the excluded experts and becomes the complete oracle. Ties and uncertainty therefore fall back rather than being promoted to success.

```text
query
  -> generated lattice cell
  -> retrieve 24 compressed experts
  -> execute candidates
  -> exact lower-bound certificate
       PASS: return
       UNKNOWN: scan excluded experts
```

### Inference development result

| Workload | Queries | Mismatches | Certified rate | Mean experts | Evaluation reduction |
|---|---:|---:|---:|---:|---:|
| Familiar, near stored experts | 100,000 | 0 | 100.000% | 24.000 | 90.625% |
| Uniform control | 25,000 | 0 | 2.236% | 250.812 | 2.026% |

The uniform control result is intentional: unfamiliar traffic receives nearly full computation because the shortcut cannot be justified.

## RAVEL-T 0.2: recursive expert training

RAVEL-T pushes the same lattice into training. The model's current experts build the router; the router creates exact training assignments; assignment errors identify overloaded shards; those shards compile into child experts; and the children rebuild the next router.

```text
current experts + lineage
          |
          v
  exact routing lattice
          |
          v
 development assignments
          |
          v
 error-ranked shards
          |
          v
 bounded child compilation
          |
          +------> new experts + lineage
                         |
                         +---- recursively rebuild lattice
```

The epoch-1 trainer starts with eight experts and permits at most eight births per growth round until reaching 64 experts. It compares the recursive candidate with a fixed eight-expert learner and a conventional flat 64-expert learner on a frozen synthetic classification task.

### Training development result

| Implementation | Holdout accuracy | Mean holdout experts | Training expert evaluations |
|---|---:|---:|---:|
| RAVEL-T recursive 8→64 | 100.000% | 8.000 | 4,144,248 |
| Fixed eight-expert baseline | 22.461% | 8.000 | 3,538,944 |
| Flat 64-expert baseline | 100.000% | 64.000 | 87,031,808 |

Additional observations:

- 56 deterministic expert births produced the 64-expert topology;
- all 8,192 holdout routes agreed exactly with the full-scan oracle;
- every holdout request was certified after evaluating eight experts;
- the recursive trainer used **95.238% fewer expert evaluations** than the flat 64-expert training baseline; and
- repeated local runs produced the same evidence and lineage digest.

This is a deliberately favorable separated-cluster mechanism study. It does not establish superiority on real data or neural training.

## Run

```bash
make test
make training-test
make training-check
```

To rewrite the checked-in records:

```bash
make evidence
make training-evidence
```

Requirements: a C11 compiler, the C math library, and Make.

## Files

- `ravel.c` — epoch-1 exact conditional-inference capsule;
- `CONTRACT.md` — readable inference contract;
- `evidence.json` — captured inference development observation;
- `ravel_train.c` — epoch-1 recursive-training capsule;
- `TRAINING_CONTRACT.md` — readable training authority and gates;
- `training-preregistration.json` — frozen protocol and baselines;
- `training-evidence.json` — deterministic training and holdout observations;
- `training-threat-model.json` — threats and residual UNKNOWNs; and
- `training-assurance-case.json` — bounded non-promotion record.

## MNCS boundary

- **Human control plane:** contracts, task boundary, baselines, exact fallback, birth limits, benefit gates, and exclusions.
- **Machine execution plane:** generated experts, centroids, labels, routing lattice, assignments, topology, and lineage.
- **Evidence plane:** paired baselines, holdout accuracy, exact mismatch counts, evaluation work, checksums, and limitations.
- **Development-control plane:** fixed seeds, preregistration, deterministic births, frozen maximum topology, and immutable promotion fields.
- **Operational-control plane:** full-scan inference rollback and fixed-topology training rollback.

The repository-visible experiments record development `PASS`. Formal MNCS and MNCDS status remain `UNKNOWN` pending protected workloads, independent evaluation, cross-host reproduction, legitimate learned baselines, adversarial training studies, and lifecycle evidence.

## Claim boundary

RAVEL does not establish a solution to intelligence, generalization, foundation-model training, or production inference. Version 0.1 demonstrates exact conditional compute over a generated compressed expert lattice. RAVEL-T 0.2 demonstrates that the same bounded structure can recursively create its routing, training shards, child experts, and future computational path on a synthetic task.

## Origin

The name, architecture, algorithms, repository setup, and initial implementations were created by **GPT-5.6 Thinking** in response to Alexander Collamore's challenge to design an AI/ML foundation that fully embraces Machine-Native Complexity. Alexander Collamore is the repository steward.
