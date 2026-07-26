# RFC 0001: Establish MNCS 0.1

- Status: Accepted
- Authors: MNCS Contributors
- Created: 2026-07-25
- Review deadline: bootstrap release
- Target version: MNCS 0.1
- Conflicts disclosed: initial repository bootstrap by the repository owner

## Summary

Establish the Machine-Native Complexity Standard as an open, experimental,
tool-neutral standard with two control layers, five cumulative conformance levels,
content-addressed evidence, provider-neutral invariants, multidimensional complexity,
and an offline validator.

## Motivation

Generated implementations can exceed normal source-maintenance limits. Ordinary
review conventions do not justify accepting them, but banning them can discard real
engineering benefit. MNCS relocates readability to contracts, evidence, policies,
and regeneration while requiring complexity to purchase a declared benefit.

## Decision

Adopt the normative files under `spec/`, Draft 2020-12 schemas under `schemas/`, and
the `mncs-validator` reference validator as MNCS 0.1. Treat UNKNOWN as distinct from
PASS. Make no structural provider mandatory. Adopt Apache-2.0 and the governance
process in this repository.

## Compatibility

This is the initial version. Future changes follow semantic compatibility rules and
the RFC process. MNCS 0.1 remains experimental and non-accredited.
