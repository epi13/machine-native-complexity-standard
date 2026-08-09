# Experimental execution-receipt corpus

These fixtures exercise `mncs-execution-receipt` 0.1-experimental. They are
runner observations, not assurance or conformance certificates. The generic
reference receipt is a completed local run whose harness result is `PASS`,
while filesystem, network, and process restriction remain `unknown`.

The deterministic test corpus covers completed, nonzero-exit, timeout, signal,
crash, resource-limit, output-limit, rejected, truncated stdout/stderr,
aggregate output limits, missing optional accelerator metrics, identity
substitution, challenge replay/window errors, malformed measurements, stale
placement references, enforcement overclaims, and incomplete observations.
