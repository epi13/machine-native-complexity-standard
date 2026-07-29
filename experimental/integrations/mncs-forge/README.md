# MNCS Forge compatibility record

This directory records the first non-normative integration with the separate
[`epi13/mncs-forge-mcp`](https://github.com/epi13/mncs-forge-mcp) repository. It does not
vendor Forge, modify a schema, establish conformance, or make MNCS CI depend on Forge.

The EdgeStream configuration is kept at repository root because Forge requires project
paths to be relative without `..` traversal. The compatibility record pins the exact
commits used for local inspection. Historical EdgeStream and Joern evidence is unchanged.
