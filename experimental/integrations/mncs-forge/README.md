# MNCS Forge compatibility record

This directory records the first non-normative integration with the separate
[`epi13/mncs-forge-mcp`](https://github.com/epi13/mncs-forge-mcp) repository. It does not
vendor Forge, modify a schema, establish conformance, or make MNCS CI depend on Forge.

The project development configuration is kept at repository root because Forge requires
project paths to be relative without `..` traversal. It retains the EdgeStream read-only
compatibility workflows and adds bounded project workflows. The compatibility record pins
the exact implementation commits used for local validation. Historical EdgeStream and
Joern evidence is unchanged.
