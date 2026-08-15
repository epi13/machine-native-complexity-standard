# CI authority surfaces

CI visibility and release authority are separate. A successful workflow is
operator-controlled automation evidence; it is not an MNCS or MNCDS result,
independent evaluation, protected custody, governance approval, certification, or
promotion.

## Release-critical workflow

`Core Standard` is the release-critical workflow. It covers:

- formatting, lint, strict typing, and unit tests across supported Python versions;
- packaged schema loading, core and MNCDS corpora, examples, and offline issue-map
  integrity;
- package build and installed-wheel smoke testing;
- the MNCS 0.3/MNCDS 0.1 release-candidate corpus;
- the embedded Rust consumer, Python/Rust comparison, and pinned external Rust
  interoperability checkout;
- documentation build; and
- `git diff --check`.

The canonical local entry point is `make check`. It covers only standards and
conformance validation; empirical study checks are owned by the
[mncs-reference-studies repository](https://github.com/epi13/mncs-reference-studies).

Core pytest invocations cover the standards test surface. Empirical regression tests
and study-specific preregistration checks run from the reference-studies repository.

The dedicated `Documentation` workflow additionally controls Pages deployment, and
the tag-only `Release` workflow packages artifacts. Neither workflow supplies the
OPEN governance or signing authority.

## Empirical-study workflows

Empirical workflows, path filters, artifacts, and study-specific environments are
maintained in the [mncs-reference-studies repository](https://github.com/epi13/mncs-reference-studies).
The standards repository does not require a sibling checkout for ordinary `make check`.

Experimental failures stay visible. They are not relabeled with universal
`continue-on-error`; repository branch-protection policy chooses required checks.
The laboratory workflow has no restrictive path filter, so changes to core code or
shared schemas still trigger compatibility checks.

Historical study results remain frozen and their negative fixtures and mutation tests
remain authoritative in the reference-studies repository. Migration does not change
their result labels or promotion boundaries.

## Frozen sources and formatting

The three RAVEL 0.5 Python evidence tools are excluded from Ruff formatting because
their exact source identities are frozen in the RAVEL 0.5 manifest. They remain
covered by their source-identity verifier, negative mutation suites, and specialized
workflow. Reformatting those bytes merely to satisfy style would invalidate
historical evidence; the exclusion does not change any expected result or gate.
