# Experimental language evidence profiles

Language evidence profiles are a replaceable, versioned description of evidence collection. They
are not a new MNCS level, not an MNCDS profile, and not a certification of a programming language.

## Why C11 remains the anchor

C11 remains the controlled reference language because the repository already has bounded C11
experiments, strict GCC and Clang builds, ASan and UBSan runs, malformed-input and mutation
fixtures, deterministic workloads, and Clang AST structural evidence. The C11 profile is compact
and intentionally non-exhaustive.

## Why Rust is the first expansion

Rust provides a useful contrast: safe and unsafe boundaries are explicit, Cargo and Cargo.lock make
build identity concrete, Clippy and rustfmt are reproducible evidence producers, and panic,
overflow, macro expansion, conditional compilation, and FFI limits can be stated directly. Wave
One pins Rust 1.97.1 and edition 2024. A narrow source provider supplements, but does not replace,
compiler and test evidence.

## Python and AI/ML evidence

Python evidence differs from C11 evidence because behavior can be changed by imports, reflection,
monkey-patching, serialization, native extensions, thread pools, accelerators, and stochastic
libraries. A Python source PASS covers only the declared source invariant. Behavior implemented in
NumPy, PyTorch, custom kernels, C extensions, or Rust extensions requires separate identities and,
where material, another language profile. CacheForge receives a new language-profile amendment;
its historical epochs and formal UNKNOWN claim boundary remain unchanged.

## Result meanings

- **PASS**: the provider decided the declared narrow invariant with complete semantics for its
  stated bounded method.
- **FAIL**: the provider found a declared violation and emits a witness or counterexample.
- **UNKNOWN**: required semantics are unsupported, incomplete, unavailable, or mismatched.
- **Operational error**: the provider crashed, timed out, was invoked incorrectly, or a required
  tool was missing. It is not converted to FAIL or UNKNOWN by the provider.

`FAIL` dominates `UNKNOWN`, which dominates `PASS` only when a higher-level policy aggregates
results. A skipped or unsupported analysis is never PASS.

## Cross-language comparison

The shared stream contract gives C11 and Rust the same valid corpus, malformed corpus, functional
acceptance criteria, recovery rule, input limit, benchmark workload, and result categories.
Correctness and malformed-input behavior are directly comparable. Throughput is normalized but
imperfect because compilers, runtimes, startup, and optimization differ. Safe-Rust guarantees,
C sanitizers, macro analysis, and structural tooling are language-specific. Source size and one
universal numerical “complexity score” are explicitly non-comparable.

## Adding another language

1. Copy the smallest suitable profile and give it a new identity and version.
2. Record compiler/interpreter, build, dependency lock, generated artifact, and environment identity.
3. Declare supported, conditional, unsupported, and explicit UNKNOWN conditions.
4. Add a bounded Provider Protocol 0.1 implementation only where it adds auditable evidence.
5. Add PASS, FAIL, UNKNOWN, operational-error, deterministic-output, and binding fixtures.
6. Bind a new case-study epoch or amendment; never rewrite frozen historical evidence.
7. Add CI without making optional heavyweight tools a hidden prerequisite for ordinary validation.

## Current limitations and Wave Two

Wave One does not exhaust macro expansion, C undefined behavior, Rust FFI, Python native extension
semantics, dynamic import graphs, stochastic accelerator kernels, or cross-host performance. Future
work should add a second Rust provider, a pinned property/fuzz campaign, a Python native-extension
boundary profile, more compilers and targets, and independently reproduced cross-host observations.
