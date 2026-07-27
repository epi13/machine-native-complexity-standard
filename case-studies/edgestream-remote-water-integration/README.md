# EdgeStream → Remote Water integration study

This development-only study compiles the existing EdgeStream generated C candidate, feeds it
binary telemetry frames under the EdgeStream contract, adapts accepted canonical event records
to the Remote Water telemetry interface, and compares the resulting authorized intents against
direct Remote Water inputs.

The component evidence boundaries remain separate. EdgeStream retains its own manifest and
captured `MNCS-L4` development result. Remote Water retains formal `MNCS-L5` and `MNCDS-D3`
status as `UNKNOWN`. This integration has its own identity and cannot promote either component
claim.

Run from the repository root with:

```bash
make edgestream-water-integration
```

The adapter is intentionally bounded to one device and four metrics: tank level, demand,
power availability, and telemetry quality. It provides no network transport, authentication,
SCADA connection, or actuator output.
