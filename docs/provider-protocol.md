# Provider Protocol and Python SDK

Provider Protocol 0.1 uses one JSON Lines request and response. Capabilities, health,
cancellation, analysis, errors, PASS/FAIL/UNKNOWN, and compact witnesses are explicit.
Normal validation never runs a provider.

```bash
mncs provider inspect python examples/providers/pattern_provider.py --json
mncs provider run descriptor.json request.json --json
mncs provider verify-result result.json
```

The `mncs_provider_sdk` package supplies typed models, strict framing, witness helpers,
an entrypoint, and a timeout-safe client. Included pattern, mock structural,
runtime-adapter, bounded-UNKNOWN, and compact-FAIL providers are examples, not production
analysis. The runner uses no shell and cleans up descendants on timeout, but does not
claim network isolation.
