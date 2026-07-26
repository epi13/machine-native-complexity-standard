# Tool-neutral structural verification

An invariant result communicates requirement, source identity, status, method,
provider version, assumptions, bounds, witness, locations, resource cost, and
limitations. The evidence consumer should not need provider-specific folklore to
understand the claim.

Suitable methods include compiler or LLVM CFG passes, abstract interpretation, model
checking, symbolic execution, proof assistants, custom static analyzers, runtime
instrumentation, language-specific verification, and independent combinations.
Joern is an optional provider, not a dependency.

Prefer exception-driven repair: evaluate first; say nothing if invariants pass; give
one compact witness on FAIL; apply policy to UNKNOWN; permit a bounded repair; and
rerun the entire suite against the new immutable hash.
