# Machine-Native Complexity Development Specification 0.1-rc.1

Status: release-candidate proposal under Draft RFC 0004. It is not Accepted or Final.
Normative terms use RFC 2119/8174 meanings from `normative-language.md`.

## 1. Scope and relationship to MNCS

MNCDS governs development used to create, evaluate, select, release, monitor,
regenerate, replace, and retire a machine-native implementation. MNCS governs
implementation evidence. Results MUST remain separately versioned and MUST NOT collapse.

MNCDS is tool-neutral. Models, generators, analyzers, compilers, providers, benchmarks,
languages, and case studies are non-normative.

Results are `PASS`, `FAIL`, and `UNKNOWN`, with `FAIL > UNKNOWN > PASS`. Missing or
inaccessible evidence, unsupported analysis, crashes, and timeouts MUST NOT be `PASS`.

## 2. Portable aggregate record

The normative interoperability unit is one `mncds-development-record-0.1` aggregate,
resolvable offline. Optional content-addressed subrecords MUST expose an equivalent
aggregate containing record/epoch/contract/baseline/environment/threat/objective/tool/
partition/selection/candidate/release/lifecycle identities, authorities and overlaps,
all materially evaluated candidates, auditable aggregates, evaluation and selection
results, reproducibility, MNCS binding, and applicable D4 controls.

Corrections MUST create a new record and reference the superseded record. Historical
records MUST NOT be rewritten.

## 3. Charter and contract binding

Before material evaluation, the process MUST freeze a charter with problem, intended
use, exclusions, readable contract, environment/resource limits, threat model,
baseline, operationally meaningful benefit objective, hard gates, partitions,
selection policy, planned profiles/levels, and lifecycle owners.

Complexity, novelty, model preference, source size, or a higher score alone MUST NOT be
the useful objective. A material charter, contract, policy, evaluator, threshold,
environment, or baseline change starts a new epoch and gets new identities.

## 4. Baseline and environment lock

The baseline MUST predate search and record source/artifact, build, dependency,
environment, evaluator, functional, safety, resource, performance, failure, and UNKNOWN
facts. The environment lock identifies platform, toolchain, dependencies, hardware,
configuration, and permitted variance. A stale, weakened, or materially different
baseline MUST NOT create false benefit.

## 5. Roles and authority

Records MUST bind contract, generator, evaluator, selection, release, and
independent-review authorities. Each overlap MUST disclose scope, rationale, risk, and
recusal or compensating control. D3/D4 require final-evaluator authority and executable
identities distinct from the generator and reviewer-role binding.

The generator MUST NOT modify contract, baseline, evaluators, selection policy,
thresholds, protected evidence, or release criteria. Filesystem, process, network, tool,
mutation, time, and candidate-count permissions MUST be bounded.

Local code can test implementation and executable identities. Independent operator and
organizational independence need external evidence and remain `UNKNOWN` when absent.

## 6. Partitions and protected evidence

Development, selection, and final-evaluation partitions MUST have distinct identities
and access rules. Evidence influencing generation/ranking cannot be protected for the
same claim.

Protected evidence records commitment, custodian, access boundary, disclosure, reuse,
and contamination. Developer-controlled withholding MUST NOT be called external
custody or organizational independence. Contaminated required holdout is `FAIL`;
unverifiable custody is `UNKNOWN`.

## 7. Generator, evaluators, and progressive evaluation

Generator/evaluator authority, executable, configuration, environment, and corpus
identities remain stable within an epoch. Mutation starts a new epoch. D2 requires
evaluator regression corpora.

Later gates MUST NOT erase earlier required `FAIL` or `UNKNOWN`. Repair creates a new
candidate identity. No evaluator may promote itself to selection or release authority.

## 8. Candidate ledger and lineage

Every materially evaluated candidate MUST be retained with identity, parents, epoch,
generator, sequence, build, objective, evaluator results, disposition, and retention.
Identities are unique; parents exist; lineage is acyclic. The selected candidate exists,
is retained, and has disposition `selected`.

Pre-material candidates MAY use a predeclared aggregate recording count, reason/stage,
generator/configuration, time/sequence range, and digest/query. Material failures MUST
NOT be hidden in an aggregate.

## 9. Reproducibility

Exactly one class is declared: `EXACT`, `SEEDED`, `STATISTICAL`, `DISTRIBUTIONAL`, or
`NONE`. D1 MAY use `NONE`; D2-D4 MUST NOT. Exact/seeded claims retain randomness.
Statistical/distributional claims define repetitions, protocol, statistic, bounds, and
failure treatment. Failed regeneration is `FAIL`; unavailable regeneration `UNKNOWN`.

## 10. Selection

Before final evidence opens, selection declares hard gates, metrics/directions/weights,
ties, UNKNOWN policy, benefit threshold, maximum regression, and human judgment.
Post-hoc changes start a new selection epoch.

Required `FAIL` fails selection. Under `reject`, required `UNKNOWN` fails. Under
`human_review`, acceptance preserves overall `UNKNOWN`; review cannot promote it.
The selected candidate meets useful benefit and all hard gates.

## 11. Independent final evaluation and MNCS binding

D3/D4 final evaluation requires authority/executable separation, immutable
configuration, reviewer binding, fresh/protected evidence, complete identities, and an
explicit result. Identity separation proves only a declared technical boundary.

When MNCS is planned, candidate, contract, and environment bindings MUST agree.
Mismatch is `FAIL`. MNCS and MNCDS reports remain separate.

## 12. Release and lifecycle

D4 binds release artifact/environment, build/package, limitations, monitoring,
rollback, regeneration/replacement, release authority, and retirement triggers.
Rollback MUST be tested. `FAIL` fails D4; absent, stale, or `UNKNOWN` remains `UNKNOWN`.
Regeneration/replacement MUST be exercised and measured.

Monitoring distinguishes failure, drift, unavailable evidence, and normal operation.
No incident is not proof. Replacement creates new artifact/candidate/claim/epoch
identities. Retirement records reason, time, affected claims, artifact, and replacement.

## 13. Recursive improvement

Epoch `n` evidence MAY improve epoch `n+1` tools. The later epoch MUST freeze prior
tool/corpus identities, retain failures/disagreements, identify feedback, predeclare an
operational objective, create new tool/config identities, use fresh inputs and separate
partitions, retain regressions, avoid silent contract/threshold change, and compare
correctness, UNKNOWN, crash, timeout, resources, determinism, and diagnostics.

Protected final evidence MUST NOT enter same-claim repair feedback. Unresolved
disagreement remains `UNKNOWN`. Higher score alone is not a useful objective.

## 14. Cumulative profiles

- D1: charter, contract, baseline, roles/overlaps, bounded generator, identities,
  ledger/lineage, selection rationale, explicit results.
- D2 adds environment lock, partitions, reproducibility above `NONE`, repetitions,
  evaluator regression, aggregates, and epochs.
- D3 adds predeclared selection, protected/fresh evidence, evaluator separation,
  reviewer binding, conflicts, and MNCS binding when claimed.
- D4 adds release, monitoring, tested rollback, exercised regeneration/replacement,
  retirement, and lifecycle identities.

## 15. Privacy, contamination, reporting, and migration

Restricted material still gets stable identities/access boundaries. Redaction is not
verification. Required hidden evidence is `UNKNOWN` absent an accepted proof.
Protected-evidence reuse identifies prior epochs/claims; development exposure
contaminates later protected use.

Reports include version, record/epoch, profile, selected candidate, computed status,
normalized issues, warnings, scope, limitations, unsupported rules, and executable
identity. Validation is offline and executes nothing.

Independent consumers read the golden corpus directly and distinguish agreement,
disagreement, unsupported, invalid, and implementation errors. Local diversity does not
prove independent operation, custody, organization, governance, or accreditation.

Draft records remain valid as drafts. Migration is optional, creates a new identity,
and starts at the oldest reliable baseline. Missing history remains `UNKNOWN`. Changing
a version string is not migration. Exact versions dispatch; unknown versions are
`UNSUPPORTED`.
