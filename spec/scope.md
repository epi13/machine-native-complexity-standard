# Scope

MNCS governs the evidence and lifecycle needed to accept a machine-generated or
machine-optimized software component whose internal complexity is not expected to be
maintained directly by humans.

MNCS does not certify a generator, guarantee absence of defects, replace domain
regulation, define a universal complexity score, or authorize opacity without a
measured benefit. It applies at a declared component boundary and environment.
Claims outside that boundary are invalid.

MNCS differs from:

- **arbitrary unreadability and accidental complexity**, which have no intentional,
  evidenced benefit;
- **obfuscation**, whose purpose is to conceal rather than provide auditable behavior;
- **compiler output**, normally justified by a readable source program and compiler
  trust model rather than an MNCS evidence bundle;
- **ordinary generated code**, which may remain routinely human-maintainable and need
  no exception envelope;
- **formal synthesis**, which can be an MNCS generator but does not by itself supply
  operational, performance, provenance, or regeneration evidence;
- **human-maintained optimized code**, whose lifecycle still expects direct source
  edits and review.
