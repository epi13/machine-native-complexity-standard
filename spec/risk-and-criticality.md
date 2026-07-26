# Risk and criticality

Evidence burden increases with opacity, structural complexity, criticality,
untrusted-input exposure, regeneration difficulty, portability requirements,
analysis uncertainty, and consequences of failure.

| Exposure / consequence | Low | Moderate | High or critical |
|---|---|---|---|
| Trusted, bounded input | L1 often sufficient | L2 recommended | L3 minimum |
| Partly untrusted input | L2 recommended | L3 minimum | L4 plus domain review |
| Adversarial input | L3 minimum | L4 minimum | L5 plus independent assurance |

The table is a floor for risk discussion, not an automatic certification rule.
Applicable regulation may require more.

A generated lookup table over fixed trusted keys is typically low risk: narrow
state, bounded memory, easy regeneration, and differential comparison. A network
parser is high risk: adversarial bytes, state transitions, length arithmetic,
sensitive emission, portability, and severe compromise consequences. The parser
therefore needs materially stronger safety, invariant, fuzz, resource, holdout, and
regeneration evidence even if both components have similar source size.
