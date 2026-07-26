# MNCDS 0.1 Development Record and Initial Decisions (Draft)

This module is part of the proposed MNCDS 0.1 normative text under RFC 0004. Normative
terms use the meanings in `normative-language.md`.

It defines the first interoperable development-record profile and resolves questions
needed to test the draft. It does not change MNCS 0.2 conformance semantics.

## 1. Companion relationship

MNCDS MUST remain separately versioned from MNCS throughout the MNCS 0.x series. A
future merger into MNCS MAY be proposed only through a major-version RFC that defines
migration and preserves the validity of historical MNCS claims made without MNCDS
records.

An MNCS result and an MNCDS result MUST remain distinguishable in storage, APIs, CLI
output, attestations, and human-readable claims.

## 2. Aggregate development record

The minimum interoperable unit for MNCDS 0.1 is one aggregate development record. A D1
record MUST contain:

- MNCDS and schema versions, record identity, epoch identity, creation time, and claimed profile;
- problem statement, intended use, contract, baseline, environment, threat-model, objective, and selection-policy identities;
- the six logical role bindings defined by MNCDS;
- generator identity, effective configuration, executable and authority identities, permissions, and resource limits;
- development and selection partition identities;
- evaluator identities and configurations;
- every materially evaluated candidate's identity, parent lineage, generator identity, build status, objective value, evaluator results, and disposition;
- selected-candidate identity, selection rationale, useful-benefit result, and UNKNOWN policy;
- a declared reproducibility class;
- an MNCS binding when the charter plans an MNCS claim;
- release controls when D4 is claimed.

A project MAY split this information among content-addressed records, but it MUST expose
an offline-resolvable aggregate view with equivalent semantics.

Correcting a record MUST create a new record identity and reference the superseded
record. Historical records MUST NOT be silently rewritten.

## 3. Material evaluation and rejected candidates

A candidate is **materially evaluated** when it reaches any gate whose result can affect
ranking, promotion, rejection, selection, a reported success rate, or a conformance
claim.

Every materially evaluated candidate MUST be retained individually by identity,
lineage, gate outcomes, objective value where applicable, and disposition.

Candidates rejected before material evaluation MAY be aggregated only when the charter
predeclares the aggregation boundary. An aggregate MUST preserve:

- count;
- rejection stage or reason class;
- generator and effective-configuration identities;
- time or sequence range;
- a stable digest, Merkle root, content-addressed index, or reproducible query over the omitted set.

Search scale MUST NOT justify selective omission of materially evaluated candidates or
failures that reveal selection pressure or evaluator exploitation.

## 4. Stochastic reproducibility classes

A record MUST declare exactly one class:

- **EXACT:** the declared process reproduces byte-identical candidates and records under the bound environment;
- **SEEDED:** the same algorithm, effective configuration, environment, and preserved seeds reproduce the run;
- **STATISTICAL:** repeated runs reproduce predeclared summary statistics within declared uncertainty bounds;
- **DISTRIBUTIONAL:** repeated runs reproduce a declared candidate family or outcome distribution under a declared comparison method;
- **NONE:** no credible exact, seeded, statistical, or distributional claim is made.

D1 MAY declare `NONE`. D2 and above MUST NOT declare `NONE`.

`EXACT` and `SEEDED` MUST preserve all randomness inputs needed by the claim. Statistical
and distributional claims MUST declare repetition count, measurement protocol, summary
or distance statistic, bounds, and failure treatment. A stronger class MUST NOT be
inferred from a weaker one.

## 5. Evaluator independence at D3

A D3 final evaluator MUST:

- use an authority identity different from the generator authority;
- use an executable identity different from the generator executable;
- use an immutable configuration identity;
- be bound to the independent-reviewer role;
- use protected holdout or fresh challenge evidence unavailable to ordinary generation and ranking;
- record PASS, FAIL, or UNKNOWN against the selected candidate;
- preserve the evidence identity used for that result.

Sharing generator authority or generator executable identity MUST fail D3. Missing or
unverifiable independence evidence MUST produce FAIL or UNKNOWN according to policy; it
MUST NOT silently pass.

Organizational separation, separate infrastructure, multiple independent evaluators,
and threshold attestations MAY support future higher-assurance profiles. They are not
required by baseline D3.

Different identities demonstrate a declared control boundary; they do not prove honesty,
competence, or absence of collusion.

## 6. Selection and UNKNOWN

The selected candidate MUST exist in the candidate ledger and MUST have disposition
`selected`. The selection-policy identity MUST match the charter.

A selected candidate with a required FAIL MUST fail the process claim.

When a selected candidate has required UNKNOWN evidence:

- policy `reject` MUST fail the process claim;
- policy `human_review` MUST include reviewer identity, explicit decision, and rationale;
- an explicit acceptance with unresolved UNKNOWN MUST preserve overall status UNKNOWN;
- human review MUST NOT convert UNKNOWN to PASS.

D3 and above MUST record the selection rule before protected-holdout evaluation. A
post-hoc rule change begins a new selection epoch.

## 7. MNCS binding

When the charter plans an MNCS claim, the development record MUST bind a resulting MNCS
manifest or package identity.

The MNCS binding's selected-candidate, contract, and environment identities MUST match
the final MNCDS record. Any mismatch MUST fail the combined claim.

A validator MUST report MNCS and MNCDS results separately even when the records bind to
one another.

## 8. D4 operational evidence

D4 MUST include:

- release artifact identity;
- rollback artifact identity and a passing rollback test;
- monitoring signals or thresholds;
- a regeneration or replacement drill with time, status, and evidence identity;
- retirement triggers.

A rollback test with FAIL or UNKNOWN MUST NOT satisfy D4. A regeneration drill with FAIL
or UNKNOWN MUST NOT satisfy D4.

## 9. Privacy-preserving extensions

Privacy-preserving proofs, confidential-computing attestations, commitments, and
transparency logs MAY be used as namespaced experimental extensions.

They MUST NOT replace required evidence unless a future RFC defines their statement,
predicate, trust, expiration, revocation, failure, and interoperability semantics and at
least two implementations agree on a versioned corpus.

Redaction without an accepted proof MUST remain UNKNOWN whenever the hidden material is
required to establish the claimed profile.

## 10. CLI and reporting

The baseline command families are separate:

```text
mncs validate ...
mncds validate ...
```

A future combined summary MAY display both results. It MUST preserve separate statuses,
versions, record identities, issue sets, scopes, and trust decisions. It MUST NOT collapse
the results into one boolean or imply that one result proves the other.

## 11. Experimental schema

The initial machine-readable aggregate record is
`schemas/mncds-development-record.schema.json`.

Ordinary validation MUST be offline and MUST NOT execute or import generators,
candidates, evaluators, analyzers, benchmarks, or evidence binaries.

The schema and validator are experimental implementations of this draft module. Their
presence in the repository does not bypass RFC review or establish accepted core status.
