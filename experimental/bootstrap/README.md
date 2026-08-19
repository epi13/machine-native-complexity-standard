# Experimental MNCS bootstrap artifacts

This directory contains non-normative examples for RFC 0009, the machine-native bootstrap and deployment proposal.

The examples demonstrate three important boundaries:

1. the caller declares desired state instead of issuing installation choreography;
2. the main MNCS catalog describes deployable family components through structured metadata; and
3. the bootstrap engine returns structured plan/apply/verification state suitable for both humans and agents.

These files are examples only. They are not frozen schemas, do not change MNCS conformance, and are not authorization to execute the represented operations.

## Example flow

```text
desired-state.fabric-worker.json
        +
component-catalog.example.json
        +
local discovery
        |
        v
bootstrap plan
        |
        v
plan-result.example.json
        |
        v
operator/policy authorization
        |
        v
apply -> verify -> capability delta + receipt
```

The `darwin` platform identifier is intentionally shown as reserved/unverified. It must not become a support claim until an implementation is tested on suitable Apple hardware.
