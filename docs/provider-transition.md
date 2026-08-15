# Forge and provider transition

Forge is now the default Codex development and evidence-control interface for this
repository. Joern was demoted from mandatory policy because MNCS evidence requirements
describe capabilities, methods, scope, identity, and limitations rather than a privileged
tool brand. Forge orchestrates declared providers; it does not perform Joern-equivalent
graph analysis.

Historical Joern evidence remains frozen. This includes repository `.joern*` snapshots,
EdgeStream evidence and environment records, the GraphFlow study, the MNEA epoch-one
baseline, RFC history, fixtures, and compatibility statements. Do not regenerate or
rewrite those artifacts solely because the default interface changed.

No analysis provider is enabled in the standards repository. The empirical Forge
configuration and project-owned Provider Protocol adapter are maintained in
`mncs-reference-studies`. An explicit Joern Provider Protocol adapter may be added as
an optional provider. The adapter, not the Joern CLI by itself,
must emit recognized Provider Protocol 0.1 capabilities and analysis responses. Another
provider may declare the same, narrower, broader, or different capabilities, together
with supported and unsupported constructs, assumptions, bounds, and limitations.

If a required capability is unavailable, unprobed, stale, malformed, or unsupported,
Forge reports a blocker and `UNKNOWN`; command exit zero, source reading, grep, and line
counts do not establish PASS. Comparative graph-sensitive evidence requires the same
provider, method, scope, and relevant bounds before and after the change.

Rollback does not require rewriting evidence. Re-enable an explicit optional provider
profile, restore a project-owned MCP registration only after inspecting its ownership,
and revert the provider-policy commits if necessary. Joern binaries, caches, repositories,
and historical outputs remain untouched throughout the transition.
