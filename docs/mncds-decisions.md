# MNCDS initial design decisions

RFC 0004 identified seven questions that blocked a stable experimental implementation.
The following decisions define the 0.1-draft implementation baseline. They remain subject
to RFC review and may change before acceptance.

## Companion status

MNCDS remains a separately versioned companion specification throughout the MNCS 0.x
series. Combining it with MNCS may be reconsidered only for a future MNCS major version,
after adoption experience shows that the two conformance families cannot remain cleanly
separable.

This avoids making historical MNCS bundles retroactively nonconforming because their
development history was not recorded.

## Minimum D1 record

D1 requires one aggregate development record containing:

- charter, objective, constraints, contract, baseline, environment, and threat-model identities;
- all six logical roles and disclosed executable identities where applicable;
- generator identity, configuration, permissions, and resource limits;
- development and selection partition identities;
- evaluator identities;
- every materially evaluated candidate's identity, lineage, outcome, objective value, and disposition;
- the selected candidate and selection rationale;
- explicit PASS, FAIL, and UNKNOWN treatment;
- a declared reproducibility class, which may be `NONE` at D1.

Separate ledgers and role records may be introduced later, but the aggregate record is the
minimum interoperable unit for 0.1.

## Stochastic reproducibility

MNCDS uses five declared classes:

- `EXACT`: byte-identical regeneration under the declared environment;
- `SEEDED`: the same algorithm, effective configuration, and seeds reproduce the run;
- `STATISTICAL`: repeated runs reproduce predeclared summary statistics within bounds;
- `DISTRIBUTIONAL`: runs reproduce a declared candidate family or outcome distribution;
- `NONE`: no credible regeneration or distributional claim.

D1 may truthfully declare `NONE`. D2 and above require one of the first four classes.
`EXACT` and `SEEDED` require preserved seeds where randomness exists. A stronger label
must not be inferred from a weaker one.

## Minimum evaluator independence

For D3, the final evaluator must have:

- an authority identity different from the generator authority;
- an executable identity different from the generator executable;
- immutable configuration identity;
- protected holdout or fresh challenge access unavailable to ordinary generation and ranking;
- an explicit independent-reviewer role binding;
- a result recorded against the selected candidate.

Organizational separation, separate infrastructure, multiple reviewers, and threshold
signatures can support higher assurance, but they are not mandatory for baseline D3.
Identity difference alone does not prove honesty; it proves only that the required role
and executable boundaries were declared and checked.

## Retaining rejected candidates

Every materially evaluated candidate is retained individually by identity, lineage,
measurements, gate outcomes, and disposition.

Candidates rejected before material evaluation may be summarized when the charter
predeclares the summarization boundary. A summary should preserve at least counts,
rejection stage, generator/configuration identity, time or sequence range, and a stable
digest or reproducible query over the omitted set. Search scale does not permit selective
omission of materially evaluated failures.

This rule scales to millions of candidates while preserving evidence about selection
pressure and evaluator exploitation.

## Privacy proofs and transparency logs

Privacy-preserving proofs, confidential-computing attestations, and transparency logs are
permitted as namespaced experimental extensions. They are not required by D1-D4 and do
not replace required evidence unless a future RFC defines their predicate, trust, and
failure semantics and at least two implementations interoperate.

Redaction without an accepted proof remains UNKNOWN when the hidden material is required
for the claimed profile.

## CLI result separation

MNCS and MNCDS results remain separate commands and separate result objects:

```text
mncs validate ...
mncds validate ...
```

A future summary command may display both, but it must preserve two independent statuses,
issue sets, versions, identities, and scopes. It must not collapse them into a single
boolean or imply that one result establishes the other.

## Remaining research questions

The following questions still require evidence rather than an editorial decision:

- What independent implementation should become the second MNCDS corpus consumer?
- Which additional issue codes are stable enough for cross-implementation normalization?
- What aggregation structure best preserves million-candidate search history without
  exposing proprietary candidate bodies?
- Which privacy-preserving proof systems are practical for restricted prompts, datasets,
  and model configurations?
- What evidence threshold should define a higher-assurance evaluator-independence profile?
