# Normative language

The terms in this document have these MNCS 0.1 meanings when capitalized:

- **MUST**, **REQUIRED**, and **SHALL** express an unconditional requirement.
- **MUST NOT** and **SHALL NOT** express an unconditional prohibition.
- **SHOULD** and **RECOMMENDED** express a strong recommendation. A deviation needs a
  recorded reason and risk assessment.
- **SHOULD NOT** expresses a strongly discouraged action. A deviation needs the same
  record.
- **MAY** and **OPTIONAL** identify a permitted choice.
- **PASS** means the declared method produced sufficient evidence for the requirement
  within its stated assumptions and bounds.
- **FAIL** means evidence demonstrates a violation or a required gate did not pass.
- **UNKNOWN** means the available method could not establish either PASS or FAIL,
  including tool error, unsupported syntax, exceeded bounds, ambiguity, or missing
  evidence.

UNKNOWN MUST NOT be converted to PASS by omission, truthiness, aggregation, provider
reputation, or absence of a counterexample. An acceptance policy MAY reject UNKNOWN
or route it to explicit human review; it MUST NOT silently accept it.

Normative text uses these words only in uppercase. Lowercase words are descriptive.
