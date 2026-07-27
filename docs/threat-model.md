# Threat model

MNCS addresses accidental or adversarial substitution of sources and evidence, silent
post-certification edits, incomplete claims, hidden UNKNOWN results, invalid performance
victories, unsafe evidence execution, path traversal, provider overclaiming, and
irreproducible generation.

MNCDS adds controls for generator authority escape, contract and baseline manipulation,
evaluator and threshold mutation, benchmark contamination, holdout leakage, selective
candidate reporting, false independence, unreproducible selection, and unsafe release or
retirement.

## Generic machine-native threat record

A machine-native threat model should record:

- stable threat identity and category;
- affected control plane and assets;
- actor, operator error, environmental cause, or tool failure;
- preconditions and attack or failure path;
- assumptions and trust boundaries;
- mitigations and their evidence identities;
- detection and monitoring signals;
- residual risk and tolerated UNKNOWN;
- responsible owner; and
- revalidation or retirement triggers.

Identifying a threat does not prove it is mitigated. A mitigation identity proves only
which mitigation was evaluated, not that the mitigation is correct or complete.

## Baseline taxonomy

Projects should consider at least:

- generator authority escape or undeclared external access;
- unauthorized contract, baseline, evaluator, policy, or threshold change;
- benchmark contamination and protected-holdout leakage;
- selective candidate retention or omitted failures;
- evaluator gaming and UNKNOWN promotion;
- candidate, prompt, model, dataset, evidence, or release substitution;
- compromised dependencies, build systems, compilers, kernels, hardware, or signing keys;
- false or collusive evaluator independence;
- adversarial runtime input, denial of service, and resource exhaustion;
- interface, dependency, environment, or operational drift;
- unavailable or misleading monitoring;
- failed rollback, regeneration, replacement, or retirement; and
- composition failures hidden by aggregate system reporting.

## Boundaries

MNCS and MNCDS do not eliminate compromised compilers, kernels, hardware, generator
services, maintainers, or reviewers. Those belong in the declared trust and environment
model. Higher criticality needs independent methods and domain assurance beyond the
minimum level.

Bundle readers should treat every file as untrusted. The reference validator parses JSON
and hashes bytes; it does not execute evidence. Provider execution is explicit and
separate, and a provider result remains evidence from an identified method rather than a
truth oracle.
