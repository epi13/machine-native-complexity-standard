# Provider interface

Structural providers MAY use compiler CFG analysis, LLVM passes, abstract
interpretation, model checking, symbolic execution, proof assistants, custom static
analysis, runtime instrumentation, language-specific verification, or multiple
independent methods.

Providers emit the invariant-result schema and disclose method, assumptions, bounds,
witnesses, locations, runtime, output size, and limitations. Their registration
document lists supported methods, all three statuses, version, and offline capability.
Joern is OPTIONAL and has no privileged status.
