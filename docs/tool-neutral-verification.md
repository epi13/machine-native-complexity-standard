# Tool-neutral structural verification

An invariant result communicates requirement, source identity, status, method,
provider version, assumptions, bounds, witness, locations, resource cost, and
limitations. The evidence consumer should not need provider-specific folklore to
understand the claim.

Suitable methods include compiler or LLVM CFG passes, abstract interpretation, model
checking, symbolic execution, proof assistants, custom static analyzers, runtime
instrumentation, language-specific verification, and independent combinations.
Joern is an optional provider, not a dependency.

Use Forge to discover declared providers and capability blockers. Forge orchestrates
bounded commands and records their identities and limitations; it does not perform graph
analysis itself. Source reading is review, not independent structural verification, and
grep or line counting cannot establish missing control-flow or data-flow facts.

When comparative structural evidence is claimed for a graph-sensitive change, use the
same provider, method, scope, and relevant bounds before and after the change. If no
provider supports the required semantics, record the limitation as UNKNOWN rather than
selecting an inadequate proxy.

Prefer exception-driven repair: evaluate first; say nothing if invariants pass; give
one compact witness on FAIL; apply policy to UNKNOWN; permit a bounded repair; and
rerun the entire suite against the new immutable hash.
