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

The canonical local entry point is `make core-check`. `make check` remains a
compatibility alias for the same core authority surface. Expensive cross-language
checks run once rather than once per Python version.

Core pytest invocations exclude tests marked `experimental`. Forge integration and
case-study preregistration tests retain that marker and run in their experimental
workflows. An unfiltered local `pytest` still runs both groups for complete developer
verification.

The dedicated `Documentation` workflow additionally controls Pages deployment, and
the tag-only `Release` workflow packages artifacts. Neither workflow supplies the
OPEN governance or signing authority.

## Experimental workflows

`Experimental Laboratories` contains multilingual profiles, the Go gateway,
composed-system waves, cross-host reconciliation, historical pre-0.4 RAVEL
reproduction, RAVEL 0.6 preregistration identity checks, and dSense. Specialized
RAVEL 0.4, RAVEL 0.5, CacheForge, EdgeStream, remote-water, and Wave Five workflows
remain separate because their identities, artifact exchange, and
historical/evaluation boundaries are clearer that way.

Experimental failures stay visible. They are not relabeled with universal
`continue-on-error`; repository branch-protection policy chooses required checks.
The laboratory workflow has no restrictive path filter, so changes to core code or
shared schemas still trigger compatibility checks.

RAVEL 0.5 reproduction success does not change its frozen development result
`FAIL`, formal MNCS and MNCDS statuses `UNKNOWN`, or unauthorized promotion state.
Expected negative fixtures and mutation tests must continue to reject their inputs.

## Frozen sources and formatting

The three RAVEL 0.5 Python evidence tools are excluded from Ruff formatting because
their exact source identities are frozen in the RAVEL 0.5 manifest. They remain
covered by their source-identity verifier, negative mutation suites, and specialized
workflow. Reformatting those bytes merely to satisfy style would invalidate
historical evidence; the exclusion does not change any expected result or gate.
